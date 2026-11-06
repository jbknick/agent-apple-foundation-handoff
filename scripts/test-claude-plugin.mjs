// Launches the Claude Code plugin's MCP server the way Claude Code does:
// variables in .claude-plugin/plugin.json are expanded, and the process runs
// from an unrelated directory so nothing depends on its working directory.
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const pluginRoot = path.resolve('plugins/apple-offload');
const manifest = JSON.parse(await readFile(path.join(pluginRoot, '.claude-plugin/plugin.json'), 'utf8'));
const server = manifest.mcpServers?.apple_offload;
if (!server) throw new Error('plugin.json must declare the apple_offload MCP server');

const project = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-claude-project-'));
const outside = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-claude-outside-'));
const state = await mkdtemp(path.join(os.tmpdir(), 'apple-offload-claude-state-'));
const expand = value =>
  value.replaceAll('${CLAUDE_PLUGIN_ROOT}', pluginRoot).replaceAll('${CLAUDE_PROJECT_DIR}', project);

const inside = path.join(project, 'test.log');
const elsewhere = path.join(outside, 'test.log');
await writeFile(inside, 'src/a.ts:1:1: error TS1: broken');
await writeFile(elsewhere, 'src/a.ts:1:1: error TS1: broken');

const client = new Client({ name: 'claude-plugin-check', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: server.command === 'node' ? process.execPath : server.command,
  args: server.args.map(expand),
  cwd: os.tmpdir(),
  env: {
    ...process.env,
    ...Object.fromEntries(Object.entries(server.env ?? {}).map(([key, value]) => [key, expand(value)])),
    APPLE_OFFLOAD_STATE_DIR: state
  },
  stderr: 'pipe'
});

try {
  await client.connect(transport);
  const names = (await client.listTools()).tools.map(tool => tool.name).sort();
  const expected = ['offload_feedback', 'offload_process', 'offload_read', 'offload_stats'];
  if (JSON.stringify(names) !== JSON.stringify(expected)) throw new Error(`unexpected tools: ${names}`);
  const allowed = await client.callTool({ name: 'offload_process', arguments: { task: 'diagnostics', path: inside } });
  if (allowed.structuredContent?.status !== 'shadow') throw new Error('project file was not processed in shadow mode');
  const denied = await client.callTool({ name: 'offload_process', arguments: { task: 'diagnostics', path: elsewhere } });
  if (!denied.isError && denied.structuredContent?.status !== 'blocked') {
    throw new Error('a file outside the project directory was processed');
  }
} finally {
  await client.close();
  await Promise.all([project, outside, state].map(dir => rm(dir, { recursive: true, force: true })));
}
