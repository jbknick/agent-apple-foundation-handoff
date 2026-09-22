---
name: apple-offload
description: Route saved local diagnostic logs, Git diffs, and issue text through the apple-offload MCP tools before Codex reads the full artifact.
---

# Apple Offload

Use this skill only when the user has a saved local artifact and wants one of:

- diagnostic extraction from test, compiler, or lint output;
- a Git diff summary;
- requirements and acceptance criteria extracted from issue text.

The user or Codex must save command output through an already-approved shell
operation. This skill never executes the source command, edits code, or intercepts
another tool.

1. Call `offload_process` with the exact task and saved path. Never add `route`,
   `model`, cloud, or provider fields.
2. If status is `ready`, use the bounded payload. Call `offload_read` only for
   specific cited lines needed to answer.
3. If status is `shadow`, `needs_codex`, or `blocked`, continue in the current
   Codex session using the original artifact path. Do not invoke another model or
   claim that offloading saved context.
   If the reason is `fm_license_not_accepted`, tell the user to run
   `node ~/plugins/apple-offload/dist/cli.js setup` themselves in an interactive
   terminal, then retry.
   Never run or approve the machine-wide license flow through MCP.
4. Call `offload_feedback` only when the user or completed workflow establishes
   `accepted`, `corrected`, or `rejected`.
5. Use `offload_stats` only for local aggregate metrics. Never describe estimates
   as actual spending.

Apple inference is local, but payloads and requested evidence returned to Codex
enter the existing Codex session. The overall workflow is not offline.
