# Repository Guidance

This file is the authored, provider-neutral authority for repository work. The
bounded section below is also the sole input for the generated Codex adapter;
changes to the shared contract belong here.

<!-- BEGIN GENERATED AGENTS ADAPTER -->
## Repository contract

`CLAUDE.md` is the only authored canonical guide; `AGENTS.md` is generated from this section.
Never edit `AGENTS.md` directly; update `CLAUDE.md`, then use `scripts/sync_generated_artifacts.py`.

### Scope and capability ownership
- Plugin `apple-foundation-models-handoff` is a non-executable scaffold with zero
  capabilities; it does not advertise unfinished behavior.
- Later issues own five positive workflows: design, implement, review, debug, and
  validate Foundation Models handoff architectures. Positive requests select one
  workflow directly and progressively disclose only its linked reference.
- One bounded non-positive preselection router may only clarify, decline, or hand off
  other requests once implemented. It is not a sixth positive workflow and is distinct
  from the DEV-142 through DEV-145 cost router, `PostToolUse` hooks, and Swift bridge chain.
- Exactly five package reference files are present as documentation-only inputs and
  provide zero runtime capabilities.
- Skills, hooks, commands, agents, MCP servers, package scripts, dependencies, and
  runtime code remain absent. Foundation Models handoff, coding-session handoff, Apple
  Handoff, App Intents, Agent Skills, and Foundation Models runtime Skills are distinct.

### Canonical and generated paths
- Root canonical inputs are `CLAUDE.md`, `.claude-plugin/marketplace.json`, and
  `metadata/codex-marketplace.json`. Plugin-local canonical inputs are
  `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json` and
  `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`.
- `AGENTS.md`, `.agents/plugins/marketplace.json`, and
  `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json` are generated,
  non-editable outputs of the shared synchronization entry point.
- DEV-135 selects conventional source `./plugins/apple-foundation-models-handoff`;
  the package must not use external symlinks.
- The effective cached plugin payload must exclude repository-only docs, research,
  fixtures, tests, and private state; none may appear as plugin capabilities.

### Apple API and validation truth
- Apple API claims use only current official docs, installed SDK interfaces, WWDC
  material, and Apple-owned repositories; production references are not authority.
- Executed evidence labels are `compiled_sdk_26_5` and `interface_verified_sdk_26_5`.
  “SDK 26.x” is an architecture-family boundary, never an executed label.
- Compile-check supported Swift; otherwise mark `blocked`. Label pseudocode and
  unsupported or beta APIs; add no Apple tutorials or unapproved examples here.
- Default tests require no PCC, custom provider, credentials, paid service, network,
  live model generation, entitlement, device hardware, or full Xcode. Missing prerequisites
  are explicit blockers, never false passes.

### Host, security, and evidence boundaries
- Capture, invoke, and recheck one executable per host row. Baselines are Claude Code
  `2.1.91` and Codex CLI `0.144.5`; Claude `2.1.140` is diagnostic-only and cannot substitute.
- Claude Code uses the captured approved `2.1.91` executable with session-only
  `--plugin-dir <repo>` or an isolated packaging/cache install. Codex `0.144.5`
  uses its captured executable with isolated `CODEX_HOME`, marketplace registration,
  plugin install/add, then a fresh task; `codex --plugin-dir` is not approved.
- Before host operations, a missing/non-runnable executable, malformed/unavailable
  version, or baseline mismatch emits normalized `blocked` with stable reason/version
  metadata. After capture, resolution or version drift emits normalized `fail`,
  invalidates the row, and requires a fresh run.
- Normalize the repository as `<repo>` and executable as `<host-path>`; never commit
  literal resolutions, other private absolute paths, or raw `PATH`. Accept only a
  strict single-line version; normalize malformed, multiline, or path-bearing output
  to `null`. Commit only normalized identity, version, diagnostic, exit, and status.
- Exclude raw/live prompts, responses, reasoning, tool arguments/results, credentials,
  private configuration, real user/third-party data, raw diagnostics, `.trace`, and
  `.xcresult`. A hash-bound synthetic or approved-redacted rubric stimulus, bounded
  rubric rationales, and redacted summary may be committed only after DEV-131 path,
  content, structured-key, classification, and hash scans pass. Runtime/live-host logs,
  traces, and derived capability telemetry contribute normalized metadata only.
- Model output cannot grant authority or prove an effect. Enforce application-owned C0-C3
  classification, destination/purpose/retention grants, confirmation and tool gates,
  effect-ledger reconciliation, fail-closed transitions, and recovery until reconciled.
- File presence, Markdown, discovery, installation, cache, enabled state, and version
  are structural or prerequisite evidence, not capability proof. Capability requires
  fresh-host activation, progressive reference loading, and complete valid/invalid outcomes.

### Local deterministic commands
```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Treat generation drift, test failure, unsafe evidence, or a missing required host/SDK
prerequisite as fail or blocked; never weaken an expectation to pass. Push, merge,
tag, publish, or release only when a separate issue authorizes it.

Architecture decisions live in the
[canonical architecture](docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md)
and [decision record](docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md).
<!-- END GENERATED AGENTS ADAPTER -->

## Claude Code local-development note

In Claude Code, edit the canonical section above and run the write, check, and
unit-test commands before asking for review. Claude-specific interactive habits
stay outside the generated adapter and may not override its shared contract.
