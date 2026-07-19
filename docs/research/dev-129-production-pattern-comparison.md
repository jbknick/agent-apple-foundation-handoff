# DEV-129 production Claude Code/Codex pattern comparison

Structural reference evidence was collected on 2026-07-17 (Asia/Jerusalem);
installed-host workflow observations were refreshed on 2026-07-19. The
reproducible command evidence for this comparison is the
[pinned reference transcript](evidence/dev-129-reference-command-transcript.md).

## Scope and authority

This report selects structural patterns for the authoritative
`agent-apple-foundation-handoff` fork. It compares packaging, metadata,
guidance, skill topology, progressive disclosure, validation, and local host
workflows. It does not select Apple Foundation Models APIs, privacy semantics,
or runtime behavior.

The five reference revisions below are immutable structural evidence. Apple
API truth must instead come from current official Apple documentation,
installed SDK interfaces, WWDC material, and Apple-owned repositories. A
reference repository's production use, validator pass, or host discovery does
not elevate its domain prose to Apple authority.

The decision vocabulary is:

- **Adopt:** preserve the observed pattern and its meaning.
- **Adapt:** preserve the useful principle while changing paths, metadata,
  generation direction, or host workflow for this fork.
- **Reject:** exclude a pattern that would create duplication, drift,
  unsupported surface, or a false capability claim.

This issue is research-only. It approves no plugin files, skills, agents,
hooks, MCP servers, commands, dependencies, or runtime packages.

**Scope amendment (2026-07-18):** That exclusion, including the earlier
no-worker/no-hook decision, is binding only for the original DEV-136
guidance/catalog slice; it is not a project-wide rejection of runtime work.
The separately approved runtime chain is DEV-142 contract, DEV-143 Apple
bridge, DEV-144 Codex PostToolUse adapter, DEV-145 Claude PostToolUse adapter,
then DEV-139 E2E. This research neither designs nor approves that chain. Each
later runtime issue must reverify the current official Codex and Claude
plugin/hook contracts; these pinned structural references are patterns, not
current runtime-contract or Apple API authority.

## Pinned reference matrix

| Reference | Revision | Exact structural evidence used | Role in this comparison |
| --- | --- | --- | --- |
| Duyet `codex-claude-plugins` | [`82de4021a311034a9596e891baf3a8266fb33bf7`](https://github.com/duyet/codex-claude-plugins/tree/82de4021a311034a9596e891baf3a8266fb33bf7) | [Claude marketplace](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/.claude-plugin/marketplace.json), [Codex marketplace](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/.agents/plugins/marketplace.json), [`build-ios-apps` Codex manifest](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/build-ios-apps/.codex-plugin/plugin.json), and [`scripts/validate-plugins.sh`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/scripts/validate-plugins.sh) | Direct dual-manifest/catalog validation and thin workflow-wrapper evidence. |
| Zeabur `agent-skills` | [`30da8243ef23470be79e02bac50a7e1dee1af12e`](https://github.com/zeabur/agent-skills/tree/30da8243ef23470be79e02bac50a7e1dee1af12e) | Canonical [`skills/`](https://github.com/zeabur/agent-skills/tree/30da8243ef23470be79e02bac50a7e1dee1af12e/skills), [`scripts/sync-codex-plugin.mjs`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/scripts/sync-codex-plugin.mjs), and [drift workflow](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/.github/workflows/codex-plugin-sync.yml) | Deterministic regeneration/drift evidence, plus a counterexample that physically mirrors the full skill tree. |
| `baleen37/bstack` | [`34a04e16b8582d9ddc605563fea1f868732cca4e`](https://github.com/baleen37/bstack/tree/34a04e16b8582d9ddc605563fea1f868732cca4e) | Shared [`plugins/me/skills`](https://github.com/baleen37/bstack/tree/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills), [Claude manifest](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/.claude-plugin/plugin.json), [`generate-codex-plugin-manifests.sh`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/generate-codex-plugin-manifests.sh), and [`check-codex-artifacts.sh`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/check-codex-artifacts.sh) | One physical skill tree and Claude-to-Codex generation direction. This fork, not upstream, remains authoritative. |
| OpenAI `plugins` | [`11c74d6ba24d3a6d48f54a194cd00ef3beea18f9`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9) | [`build-ios-apps/.codex-plugin/plugin.json`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/.codex-plugin/plugin.json), [`ios-app-intents/SKILL.md`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-app-intents/SKILL.md), its [`references/`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-app-intents/references), and per-skill [`agents/openai.yaml`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-simulator-browser/agents/openai.yaml) | Rich Codex presentation and official narrow-skill/progressive-disclosure examples. |
| OpenAI `codex` | [`693b8c2ba4396772eeb82ce2982acad19dd960f5`](https://github.com/openai/codex/tree/693b8c2ba4396772eeb82ce2982acad19dd960f5) | [`validate_plugin.py`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/skills/src/assets/samples/plugin-creator/scripts/validate_plugin.py), [`plugin_namespace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/utils/plugins/src/plugin_namespace.rs), [`marketplace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/marketplace.rs), and [`loader.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/loader.rs) | Pinned validation policy, manifest/marketplace recognition order, root-source handling, and optional capability defaults. |

Host-local observations are additionally pinned to installed Claude Code
`2.1.140` and Codex CLI `0.144.5` as refreshed on 2026-07-19. Current web
documentation can be newer than
those binaries, so a feature used by this project must pass an installed-host
test rather than relying only on prose.

## Repository guidance comparison

Duyet's pinned root
[`CLAUDE.md`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/CLAUDE.md)
and nested files are Claude-oriented; its only tracked `AGENTS.md` is a
[`kb/skills/init/templates/AGENTS.md`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/kb/skills/init/templates/AGENTS.md)
template. Zeabur independently maintains full root
[`AGENTS.md`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/AGENTS.md)
and
[`CLAUDE.md`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/CLAUDE.md)
documents without a demonstrated parity generator. Neither shape should be
copied directly.

The useful bstack principle is stated in its root
[`CLAUDE.md`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/CLAUDE.md):
keep provider-neutral guidance central and host glue thin. The pinned tracked
tree does not contain a root `AGENTS.md`; its only `AGENTS.md` and second
`CLAUDE.md` are under
[`plugins/me/skills/setup`](https://github.com/baleen37/bstack/tree/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills/setup).
Therefore this fork must adapt the principle by supplying a thin or generated
root `AGENTS.md`, not cite an adapter that is absent from the reference.

Claude cache behavior constrains how a shared guidance source can be exposed.
For marketplace installation, a relative symlink targeting inside the plugin
is preserved, a target elsewhere inside the same marketplace is dereferenced
and copied, and a target outside the marketplace is skipped. For
`--plugin-dir` and local-path loading, only a target inside the plugin is
preserved; all other symlinks are skipped. Ordinary `../` traversal outside
the installed plugin is not available. DEV-133 must select a thin/generated
adapter that stays valid under the production packaging path chosen by
DEV-132 and must test the relevant cache mode.

## Canonical and generated metadata comparison

The selected model has one shared-identity input, two distinct Codex-only
generator input domains, and one generated-output boundary:

1. Claude metadata owns only shared identity: name, version, description,
   author, project links, license, and keywords.
2. A generator-owned Codex presentation input owns the required
   `plugin.json.interface.category` plus the remaining rich `interface`
   fields.
3. A distinct generator-owned Codex marketplace input owns source path,
   stable entry ordering, and marketplace-entry `plugins[].policy` and
   `plugins[].category`. DEV-132 may colocate the two Codex-only domains in one
   authored source file, but their schema layers and ownership must remain
   separate.
4. The generator combines those inputs into explicit `.codex-plugin/plugin.json`
   and `.agents/plugins/marketplace.json` outputs. Generated Codex files are
   never hand-edited and never own or duplicate the skill corpus.

The similarly named category fields are not interchangeable.
`plugin.json.interface.category` is a Codex plugin-presentation field and is
required by the pinned
[`validate_plugin.py`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/skills/src/assets/samples/plugin-creator/scripts/validate_plugin.py).
The separate `plugins[].category` and `plugins[].policy` fields belong only to
the marketplace entry, as demonstrated by the official
[`.agents/plugins/marketplace.json`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/.agents/plugins/marketplace.json).
DEV-132 must define the concrete authored-input paths and field mapping without
collapsing these schema layers.

Current OpenAI build documentation identifies `.codex-plugin/plugin.json` as
the required entry point and describes other rich manifest fields as
optional. The pinned official validator applies a stricter creation policy:
shared identity plus a complete `interface` containing a non-empty long
description, presentation category, capabilities, and default prompt. This
project will satisfy that stricter validator while attributing the rule to the
validator rather than misreporting every rich field as a loader-level
requirement. The pinned validator passes the official `build-ios-apps`
example, while its expected failures for bstack and Duyet coexist with those
repositories' native validation passes because the policies are different.

Pinned Codex manifest recognition in
[`plugin_namespace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/utils/plugins/src/plugin_namespace.rs)
is `.codex-plugin/plugin.json`, then `.claude-plugin/plugin.json`, then
`.cursor-plugin/plugin.json`. Marketplace recognition in
[`marketplace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/marketplace.rs)
is `.agents/plugins/marketplace.json`,
`.agents/plugins/api_marketplace.json`,
`.claude-plugin/marketplace.json`, then
`.cursor-plugin/marketplace.json`. That pinned runtime also accepts local
marketplace sources `.` and `./`; use `./` if root placement is selected, but
do not claim when support began. Repository-root `./` versus conventional
`plugins/<name>` placement remains an explicit DEV-132 decision.

Current legacy loader compatibility with Claude metadata does not replace
explicit production Codex artifacts. It is a compatibility observation for
the pinned runtime, not the forward authoring contract.

## Skills and progressive disclosure comparison

The official
[`ios-app-intents/SKILL.md`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-app-intents/SKILL.md)
uses a concise activation description while moving domain detail into its
[`references/`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-app-intents/references).
The official
[`ios-simulator-browser`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-simulator-browser)
skill likewise owns executable helpers under `scripts/`. Zeabur's
[`skills/zeabur-template/references`](https://github.com/zeabur/agent-skills/tree/30da8243ef23470be79e02bac50a7e1dee1af12e/skills/zeabur-template/references)
and bstack's
[`plugins/me/skills/research/SKILL.md`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills/research/SKILL.md)
corroborate the narrow-entry/progressive-disclosure topology.

DEV-134 should therefore define several narrow workflow skills for design,
implementation, review, debugging, and validation. Each entry description
must say both what the skill does and when it applies. Dense Foundation Models
knowledge belongs in owning references and scripts, with a shared conceptual
core referenced rather than copied. Reject one giant catch-all skill,
provider-specific duplicates, and full skill-tree mirroring into generated
Codex paths.

One physical skill/reference/script tree remains the production source. The
bstack
[`plugins/me/skills`](https://github.com/baleen37/bstack/tree/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills)
layout proves the structural principle; the final path is owned by DEV-132.
Zeabur's
[`scripts/sync-codex-plugin.mjs`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/scripts/sync-codex-plugin.mjs)
is useful drift evidence but its physical copy of all skills is not selected.

## Agents, wrappers, and optional surfaces

No plugin-local agent is approved by default. The pinned official validator
defines per-skill `skills/<skill>/agents/openai.yaml` as skill UI and
activation metadata, exemplified by
[`skills/ios-simulator-browser/agents/openai.yaml`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-simulator-browser/agents/openai.yaml).
It is not a worker definition. Plugin-level presentation belongs in
`plugin.json.interface`. The official example's root
[`agents/openai.yaml`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/agents/openai.yaml)
is not defined or validated by the pinned validator as the current per-skill
contract and must not become a second canonical presentation source.

A thin wrapper is acceptable only when a host has a real invocation
difference, as illustrated by Duyet's
[`commit/skills/commit-workflow/SKILL.md`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/commit/skills/commit-workflow/SKILL.md).
Wrappers must not duplicate the domain workflow.

Pinned Codex
[`loader.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/loader.rs)
contains default surfaces for skills, hooks, MCP, and apps. Recognition does
not equal product approval. Hooks, MCP servers, commands, apps, agents,
dependencies, and runtime packages remain rejected unless a separately
approved issue defines a need, contract, test, and ownership boundary.

## Host-local workflow comparison

The 2026-07-19 refresh of installed Claude Code `2.1.140` supports
`claude plugin validate <path>` and session-only repeatable
`claude --plugin-dir <path>`. When packaging/cache semantics are under test,
it also supports an isolated `CLAUDE_CONFIG_DIR`, local marketplace
registration, install, and enabled-state inspection. The pinned bstack plugin
passed those structural workflows.

Installed Codex CLI `0.144.5` rejects `codex --plugin-dir` with exit `2` and
`unexpected argument '--plugin-dir'`. Its local workflow is an isolated
`CODEX_HOME`, `codex plugin marketplace add <root>`, available-state
inspection, `codex plugin add <plugin>`, installed/enabled-state inspection,
and then a fresh real task for behavior. The pinned bstack plugin passed the
structural marketplace/install sequence.

These workflows are intentionally host-specific. DEV-135 owns scaffold-time
validation/install support, while DEV-139 must run real Claude and Codex model
sessions. Marketplace discovery, installation, cache contents, and enabled
flags are prerequisites, not capability E2E.

## Adopt, adapt, and reject matrix

| Candidate pattern | Decision | Exact pinned path(s) | Rationale | Downstream impact |
| --- | --- | --- | --- | --- |
| One physical skill/reference/script tree | **Adopt** | bstack [`plugins/me/skills`](https://github.com/baleen37/bstack/tree/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills) and [Codex manifest generator](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/generate-codex-plugin-manifests.sh) | Both hosts consume the same corpus; generated metadata does not own content. | DEV-132 fixes the path; DEV-134 owns the catalog; DEV-135 preserves the shared tree. |
| Several narrow workflow skills | **Adopt** | OpenAI [`ios-app-intents/SKILL.md`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-app-intents/SKILL.md) and bstack [`research/SKILL.md`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills/research/SKILL.md) | Concise `what + when` entries improve activation and keep workflows bounded. | DEV-134 defines design/implement/review/debug/validate activation and output contracts. |
| Progressive disclosure into owning references and scripts | **Adopt** | OpenAI [`ios-app-intents/references`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-app-intents/references) and [`ios-simulator-browser/scripts`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-simulator-browser/scripts) | Domain detail is loaded only when needed and remains owned once. | DEV-134 maps reference ownership; DEV-139 proves actual reference loading. |
| Claude shared identity plus generated rich Codex metadata | **Adapt** | bstack [Claude manifest](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/.claude-plugin/plugin.json), [generator](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/generate-codex-plugin-manifests.sh), and official [rich Codex manifest](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/.codex-plugin/plugin.json) | Claude owns only shared identity; distinct generator inputs own Codex `interface` presentation and marketplace source/order/policy/category; generated Codex outputs are not hand-edited. | DEV-132 specifies the input schemas; DEV-135 implements generator and outputs. |
| Deterministic generation and drift validation | **Adopt** | bstack [`check-codex-artifacts.sh`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/check-codex-artifacts.sh) and Zeabur [drift workflow](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/.github/workflows/codex-plugin-sync.yml) | Re-generation must detect parity, ordering, path, interface/schema, drift, and untracked-output failures. | DEV-135 builds repository gates; DEV-139 includes them in its evidence bundle. |
| Provider-neutral guidance plus thin/generated root `AGENTS.md` | **Adapt** | bstack root [`CLAUDE.md`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/CLAUDE.md), with only setup-template [`AGENTS.md`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills/setup/AGENTS.md) | Preserve one guidance source but supply the missing Codex adapter within packaging/cache boundaries. | DEV-133 selects adapter mechanics after DEV-132 fixes placement; DEV-139 exercises both hosts. |
| Host-specific local workflows | **Adapt** | Codex [`marketplace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/marketplace.rs) plus the [host transcript](evidence/dev-129-reference-command-transcript.md) | Claude supports session-only `--plugin-dir`; Codex `0.144.5` requires isolated marketplace/install. | DEV-135 exposes structural checks; DEV-139 invokes fresh real tasks. |
| Plugin-local agent by default | **Reject** | Per-skill [`agents/openai.yaml`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-simulator-browser/agents/openai.yaml) and pinned [`validate_plugin.py`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/skills/src/assets/samples/plugin-creator/scripts/validate_plugin.py) | Per-skill YAML is UI/activation metadata, not a worker. No distinct role/context/tool contract is approved for the DEV-136 guidance/catalog slice. | DEV-134 and DEV-135 add no worker; a separately approved runtime issue must define and reverify any host contract. |
| Independently hand-maintained dual manifests and catalogs | **Reject** | Duyet [Claude marketplace](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/.claude-plugin/marketplace.json), [Codex marketplace](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/.agents/plugins/marketplace.json), and [validator](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/scripts/validate-plugins.sh) | A parity validator cannot prevent every semantic edit from drifting; generation gives one ownership boundary. | DEV-132 records ownership; DEV-135 makes Codex artifacts generator-only. |
| Full skill-tree mirroring into generated Codex paths | **Reject** | Zeabur [`scripts/sync-codex-plugin.mjs`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/scripts/sync-codex-plugin.mjs) and generated [`plugins/zeabur`](https://github.com/zeabur/agent-skills/tree/30da8243ef23470be79e02bac50a7e1dee1af12e/plugins/zeabur) | Copying the corpus creates avoidable generated duplication; no pinned host evidence requires it here. | DEV-132 and DEV-135 keep generated directories metadata-only. |
| `codex --plugin-dir` as a local workflow | **Reject** | [Installed-host transcript](evidence/dev-129-reference-command-transcript.md) and Codex [`marketplace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/marketplace.rs) | Codex `0.144.5` rejects the flag; local marketplace registration/install is the verified substitute. | DEV-135 and DEV-139 must not use this flag for Codex. |
| Root `./` marketplace source | **Adapt** | Codex [`marketplace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/marketplace.rs) | The pinned runtime accepts `.` and `./`; use `./` if root placement wins, without claiming when support began. | DEV-132 chooses root versus `plugins/<name>`; DEV-135/DEV-139 test the selected path. |
| Unapproved hooks, MCP, apps, commands, dependencies, or runtime packages | **Reject** | Codex [`loader.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/loader.rs) | Loader recognition is not a product requirement, and DEV-129/DEV-136 approve no optional runtime surface. | DEV-132/DEV-134/DEV-135 keep their guidance/catalog scope bounded; the separately approved DEV-142–DEV-145 runtime chain must reverify current official host contracts before DEV-139 E2E. |
| Capability claims from validation, discovery, install, cache, or enabled state alone | **Reject** | Duyet [`validate-plugins.sh`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/scripts/validate-plugins.sh), bstack [`check-codex-artifacts.sh`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/check-codex-artifacts.sh), and [isolated host evidence](evidence/dev-129-reference-command-transcript.md) | Structural success does not prove activation, progressive reference loading, or output behavior. | DEV-139 requires reproducible capability E2E in real model sessions for both hosts. |

## Downstream decisions

| Issue | Binding inherited decisions |
| --- | --- |
| DEV-132 — architecture synthesis | Select repository-root `./` or `plugins/<name>` using all research; define concrete paths for Claude shared identity and separate Codex presentation/marketplace inputs; preserve distinct `plugin.json.interface.category`, `plugins[].category`, and `plugins[].policy`; make explicit generated Codex artifacts and one physical skill tree architectural invariants. |
| DEV-133 — repository guidance | Keep one provider-neutral source and a thin/generated root `AGENTS.md`; apply the precise Claude symlink/cache rules to the DEV-132 placement; do not maintain two full guidance documents or rely on an absent adapter. |
| DEV-134 — Agent Skill architecture | Define several narrow `what + when` workflow skills, owning references/scripts, and progressive disclosure; treat per-skill `agents/openai.yaml` only as UI/activation metadata; add no plugin-local worker by default. |
| DEV-135 — scaffolding and marketplace | Generate rich explicit Codex manifest/marketplace outputs from the two authored input layers; never hand-edit outputs or mirror skills; satisfy the pinned stricter validator; validate ordering, parity, schema, paths, drift, and untracked outputs; implement host-specific structural workflows. |
| DEV-142–DEV-145 — approved runtime chain | DEV-142 contract, DEV-143 Apple bridge, DEV-144 Codex PostToolUse adapter, and DEV-145 Claude PostToolUse adapter are separate approved runtime work, not an exception inferred from this guidance/catalog research. Reverify current official Codex and Claude plugin/hook contracts before implementation; pinned references remain structural patterns only. |
| DEV-139 — cross-host E2E | Treat validation/discovery/install as setup only; run fresh real Claude and Codex tasks that demonstrate skill activation, progressive reference loading, and expected output behavior; preserve explicit blockers for unavailable hosts, credentials, SDKs, or hardware. |

These inherited decisions include rationale and source issue DEV-129. Any
later change must update DEV-129 and every affected downstream issue before
implementation begins.

## Validation contract and non-claims

Completion evidence for this research is structural and reproducible:

- all five reference revisions are pinned and every conclusion cites an exact
  path;
- Duyet's native validator passed 49/49, Zeabur regeneration produced no
  drift, and bstack's generated-artifact drift check passed;
- the pinned official validator passed the official example and produced the
  recorded expected policy failures for bstack and Duyet, without conflating
  those failures with native validation;
- the 2026-07-19 installed-host refresh exercised Claude Code `2.1.140` and
  Codex `0.144.5` behavior in isolated homes; and
- generated Codex artifacts have an explicit non-editable ownership boundary,
  while the physical skills/references/scripts remain shared.

This evidence does not establish capability E2E. No model session in this
issue proved skill activation, progressive reference loading, or domain output
behavior. It does not establish Apple API truth, runtime availability,
security semantics, SDK support, or host behavior beyond the recorded
versions. It does not approve optional plugin surfaces, network-dependent
default tests, or credentials and paid services. A missing binary, SDK,
credential, network requirement, or hardware capability in a downstream issue
must be an explicit blocker, never a false pass.
