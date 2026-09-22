import { mkdtemp, readFile, rm, symlink, utimes, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { MockProvider, type GenerateRequest, type ProbeResult, type Provider } from '../src/provider.js';
import { ProcessInputSchema } from '../src/schemas.js';
import { AppleOffloadRuntime } from '../src/runtime.js';
import { renderDashboard } from '../src/dashboard.js';

const cleanups: string[] = [];

async function temporary(): Promise<string> {
  const root = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-test-'));
  cleanups.push(root);
  return root;
}

afterEach(async () => {
  await Promise.all(cleanups.splice(0).map(root => rm(root, { recursive: true, force: true })));
});

describe('runtime', () => {
  it('turns a saved log into validated diagnostics, evidence, and one metric row', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const log = path.join(root, 'test.log');
    await writeFile(log, [
      'running tests',
      'src/math.ts:12:7: error TS2322: Type string is not assignable to number',
      'src/math.ts:18:3: warning TS6133: value is never read'
    ].join('\n'));
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir });
    await runtime.initialize();

    const result = await runtime.process({ task: 'diagnostics', path: log });

    expect(result.status).toBe('ready');
    expect(result.routeUsed).toBe('deterministic');
    expect(result.payload && 'diagnostics' in result.payload ? result.payload.diagnostics : []).toHaveLength(2);
    expect(result.evidence.map(item => item.startLine)).toEqual([2, 3]);
    const evidence = await runtime.read({ artifactId: result.artifactId, startLine: 2, endLine: 2 });
    expect(evidence.text).toContain('TS2322');
    expect(runtime.stats({}).runs).toBe(1);
    runtime.close();
  });

  it('aggregates workspaces into a metadata-only dashboard', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const log = path.join(root, 'private.log');
    await writeFile(log, 'src/math.ts:12:7: error TS2322: private detail');
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir, workspace: 'worktree-one' });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: log });

    const html = renderDashboard(runtime.dashboard());

    expect(html).toContain('worktree-one');
    expect(html).not.toContain(result.runId);
    expect(html).not.toContain(result.artifactId!);
    expect(html).not.toContain('private detail');
    expect(html).not.toContain(root);
    runtime.close();
  });

  it('rejects unknown request fields', () => {
    expect(ProcessInputSchema.safeParse({ task: 'diagnostics', path: 'x', model: 'anything' }).success).toBe(false);
    expect(ProcessInputSchema.safeParse({ task: 'diagnostics', path: 'x', route: 'local' }).success).toBe(false);
  });

  it('uses the mock provider when deterministic processing is insufficient', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'opaque.log');
    await writeFile(artifact, 'failure happened here');
    const provider = new MockProvider({
      diagnostics: [{
        id: 'D1', message: 'failure happened here', severity: 'error', path: null,
        line: null, column: null, evidenceId: 'E1'
      }],
      evidence: [{ id: 'E1', startLine: 1, endLine: 1, excerpt: 'failure happened here' }]
    });
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir, provider });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    expect(result.status).toBe('ready');
    expect(result.routeUsed).toBe('local');
    runtime.close();
  });

  it('returns needs_codex without another provider when local inference is unavailable', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'opaque.log');
    await writeFile(artifact, 'opaque input');
    const runtime = new AppleOffloadRuntime({
      mode: 'on', roots: [root], stateDir, provider: new MockProvider({}, false)
    });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    expect(result.status).toBe('needs_codex');
    expect(result.reason).toBe('mock_unavailable');
    runtime.close();
  });

  it('makes license acceptance an explicit doctor next step', async () => {
    const stateDir = await temporary();
    const provider: Provider = {
      probe: async () => ({
        available: false,
        reason: 'fm_license_not_accepted',
        osVersion: '27.0',
        providerVersion: null,
        structuredOutput: false,
        localModelVerified: false,
        argvPromptExposure: true
      }),
      generate: async () => { throw new Error('not called'); }
    };
    const runtime = new AppleOffloadRuntime({ stateDir, provider });
    await runtime.initialize();
    expect(await runtime.doctor()).toMatchObject({
      setupRequired: true,
      setupCommand: 'node dist/cli.js setup'
    });
    runtime.close();
  });

  it('withholds candidates in shadow mode', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'test.log');
    await writeFile(artifact, 'src/a.ts:1:1: error TS1: bad');
    const runtime = new AppleOffloadRuntime({ roots: [root], stateDir });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    expect(result.status).toBe('shadow');
    expect(result.payload).toBeNull();
    expect(result.evidence).toEqual([]);
    expect(await readFile(path.join(stateDir, 'candidates', `${result.runId}.json`), 'utf8')).toContain('TS1');
    runtime.close();
  });

  it('blocks paths outside roots, credential files, and symlinks', async () => {
    const root = await temporary();
    const outside = await temporary();
    const stateDir = await temporary();
    const external = path.join(outside, 'outside.log');
    await writeFile(external, 'src/a.ts:1:1: error TS1: bad');
    const credential = path.join(root, '.env');
    await writeFile(credential, 'TOKEN=secret');
    const link = path.join(root, 'link.log');
    await symlink(external, link);
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir });
    await runtime.initialize();
    expect((await runtime.process({ task: 'diagnostics', path: external })).reason).toBe('path_outside_approved_roots');
    expect((await runtime.process({ task: 'diagnostics', path: credential })).reason).toBe('credential_file_rejected');
    expect((await runtime.process({ task: 'diagnostics', path: link })).reason).toBe('symlink_rejected');
    runtime.close();
  });

  it('redacts secrets before provider input and returned evidence', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'opaque.log');
    await writeFile(artifact, 'token is ghp_123456789012345678901234567890');
    let observed = '';
    const provider: Provider = {
      probe: async () => readyProbe(),
      generate: async request => {
        observed = request.content;
        return {
          diagnostics: [{
            id: 'D1', message: 'redacted token', severity: 'warning', path: null,
            line: null, column: null, evidenceId: 'E1'
          }],
          evidence: [{ id: 'E1', startLine: 1, endLine: 1, excerpt: 'token is [REDACTED_SECRET]' }]
        };
      }
    };
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir, provider });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    expect(result.status).toBe('ready');
    expect(observed).not.toContain('ghp_');
    expect(result.evidence[0]?.excerpt).toBe('token is [REDACTED_SECRET]');
    runtime.close();
  });

  it('allows only one retry and then hands back to Codex', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'opaque.log');
    await writeFile(artifact, 'opaque input');
    let attempts = 0;
    const provider: Provider = {
      probe: async () => readyProbe(),
      generate: async () => {
        attempts += 1;
        throw new Error('malformed_output');
      }
    };
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir, provider });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    expect(result.status).toBe('needs_codex');
    expect(attempts).toBe(2);
    runtime.close();
  });

  it('enforces the total provider deadline', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'opaque.log');
    await writeFile(artifact, 'opaque input');
    const provider: Provider = {
      probe: async () => readyProbe(),
      generate: async (_request: GenerateRequest) => new Promise(() => {})
    };
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir, provider, deadlineMs: 25 });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    expect(result.status).toBe('needs_codex');
    expect(result.reason).toBe('deadline_exceeded');
    runtime.close();
  });

  it('marks coverage partial when the eight-chunk ceiling is reached', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'opaque.log');
    await writeFile(artifact, Array.from({ length: 2_600 }, (_, index) => `${index}-${'x'.repeat(100)}`).join('\n'));
    let calls = 0;
    const provider: Provider = {
      probe: async () => readyProbe(),
      generate: async request => {
        calls += 1;
        const match = /^(\d+): ([^\n]*)/.exec(request.content);
        if (!match) throw new Error('unexpected chunk');
        return {
          diagnostics: [{
            id: `D${calls}`, message: 'opaque line', severity: 'unknown', path: null,
            line: null, column: null, evidenceId: `E${calls}`
          }],
          evidence: [{ id: `E${calls}`, startLine: Number(match[1]), endLine: Number(match[1]), excerpt: match[2] }]
        };
      }
    };
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir, provider });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    expect(result.status).toBe('ready');
    expect(result.coverage).toBe('partial');
    expect(calls).toBe(8);
    runtime.close();
  });

  it('rejects sources larger than four MiB', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'large.log');
    await writeFile(artifact, 'x'.repeat(4 * 1024 * 1024 + 1));
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    expect(result.status).toBe('needs_codex');
    expect(result.reason).toBe('source_too_large');
    runtime.close();
  });

  it('records idempotent feedback and aggregates it', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'test.log');
    await writeFile(artifact, 'src/a.ts:1:1: error TS1: bad');
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    runtime.feedback({ runId: result.runId, outcome: 'accepted' });
    runtime.feedback({ runId: result.runId, outcome: 'corrected' });
    expect(runtime.stats({}).feedback).toEqual({ accepted: 0, corrected: 1, rejected: 0 });
    runtime.close();
  });

  it('purges expired snapshots', async () => {
    const root = await temporary();
    const stateDir = await temporary();
    const artifact = path.join(root, 'test.log');
    await writeFile(artifact, 'src/a.ts:1:1: error TS1: bad');
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir });
    await runtime.initialize();
    const result = await runtime.process({ task: 'diagnostics', path: artifact });
    const old = new Date(Date.now() - 25 * 60 * 60 * 1_000);
    await utimes(path.join(stateDir, 'snapshots', `${result.artifactId}.txt`), old, old);
    expect((await runtime.purge()).removed).toBeGreaterThan(0);
    await expect(runtime.read({ artifactId: result.artifactId, startLine: 1, endLine: 1 })).rejects.toThrow();
    runtime.close();
  });
});

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
