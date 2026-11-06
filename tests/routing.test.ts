import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { afterEach, describe, expect, it } from 'vitest';
import { renderDashboard } from '../src/dashboard.js';
import { PccProvider, type FmHelpRunner } from '../src/pcc-provider.js';
import { MockProvider, type ProbeResult, type Provider } from '../src/provider.js';
import { AppleOffloadRuntime, type RuntimeOptions } from '../src/runtime.js';
import { Store } from '../src/store.js';

const cleanups: string[] = [];

async function temporary(): Promise<string> {
  const root = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-routing-'));
  cleanups.push(root);
  return root;
}

afterEach(async () => {
  await Promise.all(cleanups.splice(0).map(root => rm(root, { recursive: true, force: true })));
});

const OPAQUE = 'failure happened here';
const RESPONSE = {
  diagnostics: [{
    id: 'D1', message: OPAQUE, severity: 'error', path: null, line: null, column: null, evidenceId: 'E1'
  }],
  evidence: [{ id: 'E1', startLine: 1, endLine: 1, excerpt: OPAQUE }]
};

function readyProbe(): ProbeResult {
  return {
    available: true,
    reason: null,
    osVersion: 'mock-os',
    providerVersion: 'mock-v1',
    structuredOutput: true,
    localModelVerified: true,
    argvPromptExposure: false
  };
}

function failing(message: string): Provider {
  return {
    probe: async () => readyProbe(),
    generate: async () => { throw new Error(message); }
  };
}

function untouchable(): Provider & { touched: boolean } {
  const provider = {
    touched: false,
    probe: async () => { provider.touched = true; return readyProbe(); },
    generate: async () => { provider.touched = true; throw new Error('must not be called'); }
  };
  return provider;
}

async function runOpaque(options: RuntimeOptions) {
  const root = await temporary();
  const stateDir = await temporary();
  const artifact = path.join(root, 'opaque.log');
  await writeFile(artifact, OPAQUE);
  const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir, ...options });
  await runtime.initialize();
  const result = await runtime.process({ task: 'diagnostics', path: artifact });
  return { runtime, result };
}

describe('model routes', () => {
  it('serves a run from pcc when opted in and records the route in stats and the dashboard', async () => {
    const onDevice = untouchable();
    const { runtime, result } = await runOpaque({
      routePreference: 'pcc_preferred',
      pccProvider: new MockProvider(RESPONSE),
      provider: onDevice
    });
    expect(result).toMatchObject({ status: 'ready', routeUsed: 'local', modelRoute: 'pcc', reason: null });
    expect(onDevice.touched).toBe(false);
    expect(runtime.stats({}).modelRoutes).toEqual({ on_device: 0, pcc: 1 });
    const dashboard = runtime.dashboard();
    expect(dashboard.totals).toMatchObject({ onDevice: 0, pcc: 1 });
    expect(dashboard.recent[0]?.route).toBe('pcc');
    expect(renderDashboard(dashboard)).toContain('On-device / PCC');
    runtime.close();
  });

  it('falls back to on_device when pcc is unavailable', async () => {
    const { runtime, result } = await runOpaque({
      routePreference: 'pcc_preferred',
      pccProvider: new MockProvider({}, false),
      provider: new MockProvider(RESPONSE)
    });
    expect(result).toMatchObject({ status: 'ready', modelRoute: 'on_device', reason: null });
    expect(runtime.stats({}).modelRoutes).toEqual({ on_device: 1, pcc: 0 });
    runtime.close();
  });

  it('falls back to on_device when pcc generation fails', async () => {
    const { runtime, result } = await runOpaque({
      routePreference: 'pcc_preferred',
      pccProvider: failing('pcc_quota_reached'),
      provider: new MockProvider(RESPONSE)
    });
    expect(result).toMatchObject({ status: 'ready', modelRoute: 'on_device' });
    runtime.close();
  });

  it('times out a slow pcc route on half the budget and lets on_device serve', async () => {
    const { runtime, result } = await runOpaque({
      routePreference: 'pcc_preferred',
      pccProvider: { probe: async () => readyProbe(), generate: () => new Promise(() => {}) },
      provider: new MockProvider(RESPONSE),
      deadlineMs: 3_000
    });
    expect(result).toMatchObject({ status: 'ready', modelRoute: 'on_device' });
    runtime.close();
  });

  it('returns needs_codex with every route reason when both routes fail', async () => {
    const { runtime, result } = await runOpaque({
      routePreference: 'pcc_preferred',
      pccProvider: new MockProvider({}, false),
      provider: failing('fm_generation_failed')
    });
    expect(result).toMatchObject({
      status: 'needs_codex',
      routeUsed: 'local',
      modelRoute: null,
      reason: 'pcc:mock_unavailable;on_device:fm_generation_failed'
    });
    expect(runtime.stats({}).modelRoutes).toEqual({ on_device: 0, pcc: 0 });
    expect(runtime.dashboard().recent[0]?.route).toBeNull();
    runtime.close();
  });

  it('never touches pcc unless the user opted in', async () => {
    const previous = process.env.APPLE_OFFLOAD_ROUTE;
    delete process.env.APPLE_OFFLOAD_ROUTE;
    try {
      const pcc = untouchable();
      const { runtime, result } = await runOpaque({ pccProvider: pcc, provider: new MockProvider(RESPONSE) });
      expect(runtime.routePreference).toBe('on_device');
      expect(result).toMatchObject({ status: 'ready', modelRoute: 'on_device' });
      expect((await runtime.doctor()).routes.map(route => route.route)).toEqual(['on_device']);
      expect(pcc.touched).toBe(false);
      runtime.close();
    } finally {
      if (previous === undefined) delete process.env.APPLE_OFFLOAD_ROUTE;
      else process.env.APPLE_OFFLOAD_ROUTE = previous;
    }
  });

  it('reads the pcc opt-in from APPLE_OFFLOAD_ROUTE', async () => {
    const previous = process.env.APPLE_OFFLOAD_ROUTE;
    process.env.APPLE_OFFLOAD_ROUTE = 'pcc_preferred';
    try {
      const runtime = new AppleOffloadRuntime({
        stateDir: await temporary(),
        pccProvider: new MockProvider({}, false),
        provider: new MockProvider(RESPONSE)
      });
      expect(runtime.routes.routes.map(route => route.route)).toEqual(['pcc', 'on_device']);
      expect((await runtime.doctor()).routes).toEqual([
        { route: 'pcc', available: false, reason: 'mock_unavailable' },
        { route: 'on_device', available: true, reason: null }
      ]);
      runtime.close();
    } finally {
      if (previous === undefined) delete process.env.APPLE_OFFLOAD_ROUTE;
      else process.env.APPLE_OFFLOAD_ROUTE = previous;
    }
  });

  it('backfills older rows without a model route', async () => {
    const stateDir = await temporary();
    const legacy = new DatabaseSync(path.join(stateDir, 'state.sqlite'));
    legacy.exec(`
      CREATE TABLE runs (
        run_id TEXT PRIMARY KEY, artifact_id TEXT, task TEXT NOT NULL, mode TEXT NOT NULL,
        route_used TEXT, status TEXT NOT NULL, coverage TEXT NOT NULL, reason TEXT,
        source_bytes INTEGER NOT NULL, output_bytes INTEGER NOT NULL, estimate_method TEXT NOT NULL,
        estimated_input_tokens INTEGER, estimated_output_tokens INTEGER, latency_ms INTEGER NOT NULL,
        validation TEXT NOT NULL, os_version TEXT, provider_version TEXT, prompt_version TEXT NOT NULL,
        workspace TEXT NOT NULL DEFAULT 'unattributed', created_at TEXT NOT NULL
      ) STRICT;
    `);
    const insert = legacy.prepare(`
      INSERT INTO runs (run_id, task, mode, route_used, status, coverage, source_bytes, output_bytes,
        estimate_method, latency_ms, validation, prompt_version, created_at)
      VALUES (?, 'diagnostics', 'on', ?, ?, 'complete', 1, 1, 'chars_div_4_v1', 1, 'passed', 'apple-offload-v0', ?)
    `);
    insert.run('served', 'local', 'ready', '2026-01-01T00:00:03.000Z');
    insert.run('unserved', 'local', 'needs_codex', '2026-01-01T00:00:02.000Z');
    insert.run('regex', 'deterministic', 'ready', '2026-01-01T00:00:01.000Z');
    legacy.close();

    const store = new Store(stateDir);
    expect(store.stats().modelRoutes).toEqual({ on_device: 1, pcc: 0 });
    expect(store.dashboard().recent.map(row => row.route)).toEqual(['on_device', null, 'deterministic']);
    store.close();
  });
});

describe('PccProvider', () => {
  // Shaped like the real macOS 27 output recorded in docs/pcc-research.md.
  const respondHelp = [
    'USAGE: fm respond [<options>] [<prompt>]',
    '  MODELS',
    '    system                  On-device Apple Foundation Model (default)'
  ].join('\n');

  function fakeFm(outputs: Record<string, string>, code = 0): FmHelpRunner & { calls: string[][] } {
    const calls: string[][] = [];
    const runner = Object.assign(async (args: string[]) => {
      calls.push(args);
      return { code, stdout: outputs[args.join(' ')] ?? '', stderr: '' };
    }, { calls });
    return runner;
  }

  it('reports fm_has_no_pcc_model when fm only lists the on-device model', async () => {
    const runner = fakeFm({ '--help': 'USAGE: fm <subcommand>', 'respond --help': respondHelp });
    const provider = new PccProvider(runner, 'darwin');
    expect(await provider.probe()).toMatchObject({ available: false, reason: 'fm_has_no_pcc_model' });
    await expect(provider.generate({ task: 'diagnostics', content: 'x', deadline: Date.now() + 1_000 }))
      .rejects.toThrow('fm_has_no_pcc_model');
    expect(runner.calls).toEqual([['--help'], ['respond', '--help']]);
  });

  it('stays unavailable even if fm starts advertising a PCC model', async () => {
    const runner = fakeFm({
      '--help': 'USAGE: fm <subcommand>',
      'respond --help': `${respondHelp}\n    pcc    Apple Private Cloud Compute model`
    });
    expect(await new PccProvider(runner, 'darwin').probe())
      .toMatchObject({ available: false, reason: 'pcc_invocation_not_implemented' });
  });

  it('surfaces the unaccepted license without trying to accept it', async () => {
    const runner = fakeFm({
      '--help': 'YOU HAVE NOT AGREED TO THE APPLE FOUNDATION MODELS CLI LEGAL NOTICE & TERMS.'
    }, 1);
    expect(await new PccProvider(runner, 'darwin').probe())
      .toMatchObject({ available: false, reason: 'fm_license_not_accepted' });
    expect(runner.calls.flat()).not.toContain('license');
  });

  it('requires macOS without running fm elsewhere', async () => {
    const runner = fakeFm({});
    expect(await new PccProvider(runner, 'linux').probe())
      .toMatchObject({ available: false, reason: 'macos_27_required' });
    expect(runner.calls).toEqual([]);
  });
});
