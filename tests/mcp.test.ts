import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { Client, InMemoryTransport } from '@modelcontextprotocol/client';
import { afterEach, expect, it } from 'vitest';
import { createServer } from '../src/mcp.js';
import { AppleOffloadRuntime } from '../src/runtime.js';

const cleanups: string[] = [];
afterEach(async () => {
  await Promise.all(cleanups.splice(0).map(root => rm(root, { recursive: true, force: true })));
});

it('exposes the four tools over the official protocol transport', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-mcp-'));
  const stateDir = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-state-'));
  cleanups.push(root, stateDir);
  const log = path.join(root, 'test.log');
  await writeFile(log, 'src/a.ts:4:2: error TS1001: broken');
  const runtime = new AppleOffloadRuntime({ mode: 'on', roots: [root], stateDir });
  await runtime.initialize();
  const server = createServer(runtime);
  const client = new Client({ name: 'test-client', version: '1.0.0' });
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await server.connect(serverTransport);
  await client.connect(clientTransport);

  const tools = await client.listTools();
  expect(tools.tools.map(tool => tool.name).sort()).toEqual([
    'offload_feedback', 'offload_process', 'offload_read', 'offload_stats'
  ]);
  const result = await client.callTool({
    name: 'offload_process',
    arguments: { task: 'diagnostics', path: log }
  });
  expect(result.structuredContent).toMatchObject({ status: 'ready', routeUsed: 'deterministic' });
  const rejected = await client.callTool({
    name: 'offload_process',
    arguments: { task: 'diagnostics', path: log, model: 'pcc' }
  });
  expect(rejected.isError).toBe(true);

  await client.close();
  await server.close();
  runtime.close();
});
