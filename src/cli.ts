#!/usr/bin/env node
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { Task } from './schemas.js';
import { TaskSchema } from './schemas.js';
import { AppleOffloadRuntime } from './runtime.js';

function usage(): never {
  throw new Error('usage: apple-offload <doctor|process|read|feedback|stats|eval|purge> [arguments]');
}

function print(value: unknown): void {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

async function evaluate(manifestPath: string, parent: AppleOffloadRuntime): Promise<Record<string, unknown>> {
  const manifest = JSON.parse(await readFile(path.resolve(manifestPath), 'utf8')) as Array<{
    task: Task;
    input: string;
    minimumFacts: number;
  }>;
  if (!Array.isArray(manifest)) throw new Error('eval manifest must be an array');
  const temporary = await mkdtemp(path.join(parent.stateDir, 'eval-'));
  const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [temporary], stateDir: parent.stateDir });
  let passed = 0;
  try {
    await runtime.initialize();
    for (const [index, item] of manifest.entries()) {
      TaskSchema.parse(item.task);
      const file = path.join(temporary, `${index}.txt`);
      await writeFile(file, item.input, { mode: 0o600 });
      const result = await runtime.process({ task: item.task, path: file });
      const facts = result.payload && 'diagnostics' in result.payload
        ? result.payload.diagnostics.length
        : result.payload && 'files' in result.payload
          ? result.payload.files.length
          : result.payload
            ? result.payload.requirements.length + result.payload.acceptanceCriteria.length
            : 0;
      if (result.status === 'ready' && facts >= item.minimumFacts) passed += 1;
    }
    return { cases: manifest.length, passed, failed: manifest.length - passed };
  } finally {
    runtime.close();
    await rm(temporary, { recursive: true, force: true });
  }
}

async function main(argv = process.argv.slice(2)): Promise<void> {
  const [command, ...args] = argv;
  if (!command) usage();
  const runtime = new AppleOffloadRuntime();
  await runtime.initialize();
  try {
    if (command === 'doctor' && args.length === 0) print(await runtime.doctor());
    else if (command === 'process' && args.length === 2) {
      print(await runtime.process({ task: TaskSchema.parse(args[0]), path: args[1] }));
    } else if (command === 'read' && args.length === 3) {
      print(await runtime.read({ artifactId: args[0], startLine: Number(args[1]), endLine: Number(args[2]) }));
    } else if (command === 'feedback' && args.length === 2) {
      print(runtime.feedback({ runId: args[0], outcome: args[1] }));
    } else if (command === 'stats' && args.length <= 1) {
      print(runtime.stats(args[0] ? { since: args[0] } : {}));
    } else if (command === 'eval' && args.length === 1) {
      print(await evaluate(args[0]!, runtime));
    } else if (command === 'purge' && args.length <= 1 && (!args[0] || args[0] === '--all')) {
      print(await runtime.purge(args[0] === '--all'));
    } else usage();
  } finally {
    runtime.close();
  }
}

main().catch(error => {
  console.error(error instanceof Error ? error.message : 'apple-offload failed');
  process.exitCode = 1;
});
