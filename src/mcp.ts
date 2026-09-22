#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import {
  FeedbackInputSchema,
  FeedbackResultSchema,
  ProcessInputSchema,
  ProcessResultSchema,
  ReadInputSchema,
  ReadResultSchema,
  StatsInputSchema,
  StatsResultSchema
} from './schemas.js';
import { AppleOffloadRuntime } from './runtime.js';

function response(value: Record<string, unknown>) {
  return {
    content: [{ type: 'text' as const, text: JSON.stringify(value) }],
    structuredContent: value
  };
}

export function createServer(runtime: AppleOffloadRuntime): McpServer {
  const server = new McpServer({ name: 'apple-offload', version: '0.1.0' });

  server.registerTool(
    'offload_process',
    {
      description: 'Process one saved local diagnostic log, Git diff, or issue artifact.',
      inputSchema: ProcessInputSchema,
      outputSchema: ProcessResultSchema
    },
    async input => response(await runtime.process(input))
  );

  server.registerTool(
    'offload_read',
    {
      description: 'Read a bounded line range from a recoverable local artifact snapshot.',
      inputSchema: ReadInputSchema,
      outputSchema: ReadResultSchema
    },
    async input => response(await runtime.read(input))
  );

  server.registerTool(
    'offload_feedback',
    {
      description: 'Record local acceptance feedback for an offload run.',
      inputSchema: FeedbackInputSchema,
      outputSchema: FeedbackResultSchema
    },
    async input => response(runtime.feedback(input))
  );

  server.registerTool(
    'offload_stats',
    {
      description: 'Return aggregate local metrics without artifact contents.',
      inputSchema: StatsInputSchema,
      outputSchema: StatsResultSchema
    },
    async input => response(runtime.stats(input))
  );

  return server;
}

async function main(): Promise<void> {
  const runtime = new AppleOffloadRuntime();
  await runtime.initialize();
  const handle = serveStdio(() => createServer(runtime));
  process.on('SIGINT', () => {
    void handle.close().finally(() => runtime.close());
  });
  console.error('apple-offload MCP server listening on stdio');
}

if (import.meta.url === new URL(process.argv[1] ?? '', 'file:').href) {
  main().catch(error => {
    console.error(error instanceof Error ? error.message : 'MCP startup failed');
    process.exitCode = 1;
  });
}
