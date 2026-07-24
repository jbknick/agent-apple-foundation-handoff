# Codex-Only Apple Foundation Models Runtime Completion Design

Project:
[Agent Apple Foundation Handoff](https://linear.app/devprentice/project/agent-apple-foundation-handoff-8297ee383b88)

Decision date: `2026-07-23`

Approved direction: the user confirmed that this project uses Apple Foundation
Models only during Codex runs through the Codex plugin system. The previously
suggested mobile/TestFlight scope belonged to another project and is excluded.
The user approved the corrected issue breakdown with `lgtm`.

Baseline amendment: on `2026-07-24`, the user replaced the active and future
Codex execution baseline with exact Codex CLI `0.145.0`. Historical evidence
captured on `0.144.5` remains immutable and may not satisfy a current host row.

## Summary and baseline

The repository baseline is `main` at `b6b2289`, matching `origin/main` after a
fresh fetch. DEV-142 is complete and supplies the frozen
`diagnostic-condensation-v1` request, policy, result, privacy, fallback, and
benchmark corpus contracts. The repository does not yet contain a production
Apple bridge or Codex runtime hook.

The approved conditional runtime path was deliberately narrow:

```text
completed eligible Codex Bash result
  -> trusted Codex plugin PostToolUse boundary
  -> DEV-142 deterministic cost router
  -> DEV-246 exact-host result-replacement capability gate
  -> blocked: host_replacement_unavailable
```

Apple Foundation Models is the only generation provider in this path. The
runtime has no mobile application, Claude Code adapter, external model, PCC,
remote fallback, credential, paid service, or network inference.

The five positive workflow skills and the non-positive preselection router
remain separate guidance capabilities. This decision narrows only the
diagnostic-condensation runtime and its release evidence; it does not silently
remove existing shared metadata or rewrite completed workflow evidence.

## Authority and bounded supersession

The following sources remain authoritative unless this design expressly narrows
their downstream runtime scope:

- `docs/superpowers/specs/2026-07-21-dev-142-runtime-cost-routing-and-benchmark-design.md`
- `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- current official Codex plugin and hook documentation
- the installed SDK interfaces and executed evidence required by `AGENTS.md`

DEV-142's versioned request, routing, validation, privacy, fallback, and
correctness contracts remain unchanged. Its former two-host runtime ownership
and release matrix were conditionally narrowed as follows:

- DEV-145's Claude Code runtime adapter is canceled as out of scope.
- Historical 48-pair/96-arm cross-host deterministic evidence remains truthful
  for DEV-142's completed contract work.

This is a product-scope amendment, not permission to weaken the DEV-142 cost
floor, correctness requirements, privacy policy, original-result preservation,
or blocker rules.

## Codex capability gate

Current official Codex documentation establishes that:

- a plugin can bundle lifecycle hooks at `hooks/hooks.json` or through the
  `.codex-plugin/plugin.json` `hooks` entry;
- plugin hook paths are relative to and contained by the installed plugin root;
- installed or enabled plugin hooks require explicit trust before execution;
- `PostToolUse` can observe shell and unified-exec completion as canonical
  `Bash`; and
- `PostToolUse` output is documented as feedback and control fields, not as a
  byte-for-byte replacement or suppression contract for the original tool
  result.

DEV-246 therefore owns an exact-host capability probe before any production
implementation begins. The probe must use the captured Codex CLI `0.145.0`
executable and prove whether the plugin hook can prevent the original eligible
tool result from entering the next parent-model request while supplying the
validated compact result.

If the captured host cannot do this, DEV-246 records `blocked` with normalized
evidence and the conditional downstream issues are canceled. Feedback-only
output, an additional parent turn, transcript mutation, an MCP/model-selected
detour, or sending both the original and condensed result does not satisfy the
product outcome and must not be adopted as a fallback. Any alternative
interface or task-boundary change returns to Sol and the user for a new
architecture decision.

For exact Codex CLI `0.145.0`, an official-manual statement that `PostToolUse`
`suppressOutput` is parsed but not implemented or supported is sufficient to
record `blocked:host_replacement_unavailable` before authentication or live
execution. The project must not copy a credential or run an unsupported effect
merely to reproduce the documented limitation.

The DEV-246 executable is intentionally exact-version. If the frozen
`0.145.0` manual no longer contains both unsupported-effect statements, the
row fails as `official_manual_contract_drift` and returns to Sol/user. It does
not infer or exercise a new trust, task, or boundary interface without a
refreshed architecture.

The manual-only blocker is valid only for pinned official-manual SHA-256
`6cff0c5701d5a8b10ae497b5dda6ee70f478518d4fa029558168ee2bcc18918b`.
Caller-supplied bytes with another digest fail as
`official_manual_hash_mismatch`.

## Terminal capability decision — 2026-07-24

DEV-246 verified the pinned manual and recorded
`blocked:host_replacement_unavailable`. Codex CLI `0.145.0` parses
`PostToolUse.suppressOutput` but does not implement or support that effect.
The probe therefore stopped before authentication, installation, trust, or a
model task.

DEV-143, DEV-144, DEV-139, DEV-140, and DEV-141 are canceled rather than
advertised as implementation-ready. Their conditional plans are intentionally
not published. Resumption requires a later owner-approved Codex baseline whose
official contract supports model-visible replacement, followed by a new
brainstorming decision, refreshed spec, and Sol-authored plans.

## Closed responsibility boundaries

### DEV-246: Codex capability discovery boundary

DEV-246 owns only the synthetic, exact-host experiment that determines whether
Codex CLI `0.145.0` exposes a trusted `PostToolUse` contract capable of replacing
or suppressing the original tool result before the next parent-model request.
It freezes the observed input/output schema, captures normalized evidence, and
returns `pass`, `blocked`, or `fail`.

It does not add production runtime code, invoke Apple Foundation Models, mutate
real transcripts, claim capability from model prose, or choose an alternative
architecture.

### DEV-133: separate deferred validation debt

DEV-133 remains `In Review` outside the runtime blocker chain. Its repository
guidance implementation is already merged and has an existing issue plan at
`docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md`.
Its deferred Claude semantic and missing-tool validation debt remains truthful;
this Codex runtime amendment neither completes nor expands it.

## Verification plan

Every implementation plan must include focused RED/GREEN tests plus the
repository gates that apply to its merged tree. The common deterministic gates
are:

```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

DEV-246 additionally requires exact Codex `0.145.0` executable capture, pinned
official-manual provenance, hash-bound synthetic plugin identity, and normalized
`pass`, `blocked`, or `fail` output. When the pinned manual records unsupported
`PostToolUse` suppression, the terminal manual-only blocker stops before
authentication, installation, trust, or a model task.

Missing prerequisites are blockers, never passes. Compile-only, mock-only,
structural, version, or file-presence evidence cannot substitute for live
runtime or model-visible replacement proof.

The canceled downstream work has no approved implementation interface,
acceptance gate, or execution order. A future baseline may resume it only
through the new decision process recorded in the terminal capability decision.
