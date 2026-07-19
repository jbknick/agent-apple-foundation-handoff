# Repository Guidance

This file is the authored, provider-neutral authority for repository work. The
bounded section below is also the sole input for the generated Codex adapter;
changes to the shared contract belong here.

<!-- BEGIN GENERATED AGENTS ADAPTER -->
## Repository contract

`CLAUDE.md` is the only authored canonical guide; `AGENTS.md` is generated. Never edit `AGENTS.md` directly; use `scripts/sync_generated_artifacts.py`.

### Scope and capability ownership

- DEV-135 installed the metadata scaffold. The package exposes five workflows plus one non-positive router. The five production workflows are implemented: `design-apple-foundation-models-handoff`, `implement-apple-foundation-models-handoff`,
  `review-apple-foundation-models-handoff`, `debug-apple-foundation-models-handoff`, and `validate-apple-foundation-models-handoff`. `route-apple-foundation-models-handoff` is the non-positive router; it is not a workflow.
- Before selecting any positive workflow, resolve non-positive pre-selection in this order: `domain = out_of_domain`, `domain = ambiguous`, then a confirmed implementation request missing an approved architecture or exact change boundary.
- Set `domain = foundation_models_handoff` only for explicit Apple Foundation Models session, profile, or provider coordination; set `domain = ambiguous` for bare `Apple handoff` regardless of operation, artifact, failure, or evidence wording; set `domain = out_of_domain` for App Intents or Shortcuts, Apple Handoff or NSUserActivity, generic Swift or actors, generic Core ML, coding-session handoff, Agent Skills, and Foundation Models runtime Skills.
- For any of those cases, select and load only `route-apple-foundation-models-handoff`, copy its exact matching branch before inspection or non-skill tool use, and select no positive workflow.
- The bounded non-positive preselection router may only clarify, decline, or hand off
  those requests. It is not a sixth positive workflow and is distinct from the
  DEV-142 through DEV-145 cost router, `PostToolUse` hooks, and Swift bridge chain.
- Treat pre-selection as one closed compilation transaction: resolve and freeze `domain`, `requestedOperation`, `artifactState`, and `evidenceState` exactly once; emit a router-owned outcome immediately before positive selection, or pass the same frozen tuple to the one selected positive workflow for unchanged serialization without re-inference.
- On positive activation, `routerInput` is an immutable pre-selection record, not a workflow finding. Serialize the exact four normalized values from the source request in the shown field order; never use inspection, execution, evidence results, or drafted output to infer or revise a value. This serialization neither invokes nor emulates the router and has no branch or ownership effect.
- Treat a request asking only about Swift actors, actor isolation, or a Swift example as `domain = out_of_domain` even when it asks for implementation; select only `route-apple-foundation-models-handoff` and return its `no_activation` result before positive selection.
- Otherwise select exactly one matching positive workflow; once selected, it remains the only workflow owner for the request. Load one needed reference; never copy workflows or reference corpora or add a plugin-local worker.

### Canonical and generated paths
- Canonical inputs: `CLAUDE.md`, `.claude-plugin/marketplace.json`, `metadata/codex-marketplace.json`, `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`, and `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`.
  `skills/**` and `references/**` are current plugin-local canonical inputs. DEV-137 references are integrated and link-resolved.
- `AGENTS.md`, `.agents/plugins/marketplace.json`, and `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
  are generated, non-editable outputs.
- DEV-135 selects conventional source `./plugins/apple-foundation-models-handoff`; the package must not use external symlinks.
- The effective cached plugin payload must exclude repository-only docs, research, fixtures, tests, and private state;
  none may appear as plugin capabilities.

### Apple API and validation truth

- Apple API claims use only current official docs, installed SDK interfaces, WWDC material, and Apple-owned repositories; production references are not authority.
- Executed evidence labels are `compiled_sdk_26_5` and `interface_verified_sdk_26_5`; “SDK 26.x” is an architecture-family boundary, never an executed label.
- Compile-check supported Swift; otherwise mark `blocked`. Label pseudocode and unsupported or beta APIs; add no Apple tutorials or unapproved examples.
- Default tests require no PCC, custom provider, credentials, paid service, network, live model generation, entitlement, device hardware, or full Xcode. Missing prerequisites are blockers, never passes.

### Host, security, and evidence boundaries
- Capture one explicit executable before each host row, invoke only it, and recheck resolution and version afterward.
  Primary baselines are Claude Code `2.1.91` and Codex CLI `0.144.5`; Claude Code `2.1.140` is diagnostic only and cannot substitute.
- Claude Code uses the captured approved `2.1.91` executable with session-only `--plugin-dir <repo>` or an isolated
  install for packaging and cache tests. Codex `0.144.5` uses the captured executable with isolated `CODEX_HOME`,
  marketplace registration, plugin install/add, and then a fresh task. `codex --plugin-dir` is not an approved
  workflow for Codex `0.144.5`.
- DEV-135 provides metadata for structural discovery and installation. DEV-136 host evidence is Codex-only.
  Claude execution and cross-host comparison are `blocked/owner-deferred`.
  Behavioral capability claims require fresh exact-model DEV-136 forward evidence.
  Structural integration alone is not a pass.
- Normalize repository location as `<repo>` and executable identity as `<host-path>`; never commit their literal
  resolutions or raw `PATH`. Never commit other private absolute paths. Initial absence, non-executability, or version mismatch is `blocked`.
- Before host operations, a missing or non-runnable executable, unavailable or malformed version, or approved-baseline
  mismatch emits a normalized `blocked` row with stable reason/version metadata before exit.
- After successful capture, resolution or version drift emits normalized `fail` before exit, invalidates the row,
  and requires a fresh run.
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
- Discovery, file presence, and installation are structural prerequisites and cannot prove behavioral or capability activation.
  Markdown checks, cache inspection, enabled state, and version output are likewise prerequisite evidence. Capability requires
  reproducible fresh-host activation, progressive reference loading, valid/invalid outcomes, and complete outputs.

### Local deterministic commands
```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Generation drift, test failure, unsafe evidence, or missing prerequisites are fail or blocked; never weaken expectations. Push, merge, tag, publish, or release only when separately authorized.

Architecture decisions live in the
[canonical architecture](docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md)
and [decision record](docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md).
<!-- END GENERATED AGENTS ADAPTER -->

## Claude Code local-development note

In Claude Code, edit the canonical section above and run the write, check, and
unit-test commands before asking for review. Claude-specific interactive habits
stay outside the generated adapter and may not override its shared contract.
