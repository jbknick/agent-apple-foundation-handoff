import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const root = mkdtempSync(path.join(os.tmpdir(), 'apple-offload-cli-'));
const state = mkdtempSync(path.join(os.tmpdir(), 'apple-offload-cli-state-'));
const artifact = path.join(root, 'test.log');
writeFileSync(artifact, 'src/a.ts:1:1: error TS1: broken');
const env = {
  ...process.env,
  APPLE_OFFLOAD_MODE: 'on',
  APPLE_OFFLOAD_ROOTS: root,
  APPLE_OFFLOAD_STATE_DIR: state
};

try {
  const processResult = JSON.parse(execFileSync(process.execPath, ['dist/cli.js', 'process', 'diagnostics', artifact], { env, encoding: 'utf8' }));
  if (processResult.status !== 'ready' || processResult.routeUsed !== 'deterministic') {
    throw new Error('CLI process did not match runtime result');
  }
  const stats = JSON.parse(execFileSync(process.execPath, ['dist/cli.js', 'stats'], { env, encoding: 'utf8' }));
  if (stats.runs !== 1) throw new Error('CLI stats did not persist one run');
} finally {
  rmSync(root, { recursive: true, force: true });
  rmSync(state, { recursive: true, force: true });
}
