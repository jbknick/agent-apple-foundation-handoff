# Apple Offload v0 verification

Executed on 2026-09-22 with Node.js 25.8.0 and pnpm 10.31.0.

| Check | Result | Evidence class |
|---|---|---|
| TypeScript typecheck and build | Pass | Local deterministic |
| Vitest runtime, protocol, security, and 60-fixture evaluation | Pass | Local deterministic |
| CLI process/stats parity | Pass | Local deterministic |
| Repository MCP STDIO discovery and process call | Pass | Local deterministic |
| Installed personal-plugin MCP discovery and process call | Pass | Fresh local plugin cache |
| Forbidden HTTP, PCC/model flag, OAuth, sampling, and telemetry scan | Pass | Static local |
| First milestone: saved log to cited diagnostics and one SQLite run | Pass | Local deterministic |
| Installed `fm` interface capture | Pass | Help verified; no version flag exists, so version remains `null` |
| On-device structured-output smoke test without `--model` | Pass | Live local hardware |
| Opaque diagnostic routed through `fm` with validated evidence | Pass | Live local hardware |
| Network-unavailable on-device repeat | Unrun | Requires an explicit temporary network change |

The 60 held-out fixtures are deterministic extraction cases, 20 per task. They
are correctness fixtures, not a claim about Apple model quality. No Codex or
remote judge is called. Payload reduction and spending remain unmeasured because
matched imported baselines and user-entered spending observations are absent.

Installed `fm respond --help` confirms stdin prompt transport and `--no-stream`.
Artifact prompts are bounded, redacted, sent over stdin, and never logged.
