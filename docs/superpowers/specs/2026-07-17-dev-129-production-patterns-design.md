# DEV-129 Production Plugin Pattern Comparison Design

Issue: [DEV-129](https://linear.app/devprentice/issue/DEV-129/r3parallel-compare-production-claude-codecodex-plugin-and-skill)

Evidence collection range: `2026-07-16` through `2026-07-17`

## Purpose

DEV-129 determines which structural patterns from production Claude Code and
Codex plugin repositories fit this authoritative fork. The references inform
packaging, generation, progressive disclosure, guidance, and local-development
workflows. They are never Apple API authority.

This issue creates research documentation only. It does not add plugin
metadata, skills, agents, guidance adapters, generators, dependencies, or
runtime code.

## Pinned references

Evidence is tied to these immutable revisions:

- `duyet/codex-claude-plugins@82de4021a311034a9596e891baf3a8266fb33bf7`
- `zeabur/agent-skills@30da8243ef23470be79e02bac50a7e1dee1af12e`
- `baleen37/bstack@34a04e16b8582d9ddc605563fea1f868732cca4e`
- `openai/plugins@11c74d6ba24d3a6d48f54a194cd00ef3beea18f9`
- `openai/codex@693b8c2ba4396772eeb82ce2982acad19dd960f5`

Installed host observations use Claude Code `2.1.91` and Codex CLI `0.144.5`.
Version-sensitive conclusions must be revalidated when either host changes.

## Selected structural model

The selected direction is one physical canonical skill/reference/script tree
with host metadata generated where the host contracts differ.

- Claude metadata is a practical canonical input for shared core fields.
- Codex metadata must be generated into the current rich production shape,
  including interface/policy/path requirements, rather than merely copying a
  Claude manifest and appending a skills path.
- Generated Codex artifacts never own or duplicate the skill corpus.
- Deterministic generation and drift checks must validate field parity,
  ordering, paths, schema/interface requirements, and untracked generated
  files.

Current Codex loader compatibility with Claude-only metadata is evidence about
the pinned runtime, not the forward production packaging contract. The project
will keep explicit Codex artifacts.

## Skill and reference topology

Use several narrow workflow entry skills with concise `what + when`
descriptions. Dense domain knowledge belongs in owning references and scripts,
loaded through progressive disclosure. A shared conceptual core can be
referenced by design, implement, review, debug, and validate workflows.

Reject both a giant catch-all skill and provider-specific copies of the same
domain workflow. Thin wrappers are justified only when the host invocation
surface genuinely differs.

No plugin-local agent is approved by default. Official `agents/openai.yaml` is
presentation and activation metadata, not proof that a custom worker is
required. A future issue may add a custom agent only for a separately approved
role with distinct context, tools, and responsibilities.

## Repository guidance topology

Keep one provider-neutral guidance source. Root `AGENTS.md` should be a thin or
generated Codex adapter rather than an independently maintained full copy.
Do not rely on an absent adapter, and do not use an external-resolving symlink
as the packaged compatibility mechanism.

## Host-local workflows

Claude Code supports:

- `claude plugin validate <path>` for structural validation;
- session-only `claude --plugin-dir <path>` loading; and
- isolated marketplace/install workflows when packaging is under test.

Codex `0.144.5` does not support `codex --plugin-dir`. Its isolated local
workflow is:

1. set a disposable `CODEX_HOME`;
2. add a local marketplace root;
3. install the named plugin into the cache;
4. inspect discovery/enabled state; and
5. start a fresh real task that observes skill activation and behavior.

Validation, installation, cache contents, and discovery are structural gates
only. Capability E2E requires a real model session in both hosts and remains a
DEV-139 responsibility.

## Adopt, adapt, and reject framework

The comparison artifact classifies each candidate as:

- **Adopt** when the pattern fits the fork without changing its meaning;
- **Adapt** when the principle fits but paths, generation direction, metadata
  richness, or host workflow must change; or
- **Reject** when the pattern creates duplication, stale behavior, unnecessary
  runtime surface, or unsupported success claims.

Every classification must cite an exact pinned path and give both rationale
and downstream impact.

## Artifact and validation boundary

The issue adds:

- `docs/research/evidence/dev-129-reference-command-transcript.md`; and
- `docs/research/dev-129-production-pattern-comparison.md`.

Together with this design and its implementation plan, the stacked delta must
contain exactly four DEV-129 documentation files.

Completion requires pinned identities, exact reference paths, practical
validator/generator/drift results, isolated host-loading evidence, explicit
non-claims, an adopt/adapt/reject matrix, downstream decisions, task reviews,
whole-branch review, and fresh exact-head verification. Network is allowed for
research clone/link checks, but no default future test may depend on it.

The ready PR must target the DEV-128 branch and remain unmerged.
