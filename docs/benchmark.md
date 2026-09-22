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
| Installed `fm` help/version capture | Blocked | Apple terms not accepted |
| On-device structured-output smoke test without `--model` | Unrun | Requires terms acceptance |
| Network-unavailable on-device repeat | Unrun | Requires successful live smoke first |

The 60 held-out fixtures are deterministic extraction cases, 20 per task. They
are correctness fixtures, not a claim about Apple model quality. No Codex or
remote judge is called. Payload reduction and spending remain unmeasured because
matched imported baselines and user-entered spending observations are absent.

Known limitation: Apple's published WWDC26 examples pass prompts positionally.
Until installed help can be inspected after terms acceptance, `doctor` reports
`argvPromptExposure: true`; prompts are bounded, redacted, and never logged.
