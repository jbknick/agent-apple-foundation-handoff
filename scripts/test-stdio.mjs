import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const root = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-stdio-'));
const state = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-stdio-state-'));
const artifact = path.join(root, 'test.log');
await writeFile(artifact, 'src/a.ts:1:1: error TS1: broken');

const client = new Client({ name: 'stdio-check', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: ['dist/mcp.js'],
  cwd: process.cwd(),
  env: {
    ...process.env,
    APPLE_OFFLOAD_MODE: 'on',
    APPLE_OFFLOAD_ROOTS: root,
    APPLE_OFFLOAD_STATE_DIR: state
  },
  stderr: 'pipe'
});

try {
  await client.connect(transport);
  const tools = await client.listTools();
  if (tools.tools.length !== 4) throw new Error('expected four MCP tools');
  const result = await client.callTool({
    name: 'offload_process',
    arguments: { task: 'diagnostics', path: artifact }
  });
  if (result.structuredContent?.status !== 'ready') throw new Error('STDIO process call failed');
} finally {
  await client.close();
  await rm(root, { recursive: true, force: true });
  await rm(state, { recursive: true, force: true });
}
