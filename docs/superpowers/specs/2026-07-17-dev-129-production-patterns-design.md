# DEV-129 Production Plugin Pattern Comparison Design

Issue: [DEV-129](https://linear.app/devprentice/issue/DEV-129/r3parallel-compare-production-claude-codecodex-plugin-and-skill)

Evidence collection range: `2026-07-16` through `2026-07-19` (structural
references through 2026-07-17; installed-host workflow refresh on 2026-07-19)

## Purpose

DEV-129 determines which structural patterns from production Claude Code and
Codex plugin repositories fit this authoritative fork. The references inform
packaging, generation, progressive disclosure, guidance, and local-development
workflows. They are never Apple API authority.

This issue creates research documentation only. It does not add plugin
metadata, skills, agents, guidance adapters, generators, dependencies, or
runtime code.

**Issue-boundary amendment (2026-07-18):** The earlier DEV-136 no-worker/no-
hook decision remains valid only for its original guidance/catalog scope; it is
not a project-wide runtime prohibition. DEV-142 contract, DEV-143 Apple bridge,
DEV-144 Codex PostToolUse adapter, DEV-145 Claude PostToolUse adapter, and
DEV-139 E2E are separate approved runtime work. This design does not specify
that runtime work; each later issue must reverify current official Codex and
Claude plugin/hook contracts, because pinned structural references are neither
current runtime-contract nor Apple API authority.

## Pinned references

Evidence is tied to these immutable revisions:

- `duyet/codex-claude-plugins@82de4021a311034a9596e891baf3a8266fb33bf7`
- `zeabur/agent-skills@30da8243ef23470be79e02bac50a7e1dee1af12e`
- `baleen37/bstack@34a04e16b8582d9ddc605563fea1f868732cca4e`
- `openai/plugins@11c74d6ba24d3a6d48f54a194cd00ef3beea18f9`
- `openai/codex@693b8c2ba4396772eeb82ce2982acad19dd960f5`

Installed-host workflow observations were refreshed on 2026-07-19 using Claude
Code `2.1.140` and Codex CLI `0.144.5`. Version-sensitive conclusions must be
revalidated when either host changes.

## Selected structural model

The selected direction is one physical canonical skill/reference/script tree
with host metadata generated where the host contracts differ.

- Claude metadata is the canonical input for shared identity fields such as
  name, version, description, author, project links, license, and keywords.
- A separate generator input owns Codex-only plugin `interface` presentation
  data, including `plugin.json.interface.category`, and Codex marketplace data,
  including entry ordering, source path, `plugins[].policy`, and
  `plugins[].category`. Marketplace `plugins[].policy` and
  `plugins[].category` exist only in `marketplace.json`; the distinct
  `plugin.json.interface.category` belongs to the Codex presentation input.
- The generator combines those two authored inputs into explicit Codex
  manifest and marketplace outputs. Generated outputs are never hand-edited.
- Generated Codex artifacts never own or duplicate the skill corpus.
- Deterministic generation and drift checks must validate field parity,
  ordering, paths, schema/interface requirements, and untracked generated
  files.

The current OpenAI build documentation identifies
`.codex-plugin/plugin.json` as the required entry point and describes its other
manifest fields as optional. The pinned official `validate_plugin.py` applies
a stricter creation policy: it requires shared identity fields and a complete
`interface`, including long description, presentation category, capabilities,
and a default prompt. This project will satisfy the pinned stricter validator
while recording that the requirement comes from the validator, not overstating
every rich field as a loader-level requirement.

Current Codex loader compatibility with Claude-only metadata is evidence about
the pinned runtime, not the forward production packaging contract. The project
will keep explicit Codex artifacts. The pinned loader explicitly accepts local
marketplace source `.` and `./`; this research does not claim when that support
was introduced. DEV-132 must choose the final repository-root versus
`plugins/<name>` production path using the complete research set.

## Skill and reference topology

Use several narrow workflow entry skills with concise `what + when`
descriptions. Dense domain knowledge belongs in owning references and scripts,
loaded through progressive disclosure. A shared conceptual core can be
referenced by design, implement, review, debug, and validate workflows.

Reject both a giant catch-all skill and provider-specific copies of the same
domain workflow. Thin wrappers are justified only when the host invocation
surface genuinely differs.

No plugin-local agent is approved by default. The pinned official validator
recognizes per-skill `skills/<skill>/agents/openai.yaml` as skill UI and
activation metadata. Plugin presentation belongs in the plugin manifest's
`interface` object. Although the pinned `build-ios-apps` reference also has a
root `agents/openai.yaml` containing presentation-like fields, the pinned
validator does not define or validate that root file as the current contract.
Neither file is proof that a custom worker is required. A future issue may add
a custom agent only for a separately approved role with distinct context,
tools, and responsibilities.

## Repository guidance topology

Keep one provider-neutral guidance source. Root `AGENTS.md` should be a thin or
generated Codex adapter rather than an independently maintained full copy.
Do not rely on an absent adapter. Apply Claude's precise cache rules instead of
a blanket symlink prohibition: marketplace installs preserve relative links
inside the plugin, dereference targets elsewhere inside the same marketplace,
and skip targets outside the marketplace; `--plugin-dir` and local-path loads
preserve only targets inside the plugin and skip all others. Ordinary `../`
path traversal outside an installed plugin does not work. The final adapter
must remain valid under the selected packaging workflow.

## Host-local workflows

The 2026-07-19 installed Claude Code `2.1.140` refresh directly demonstrates:

- `claude plugin validate <path>` for structural validation;
- session-only repeatable `claude --plugin-dir <path>` loading; and
- isolated marketplace/install workflows when packaging is under test.

Those installed observations are authoritative for features this project
relies on. Documentation alone is context, not a supported project assumption,
until the behavior is verified on the installed host; version-sensitive
conclusions are revalidated after an upgrade.

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

Together with this design and its implementation plan, the atomic delta must
contain exactly four DEV-129 documentation files.

Completion requires pinned identities, exact reference paths, practical
validator/generator/drift results, isolated host-loading evidence, explicit
non-claims, an adopt/adapt/reject matrix, downstream decisions, task reviews,
whole-branch review, and fresh exact-head verification. Network is allowed for
research clone/link checks, but no default future test may depend on it.

Sequential integration is against `origin/main`: exactly three main-agent
review/fix rounds must complete, the exact final reviewed remote head must be
recorded, the squash merge must be head-locked to it, and a merged-tree smoke
must pass before final Linear evidence/status is updated when the Definition of
Done holds.
