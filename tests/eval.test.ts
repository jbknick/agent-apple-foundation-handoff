import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { expect, it } from 'vitest';
import { AppleOffloadRuntime } from '../src/runtime.js';

it('passes all 60 held-out deterministic fixtures', async () => {
  const fixtures = JSON.parse(await readFile(new URL('./fixtures/eval.json', import.meta.url), 'utf8')) as Array<{
    task: 'diagnostics' | 'diff_summary' | 'issue_extract';
    input: string;
    minimumFacts: number;
  }>;
  expect(fixtures).toHaveLength(60);
  const root = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-eval-'));
  const stateDir = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-eval-state-'));
  try {
    const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir });
    await runtime.initialize();
    for (const [index, fixture] of fixtures.entries()) {
      const file = path.join(root, `${index}.txt`);
      await writeFile(file, fixture.input);
      const result = await runtime.process({ task: fixture.task, path: file });
      expect(result.status, `fixture ${index}`).toBe('ready');
      const count = result.payload && 'diagnostics' in result.payload
        ? result.payload.diagnostics.length
        : result.payload && 'files' in result.payload
          ? result.payload.files.length
          : result.payload
            ? result.payload.requirements.length + result.payload.acceptanceCriteria.length
            : 0;
      expect(count, `fixture ${index}`).toBeGreaterThanOrEqual(fixture.minimumFacts);
    }
    runtime.close();
  } finally {
    await rm(root, { recursive: true, force: true });
    await rm(stateDir, { recursive: true, force: true });
  }
});
