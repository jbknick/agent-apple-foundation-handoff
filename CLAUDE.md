# Repository Guidance

This file is the authored, provider-neutral authority for repository work. The
bounded section below is also the sole input for the generated Codex adapter;
changes to the shared contract belong here.

<!-- BEGIN GENERATED AGENTS ADAPTER -->
## Repository contract

`CLAUDE.md` is the only authored canonical repository guide. `AGENTS.md` is generated
from its bounded adapter section. Never edit `AGENTS.md` directly;
update `CLAUDE.md`, then use `scripts/sync_generated_artifacts.py`.

### Scope and capability ownership

- The plugin ID is `apple-foundation-models-handoff`. It helps Apple-platform engineers
  design, implement, review, debug, and validate Foundation Models handoff architectures;
  it is not generic Apple Intelligence education.
- Keep exactly five narrow skills: `design-apple-foundation-models-handoff`, `implement-apple-foundation-models-handoff`,
  `review-apple-foundation-models-handoff`, `debug-apple-foundation-models-handoff`, and
  `validate-apple-foundation-models-handoff`.
- Select the one skill matching the request, then progressively disclose only
  the directly linked reference needed for that concern. Do not copy complete
  workflows into guidance, duplicate the reference corpus, or add a plugin-local
  worker.
- Foundation Models handoff, coding-session handoff, Apple Handoff, App Intents,
  Claude/Codex Agent Skills, and Foundation Models runtime Skills are distinct.

### Canonical and generated paths

- Authored canonical inputs include `CLAUDE.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `metadata/codex-interface.json`, `metadata/codex-marketplace.json`, `skills/**`, and `references/**`.
- `AGENTS.md`, `.codex-plugin/plugin.json`, and `.agents/plugins/marketplace.json` are generated,
  non-editable outputs of the shared synchronization entry point.
- Preferred source `./` is conditional on isolated cache inspection and fresh
  real-host activation/reference proof. The deterministic fallback is
  `./plugins/apple-foundation-models-handoff`; it changes placement only and
  must not use external symlinks.
- The effective cached plugin payload must exclude repository-only docs, research, fixtures, tests, and private state;
  none may appear as plugin capabilities.

### Apple API and validation truth

- Apple API claims may use only current official Apple documentation, installed
  SDK interfaces, WWDC material, and Apple-owned repositories. Structural
  production references are not Apple API authority.
- Executed evidence uses exact labels `compiled_sdk_26_5` and
  `interface_verified_sdk_26_5`. “SDK 26.x” is only an architecture-family
  boundary, never an executed evidence label.
- Compile-check Swift examples when the local SDK supports them. Otherwise mark
  the prerequisite `blocked`; label pseudocode and unsupported or beta APIs
  explicitly. Do not add Apple tutorials or unapproved Swift examples here.
- Default tests require no PCC, custom provider, credentials, paid service,
  network call, live model generation, entitlement, device hardware, or full
  Xcode. A missing prerequisite is an explicit blocker, never a false pass.

### Host, security, and evidence boundaries

- Capture one explicit executable before each host row, invoke only it, and recheck resolution and version afterward.
  Primary baselines are Claude Code `2.1.91` and Codex CLI `0.144.5`; Claude Code `2.1.140` is diagnostic only and cannot substitute.
- Claude Code uses the captured approved `2.1.91` executable with session-only `--plugin-dir <repo>` or an isolated
  install for packaging and cache tests. Codex `0.144.5` uses the captured executable with isolated `CODEX_HOME`,
  marketplace registration, plugin install/add, and then a fresh task. `codex --plugin-dir` is not an approved
  workflow for Codex `0.144.5`.
- Until DEV-135 creates plugin metadata, these loading flows are planned and conditional; they claim no discovery,
  installation, activation, reference, or capability success.
- Normalize repository location as `<repo>` and executable identity as `<host-path>`; never commit their literal
  resolutions or raw `PATH`. Never commit other private absolute paths. Initial absence, non-executability, or version mismatch is `blocked`.
- Before host operations, a missing or non-runnable executable, unavailable or malformed version, or approved-baseline
  mismatch emits a normalized `blocked` row with stable reason/version metadata before exit.
- After successful capture, resolution or version drift emits normalized `fail` before exit, invalidates the row,
  and requires a fresh run. Post-capture resolution or version drift is `fail` and invalidates the row.
- Accept only a strict single-line version. Normalize malformed, multiline, or path-bearing output to `null`; committed
  evidence uses normalized `<host-path>`, exact version or `null`, stable diagnostic class, exit code, and status.
- Raw/live prompts, responses, reasoning, tool arguments/results, credentials, private configuration, real
  user/third-party data, raw diagnostics, `.trace`, and `.xcresult` remain excluded.
- A hash-bound synthetic or approved-redacted rubric stimulus, rubric assessments with only bounded rationales, and a
  redacted summary may be committed only after the DEV-131 path, content, structured-key, classification, and hash
  scanners pass. Runtime/live-host logs, traces, and derived capability telemetry contribute normalized metadata only.
- Model output cannot grant authority or prove an effect. Enforce application-
  owned C0-C3 context classification, destination/purpose/retention grants,
  confirmation and tool gates, effect-ledger reconciliation, fail-closed
  transitions, and persistent recovery until explicit reconciliation.
- File presence, Markdown checks, discovery, installation, cache inspection,
  enabled state, and version output are structural or prerequisite evidence, not
  capability proof. Capability requires reproducible fresh-host activation,
  progressive reference loading, valid/invalid outcomes, and complete outputs.

### Local deterministic commands

```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Treat generation drift, test failure, unsafe evidence, or a missing required
host/SDK prerequisite as fail or blocked according to the contract; never weaken
an expectation to pass. Do not push, merge, tag, publish, or release unless a
separate issue explicitly authorizes that action.

Architecture decisions live in the [canonical architecture](docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md)
and its [decision record](docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md).
<!-- END GENERATED AGENTS ADAPTER -->

## Claude Code local-development note

In Claude Code, edit the canonical section above and run the write, check, and
unit-test commands before asking for review. Claude-specific interactive habits
stay outside the generated adapter and may not override its shared contract.
