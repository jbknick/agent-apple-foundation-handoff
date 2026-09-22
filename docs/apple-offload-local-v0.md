# Apple Offload — Local-Only v0

PRD, HLD & Technical Design

Version: v0.2 | 2026-09-22 | Implementation brief for Codex

**Scope decision:** v0 uses only Apple on-device inference. PCC is deferred because its usable per-user allowance has not been established for this workflow. Do not implement PCC adapters, flags, configuration, quota handling or placeholders.

## 1. PRD

**Goal:** Reduce unnecessary Codex context and delegated language work by processing local artifacts with Apple Foundation Models before Codex reads them. Preserve correctness, evidence and user control.

**Target:** Personal development on an Apple Intelligence-capable Mac running macOS 27. Codex is the first host; keep the runtime host-independent.

**v0 scope:** Three read-only operations: extract test/compiler/lint diagnostics; summarize Git diffs; extract requirements and acceptance criteria from issue text. Deliver a local MCP server, one routing skill, a standalone CLI, and local metrics. The plugin performs no runtime network calls or remote inference.

**Excluded:** All cloud inference and automatic cloud fallback, code edits, autonomous debugging, arbitrary command execution, transparent interception of Codex tools, remote workers, web dashboards, third-party routers, automatic subscription management.

**Workflow:** Codex uses its existing approved shell to save command output locally, preserving the original exit status without printing the log. It passes the artifact path to this plugin, receives a bounded result, and requests specific evidence only when necessary. The standalone CLI runs the same operations without invoking Codex.

**Release targets, not measured claims:** At least 95% task correctness on held-out fixtures; 100% retention of annotated critical diagnostic IDs; at least 60% median reduction of visible diagnostic payloads versus the normal baseline. Failures must remain recoverable.

## 2. HLD

```text
Codex skill → local STDIO MCP ─┐
Standalone CLI ───────────────┴→ shared runtime
                                  ↓
                       validate path / snapshot
                                  ↓
                      deterministic preprocessing
                                  ↓
                       Apple on-device only
                                  ↓
                      schema + evidence validation
                                  ↓
                       bounded result or handback
                                  └→ SQLite metrics
```

Integration targets: Apple’s local `fm` CLI [S1], Codex local STDIO MCP [S2], and skill/MCP packaging [S3]. Verify installed interfaces on the target Mac before implementation; do not invent unavailable APIs.

Use TypeScript, pnpm, the official MCP SDK, Zod, SQLite and Vitest. Invoke Apple's installed `fm` through an isolated provider adapter; do not implement a model gateway or add Swift/Python to v0.

**Routing:** Return deterministic results when sufficient; otherwise use only the on-device model. Unsupported tasks, unavailable local inference or generation failures return `needs_codex`. This is a status handed back to the existing Codex session, not a remote call. No cloud fallback or runtime provider selection.

## 3. Technical Design

### Interfaces

| Interface | Contract |
|---|---|
| `offload_process` | `{task: diagnostics\|diff_summary\|issue_extract, path}` |
| `offload_read` | `{artifactId, startLine, endLine}`; bounded, explicitly requested evidence |
| `offload_feedback` | `{runId, outcome: accepted\|corrected\|rejected}` |
| `offload_stats` | `{since?}`; aggregate metrics, no artifact contents |
| CLI | `doctor`, `process`, `read`, `feedback`, `stats`, `eval`, `purge` |

Processing returns `{runId, status, routeUsed, artifactId, payload, evidence, coverage, reason}`. Status is `ready | shadow | needs_codex | blocked`; coverage is `complete | partial`. `routeUsed` is `deterministic | local`, or `null` if no processing occurred. Metadata comes from the runtime, not the model. Use strict request schemas: reject unknown fields, including `route` or `model`; expose no cloud options in CLI/configuration.

Use fixed schemas per task: diagnostic IDs/messages/locations; diff changes by file; issue requirements/acceptance criteria. Each extracted fact links to source lines. Unknowns remain explicit; do not invent root causes, requirements or paths. Validate quoted evidence against the immutable source snapshot.

### Execution and safety

**Provider:** Implement one local adapter with `probe()` and `generate()`. `doctor` checks the OS, `fm` availability and a local structured-output smoke test. Verify installed flags, local-only execution semantics and schema format using installed help/documentation; do not assume Apple's schema format is generic JSON Schema. Fail closed if on-device execution cannot be established. Record actual capabilities; unavailable token/model details stay `null`. No cloud adapters or multi-provider registry.

**Limits:** Default to one generation at a time, 4 MiB source limit, eight chunks, a 30-second total processing deadline, including all chunks and retries, and a 1,200-token estimated response budget. Configure MCP timeout above this deadline. Chunk at diagnostic/diff boundaries and preserve line mappings. Budget prompts, schemas and output together; never assume a universal context size. Incomplete processing is `partial`, never silently complete.

**Failures:** Allow one bounded retry within the deadline. Unavailable local model, context overflow, timeout or invalid evidence returns an explicit reason and recoverable artifact ID. Never dump raw input automatically or retry through a remote provider.

**Security:** Restrict canonical paths to user-approved roots; reject symlink escapes and credential files. Treat artifact text as untrusted data, not instructions. No model tools or shell-string execution. Invoke `fm` with argument arrays and `shell:false`; prefer documented stdin/file transport. Flag argv prompt exposure when that is the only supported transport. Do not log prompts. Apply redaction to both provider inputs and returned results. **Privacy boundary:** Plugin inference, evaluation and telemetry remain local. Summaries and requested evidence returned to Codex enter its existing session; the overall Codex workflow is not offline.

Store snapshots outside Git with owner-only permissions and 24-hour expiry. SQLite stores metadata only; provide purge. Write only plugin-owned state, never repository source files.

### Rollout and measurement

Modes are user-controlled: `off` bypasses; default `shadow` stores candidates but returns no candidate content to the working Codex session; `on` returns validated results. Shadow evaluation leaves the normal workflow unchanged and incurs evaluation overhead, not savings.

Record run ID, task, routeUsed, mode, source/output sizes, tokenizer/estimate method, latency, validation, coverage, needs_codex handbacks, feedback and OS/provider/prompt versions. Feedback measures acceptance, not correctness; fixtures measure correctness separately.

Report three separate quantities:

- **Payload reduction:** Baseline visible payload minus the full replacement payload; include tool/schema overhead and evidence fetches. Compare against normal truncation, not an unlimited raw log.
- **Estimated API equivalent:** Use dated, configurable input/cached-input/output prices and paired workload measurements; include retries, failed offloads and subsequent handback work when observed. Never substitute Apple token counts for OpenAI counts.
- **Actual spending:** User-entered or locally imported allowance/credit/purchase observations, separate from estimates. No automatic token-to-subscription-credit conversion or online usage polling. Use the applicable Codex usage documentation when interpreting observations [S4].

Keep evaluation local: deterministic fixture grading plus human review; no remote model judges. Import separately captured Codex baselines rather than calling Codex from the evaluator. Use `null`, not zero, for unavailable measurements. Report negative deltas. Do not count shadow work, duplicate runs or already-visible input as avoided initial ingestion.

## 4. Codex Implementation Order

1. Inspect `AGENTS.md` and repository conventions; preserve existing shared plugin metadata. Verify Apple/Codex interfaces on the target Mac and document blockers.
2. Scaffold the host-independent runtime, fixed schemas, mock provider, security checks and SQLite migrations.
3. Implement artifact processing and only the local `fm` adapter. Verify processing with network access disabled after the required local model is installed; document blockers rather than adding another provider.
4. Wire MCP, CLI and routing skill; package using the current documented Codex manifest. Test installation in a fresh session.
5. Add 60 held-out fixtures, 20 per task, plus path traversal, prompt injection, malformed JSON, overflow, timeout, unavailable-local-model and partial-coverage tests. Assert remote options are rejected and failure paths make no network calls. Compare against locally imported, matched Codex baselines with the same Codex model/settings.

**Done:** Tests pass; local Mac smoke test and offline processing test pass; no cloud configuration, cloud-provider code or runtime network calls exist; source files remain unchanged; evidence drill-down works; failed routes remain recoverable; metrics distinguish estimates from spending. Deliver install/uninstall instructions, example workflow, benchmark report and known limitations. Hardware-dependent tests must be reported as unrun when no compatible Mac is available.

## Source references

References retained from the previous brief, not reverified for this scope-only revision. Codex must verify relevant interfaces on the target Mac before coding.

```text
[S1] Apple: Build AI-powered scripts with the fm CLI and Python SDK
https://developer.apple.com/videos/play/wwdc2026/334/
[S2] OpenAI: Model Context Protocol
https://developers.openai.com/codex/mcp/
[S3] OpenAI: Build plugins
https://developers.openai.com/codex/build-plugins
[S4] OpenAI: Using Codex with your ChatGPT plan
https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
```
