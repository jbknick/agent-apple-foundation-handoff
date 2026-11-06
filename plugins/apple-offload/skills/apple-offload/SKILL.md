---
name: apple-offload
description: Route saved local diagnostic logs, Git diffs, and issue text through the apple-offload MCP tools before you read the full artifact.
---

# Apple Offload

Use this skill only when the user has a saved local artifact and wants one of:

- diagnostic extraction from test, compiler, or lint output;
- a Git diff summary;
- requirements and acceptance criteria extracted from issue text.

The user or the agent must save command output through an already-approved shell
operation. This skill never executes the source command, edits code, or intercepts
another tool.

1. Call `offload_process` with the exact task and saved path. Never add `route`,
   `model`, or provider fields: the route (on-device, or Apple PCC when the user
   opted in) comes from the user's configuration, not from the agent.
2. If status is `ready`, use the bounded payload. Call `offload_read` only for
   specific cited lines needed to answer.
3. If status is `shadow`, `needs_agent`, or `blocked`, continue in the current
   agent session using the original artifact path. Do not invoke another model
   or claim that offloading saved context.
   (Deprecated: `needs_agent` was `needs_codex`; results still carry
   `legacyStatus: "needs_codex"` for one minor release.)
   If the reason is `fm_license_not_accepted`, tell the user to run the plugin's
   `dist/cli.js setup` themselves in an interactive terminal, then retry. Codex
   personal install: `node ~/plugins/apple-offload/dist/cli.js setup`. Claude Code:
   the same command from the installed plugin directory.
   Never run or approve the machine-wide license flow through MCP.
4. Call `offload_feedback` only when the user or completed workflow establishes
   `accepted`, `corrected`, or `rejected`.
5. Use `offload_stats` only for local aggregate metrics. Never describe estimates
   as actual spending.

Apple inference is local, but payloads and requested evidence returned to the
agent enter its existing session. The overall workflow is not offline.
