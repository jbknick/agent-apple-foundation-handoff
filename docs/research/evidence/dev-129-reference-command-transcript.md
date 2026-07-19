# DEV-129 pinned production-reference command transcript

Structural reference evidence was collected on 2026-07-17 (Asia/Jerusalem);
installed-host workflow observations were refreshed on 2026-07-19. Repository
paths below are pinned links. Temporary checkout and host-home paths are normalized as
`<reference-root>`, `<claude-home>`, and `<codex-home>`.

## Scope and classifications

This transcript records structural evidence for comparing Claude Code and
Codex plugin repositories. The five references are production-structure
inputs only; they are not sources for Apple API truth.

The classifications used by the comparison are:

- **Adopt:** the observed pattern can retain its meaning in this fork.
- **Adapt:** the principle is useful, but its paths, generation direction,
  metadata richness, or host workflow must change.
- **Reject:** the pattern would introduce duplication, stale behavior,
  unnecessary runtime surface, or an unsupported success claim.

The initial absence gate passed:

```text
$ test ! -e docs/research/evidence/dev-129-reference-command-transcript.md
exit 0
```

Every checkout was a fresh network clone followed by a detached checkout of
the specified commit. No reference was patched. The only generator that wrote
inside a reference checkout was Zeabur's own sync command, followed by its
required clean-diff gate.

## Pinned revisions

The following `git -C <reference-root>/<name> rev-parse HEAD` commands all
exited `0`:

| Reference | Detached revision |
| --- | --- |
| [`duyet/codex-claude-plugins`](https://github.com/duyet/codex-claude-plugins/tree/82de4021a311034a9596e891baf3a8266fb33bf7) | `82de4021a311034a9596e891baf3a8266fb33bf7` |
| [`zeabur/agent-skills`](https://github.com/zeabur/agent-skills/tree/30da8243ef23470be79e02bac50a7e1dee1af12e) | `30da8243ef23470be79e02bac50a7e1dee1af12e` |
| [`baleen37/bstack`](https://github.com/baleen37/bstack/tree/34a04e16b8582d9ddc605563fea1f868732cca4e) | `34a04e16b8582d9ddc605563fea1f868732cca4e` |
| [`openai/plugins`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9) | `11c74d6ba24d3a6d48f54a194cd00ef3beea18f9` |
| [`openai/codex`](https://github.com/openai/codex/tree/693b8c2ba4396772eeb82ce2982acad19dd960f5) | `693b8c2ba4396772eeb82ce2982acad19dd960f5` |

The 2026-07-19 host refresh used Claude Code `2.1.140` and Codex CLI
`0.144.5` for workflow observations.

## Exact structural path evidence

All paths in this section passed `test -e` where described as present. Root
and nested guidance inventories came from `find` and `git ls-tree -r
--name-only HEAD`, so an absence below is an absence from the pinned tracked
tree rather than an assumption.

### Repository guidance

| Reference | Pinned paths and observed structure | Structural reading |
| --- | --- | --- |
| Duyet | Root [`CLAUDE.md`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/CLAUDE.md) plus nested `CLAUDE.md` files under plugins such as [`commit/CLAUDE.md`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/commit/CLAUDE.md). No tracked root `AGENTS.md`; the only tracked `AGENTS.md` is a skill template at [`kb/skills/init/templates/AGENTS.md`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/kb/skills/init/templates/AGENTS.md). | Claude-oriented root and nested guidance, not a demonstrated cross-host root-adapter pattern. |
| Zeabur | Both root [`AGENTS.md`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/AGENTS.md) and root [`CLAUDE.md`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/CLAUDE.md) are full guidance documents. | Evidence that independent full host files are possible, but not evidence that they remain mechanically synchronized. Adapt to one provider-neutral source plus a thin or generated adapter. |
| bstack | Root [`CLAUDE.md`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/CLAUDE.md) calls itself provider-neutral and says provider-specific glue should be thin. There is no tracked root `AGENTS.md`. The only tracked `AGENTS.md` and second `CLAUDE.md` are templates inside [`plugins/me/skills/setup`](https://github.com/baleen37/bstack/tree/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills/setup). | Adopt the provider-neutral principle; adapt the incomplete root shape by supplying the required Codex adapter. |
| Official OpenAI | [`openai/codex/AGENTS.md`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/AGENTS.md) has a nested [`codex-rs/tui/src/bottom_pane/AGENTS.md`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/tui/src/bottom_pane/AGENTS.md). The `build-ios-apps` example has neither root guidance filename. | Confirms scoped `AGENTS.md` inheritance as a Codex repository convention, but does not establish this project's cross-host authoring direction. |

### Manifests, marketplaces, generation, and drift

- Duyet maintains a Claude marketplace at
  [`.claude-plugin/marketplace.json`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/.claude-plugin/marketplace.json),
  a Codex marketplace at
  [`.agents/plugins/marketplace.json`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/.agents/plugins/marketplace.json),
  and dual manifests such as
  [`build-ios-apps/.claude-plugin/plugin.json`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/build-ios-apps/.claude-plugin/plugin.json)
  and
  [`build-ios-apps/.codex-plugin/plugin.json`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/build-ios-apps/.codex-plugin/plugin.json).
  Its
  [`scripts/validate-plugins.sh`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/scripts/validate-plugins.sh)
  checks manifests, host-specific fields, selected cross-manifest parity, and
  marketplace paths; the pinned tree does not contain a generator for these
  catalogs. This is useful validation evidence, not a reason to adopt manual
  dual authoring.
- Zeabur's canonical skills are under
  [`skills/`](https://github.com/zeabur/agent-skills/tree/30da8243ef23470be79e02bac50a7e1dee1af12e/skills).
  [`scripts/sync-codex-plugin.mjs`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/scripts/sync-codex-plugin.mjs)
  deletes and rebuilds `plugins/zeabur`, physically copying all skills and the
  root Codex manifest. The drift workflow is
  [`.github/workflows/codex-plugin-sync.yml`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/.github/workflows/codex-plugin-sync.yml),
  and the generated marketplace is
  [`.agents/plugins/marketplace.json`](https://github.com/zeabur/agent-skills/blob/30da8243ef23470be79e02bac50a7e1dee1af12e/.agents/plugins/marketplace.json).
  Adopt deterministic drift detection; reject full skill-tree mirroring for
  this fork unless a later pinned host test proves it necessary.
- bstack keeps Claude metadata at
  [`.claude-plugin/marketplace.json`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/.claude-plugin/marketplace.json)
  and
  [`plugins/me/.claude-plugin/plugin.json`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/.claude-plugin/plugin.json),
  generates the Codex
  [marketplace](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/.agents/plugins/marketplace.json)
  and
  [`plugins/me/.codex-plugin/plugin.json`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/.codex-plugin/plugin.json),
  and leaves the physical
  [`plugins/me/skills`](https://github.com/baleen37/bstack/tree/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills)
  tree shared. Exact generators are
  [`generate-codex-plugin-manifests.sh`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/generate-codex-plugin-manifests.sh),
  [`generate-codex-marketplace.sh`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/generate-codex-marketplace.sh),
  and
  [`sync-codex-artifacts.sh`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/sync-codex-artifacts.sh);
  the drift gate is
  [`check-codex-artifacts.sh`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/scripts/check-codex-artifacts.sh).
  Adopt its shared physical tree and generation direction; adapt the output to
  the current rich Codex schema. For this fork, the precise canonical inputs
  are the Claude manifest's shared identity fields plus a separate authored
  generator input for Codex-only plugin `interface` data, including
  `plugin.json.interface.category`, and marketplace source/order plus the
  distinct `plugins[].policy` and `plugins[].category` entry fields. The
  generator owns explicit Codex manifest and marketplace outputs, which must
  not be hand-edited.
- The official Codex example uses a rich
  [`.codex-plugin/plugin.json`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/.codex-plugin/plugin.json)
  with paths and detailed `interface` fields. Current
  [OpenAI build documentation](https://developers.openai.com/codex/plugins/build)
  calls `.codex-plugin/plugin.json` the required entry point and says the other
  manifest fields are optional. In contrast, the pinned
  [`validate_plugin.py`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/skills/src/assets/samples/plugin-creator/scripts/validate_plugin.py)
  enforces a stricter plugin-creation policy: shared identity fields and a
  complete `interface`, including `longDescription`, `category`,
  `capabilities`, and `defaultPrompt`. This project can adopt the stricter
  validator without mislabeling all rich fields as loader-level requirements.
  Marketplace-entry `plugins[].policy` and `plugins[].category` belong only in
  `marketplace.json`. The similarly named but distinct
  `plugin.json.interface.category` belongs to the Codex presentation input and
  is required by the pinned validator. The example's
  [`agents/openai.yaml`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/agents/openai.yaml)
  contains plugin-presentation-like fields, but the pinned validator neither
  defines nor validates that root file as the current contract. It does
  validate per-skill `skills/<skill>/agents/openai.yaml` files as skill UI and
  activation metadata, for example
  [`ios-simulator-browser/agents/openai.yaml`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-simulator-browser/agents/openai.yaml).
  Plugin presentation belongs in `plugin.json.interface`; neither YAML file is
  a plugin-local worker definition. The pinned format reference is
  [`plugin-json-spec.md`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md).

### Loader and marketplace compatibility

- [`plugin_namespace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/utils/plugins/src/plugin_namespace.rs)
  recognizes manifests in this order: `.codex-plugin/plugin.json`,
  `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`.
- [`marketplace.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/marketplace.rs)
  checks marketplaces in this full order:
  `.agents/plugins/marketplace.json`,
  `.agents/plugins/api_marketplace.json`,
  `.claude-plugin/marketplace.json`, then
  `.cursor-plugin/marketplace.json`. Its local-source resolver explicitly
  accepts `.` and `./` as the marketplace root. The pinned source proves that
  support at revision `693b8c2`; it does not establish when it was introduced.
- [`loader.rs`](https://github.com/openai/codex/blob/693b8c2ba4396772eeb82ce2982acad19dd960f5/codex-rs/core-plugins/src/loader.rs)
  defines default paths for `skills/`, `hooks/hooks.json`, `.mcp.json`, and
  `.app.json` when capabilities are not explicitly redirected.

This compatibility evidence describes the pinned Codex runtime. It does not
replace explicit production Codex metadata or approve optional hooks, MCP
servers, apps, or other runtime surface for the original DEV-136
guidance/catalog slice. The later Linear approval for DEV-142–DEV-145 runtime
work is separate evidence and must reverify current official Codex and Claude
plugin/hook contracts. This transcript's pinned references remain structural
patterns, not current runtime-contract or Apple API authority. It also leaves
the final repository-root versus `plugins/<name>` production location open for
DEV-132.

### Claude cache and symlink rules

Anthropic's [official plugin reference](https://code.claude.com/docs/en/plugins-reference#share-files-within-a-marketplace-with-symlinks)
documents rules narrower than a blanket symlink rejection:

- a marketplace install preserves a relative symlink whose target is inside
  the plugin directory;
- a marketplace install dereferences a target elsewhere inside the same
  marketplace and copies the target content into the plugin cache;
- a marketplace install skips a target outside the marketplace;
- `--plugin-dir` and local-path loads preserve only targets inside the plugin
  directory and skip all other symlinks; and
- ordinary path traversal such as `../shared-utils` does not work after
  installation because files outside the plugin are not copied.

The one-physical-tree design must be evaluated against the exact loading mode;
the evidence does not require rejecting all symlinks, and it does not approve
an adapter that resolves outside its packaged boundary.

### Narrow skills and progressive disclosure

- Official workflow skills use concise `what + when` descriptions, for
  example
  [`ios-app-intents/SKILL.md`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-app-intents/SKILL.md),
  with dense material in its
  [`references/`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-app-intents/references),
  while
  [`ios-simulator-browser`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-ios-apps/skills/ios-simulator-browser)
  owns executable helpers under `scripts/`.
- Zeabur uses narrow `skills/zeabur-*` entries and moves dense template
  material to
  [`skills/zeabur-template/references`](https://github.com/zeabur/agent-skills/tree/30da8243ef23470be79e02bac50a7e1dee1af12e/skills/zeabur-template/references).
- bstack uses workflow skills such as
  [`plugins/me/skills/research/SKILL.md`](https://github.com/baleen37/bstack/blob/34a04e16b8582d9ddc605563fea1f868732cca4e/plugins/me/skills/research/SKILL.md).
- Duyet uses a thin Codex workflow wrapper at
  [`commit/skills/commit-workflow/SKILL.md`](https://github.com/duyet/codex-claude-plugins/blob/82de4021a311034a9596e891baf3a8266fb33bf7/commit/skills/commit-workflow/SKILL.md).

Together these support adopting several narrow workflow skills and progressive
disclosure, while keeping wrappers thin and only for real host invocation
differences.

## Reference-native validation

The planned commands were run unchanged against the detached checkouts:

| Command | Normalized result |
| --- | --- |
| `bash <reference-root>/duyet/scripts/validate-plugins.sh` | PASS: `Checked 49 item(s). 0 failed.` |
| `git -C <reference-root>/zeabur diff --quiet` | PASS before generation. |
| `node <reference-root>/zeabur/scripts/sync-codex-plugin.mjs` | PASS: generated `plugins/zeabur` from root skills and manifest. |
| `git -C <reference-root>/zeabur diff --exit-code -- plugins/zeabur .agents/plugins/marketplace.json` | PASS: no drift, exit `0`. |
| `bash <reference-root>/bstack/scripts/check-codex-artifacts.sh` | PASS: no drift, exit `0`. |
| `python3 <reference-root>/openai-codex/.../validate_plugin.py <reference-root>/openai-plugins/plugins/build-ios-apps` | PASS: `Plugin validation passed`, exit `0`. |

The Duyet validator covered 23 Claude manifests, 23 Codex manifests, one
Antigravity manifest, cross-manifest parity, and marketplaces: 49/49 checks
passed. No pinned-reference dependency blocker occurred.

The same pinned official validator was also reproduced against the two
third-party reference plugins. Both expected nonzero results are recorded as
current official-policy diagnostics, separately from their native validation
passes:

```text
$ python3 <reference-root>/openai-codex/.../validate_plugin.py \
    <reference-root>/bstack/plugins/me
Plugin validation failed:
- plugin.json field `interface` must be an object
exit 1

$ python3 <reference-root>/openai-codex/.../validate_plugin.py \
    <reference-root>/duyet/build-ios-apps
Plugin validation failed:
- plugin.json field `agents` is not accepted by plugin validation
- plugin.json field `interface.links` is not accepted by plugin validation
- plugin.json field `interface.longDescription` must be a non-empty string
- plugin.json field `interface.defaultPrompt` or `interface.default_prompt` is required
exit 1
```

Exact nonzero-status and diagnostic-content gates passed. These results show
why bstack's copy-plus-skills generator must be adapted and why Duyet's rich
manifest cannot be copied unchanged. They do not contradict the native 49/49
or no-drift results: those validators enforce different repository-local
contracts.

## Installed host workflow evidence

The 2026-07-19 installed Claude CLI refresh defines the behavior this project
can rely on. [Official documentation](https://code.claude.com/docs/en/plugins-reference)
provides context, but only behavior verified on the installed host is relied
on. The following selected refresh output was observed:

```text
$ claude --version
2.1.140 (Claude Code)

$ claude --help | rg -- '--plugin-dir'
--plugin-dir <path>  Load a plugin from a directory or .zip for this session only (repeatable: --plugin-dir A --plugin-dir B.zip) (default: [])

$ claude plugin --help
install ...
list ...
marketplace ...
validate [options] <path>  Validate a plugin or marketplace

$ claude plugin validate <reference-root>/bstack/plugins/me
Validation passed
```

All Claude gates exited `0`. Session-only `claude --plugin-dir <path>` is a
repeatable supported local-development workflow for installed Claude Code
`2.1.140`. Documentation alone is not treated as installed-host behavior
without verification on the current host.

Codex's installed CLI and the pinned OpenAI loader source establish a different
workflow:

```text
$ codex --version
codex-cli 0.144.5

$ codex plugin --help
add          Install a plugin from a configured marketplace snapshot
list         List plugins available from configured marketplace snapshots
marketplace  Add, list, upgrade, or remove configured plugin marketplaces
remove       Remove an installed plugin from local config and cache

$ codex plugin marketplace --help
add | list | upgrade | remove

$ codex --plugin-dir /tmp --help
error: unexpected argument '--plugin-dir' found
exit 2
```

The nonzero-status gate and exact `unexpected argument.*--plugin-dir` match
both passed. Therefore `codex --plugin-dir` is rejected by Codex `0.144.5`;
the representative local path is isolated marketplace registration followed
by install and inspection of the cached installed plugin.

## Isolated representative loading

Fresh disposable homes were created for both hosts, then the pinned bstack
root was used without modification. Paths in the selected output are
normalized:

```text
$ CLAUDE_CONFIG_DIR=<claude-home> claude plugin marketplace add <reference-root>/bstack --scope user
Successfully added marketplace: bstack
$ CLAUDE_CONFIG_DIR=<claude-home> claude plugin list --available --json | jq ...
{"pluginId":"me@bstack","version":"17.32.1"}
$ CLAUDE_CONFIG_DIR=<claude-home> claude plugin install me@bstack --scope user
Successfully installed plugin: me@bstack
$ CLAUDE_CONFIG_DIR=<claude-home> claude plugin list --json | jq ...
{"id":"me@bstack","version":"17.32.1","enabled":true,"installPath":"<claude-home>/plugins/cache/bstack/me/17.32.1"}

$ CODEX_HOME=<codex-home> codex plugin marketplace add <reference-root>/bstack --json | jq ...
{"marketplaceName":"bstack","installedRoot":"<reference-root>/bstack","alreadyAdded":false}
$ CODEX_HOME=<codex-home> codex plugin list --available --json | jq ...
{"pluginId":"me@bstack","version":"17.32.1","installed":false,"enabled":false}
$ CODEX_HOME=<codex-home> codex plugin add me@bstack --json | jq ...
{"pluginId":"me@bstack","installedPath":"<codex-home>/plugins/cache/bstack/me/17.32.1"}
$ CODEX_HOME=<codex-home> codex plugin list --json | jq ...
{"pluginId":"me@bstack","version":"17.32.1","installed":true,"enabled":true}
```

Every marketplace-add, available-list, install, and enabled-list command
exited `0`; each `jq -e` selector found exactly the required `me@bstack`
record. These are reproducible structural load gates and use no project
credentials or paid provider.

## Claims this evidence does not establish

- This evidence does not establish capability E2E in either host. No model
  session activated a skill, loaded a progressive reference, or demonstrated
  domain output behavior.
- Validation, marketplace discovery, installation, cache contents, and an
  enabled flag do not prove that a model will select or correctly follow a
  skill. Real Claude and Codex task invocations remain a DEV-139 gate.
- The pinned Codex loader's Claude-compatible fallbacks do not establish that
  Claude-only metadata is the forward production contract. The selected
  direction remains explicit generated Codex artifacts over one shared
  physical skill/reference tree, using Claude shared identity and a separate
  Codex-only presentation/marketplace input. DEV-132 still owns the final root
  versus `plugins/<name>` location.
- Root `.`/`./` marketplace-source support at the pinned Codex revision does
  not establish when the behavior was introduced or guarantee it in another
  host version.
- Per-skill `agents/openai.yaml` is skill UI/activation metadata, not a custom
  worker. The root file in the pinned reference is not validated as the current
  contract and does not establish a second presentation source; plugin
  presentation belongs in `plugin.json.interface`.
- The current OpenAI documentation's optional rich manifest fields and the
  pinned validator's stricter creation policy are different contract layers.
  Passing or failing one must not be reported as passing or failing the other.
- Claude documentation alone does not establish that a feature is available on
  the current host; version-sensitive behavior must be reverified after a host
  change.
- The presence of hooks, MCP, app, command, or agent loader surfaces did not
  approve those capabilities for the original DEV-136 guidance/catalog slice.
  The later Linear approval for DEV-142–DEV-145 runtime work is separate
  evidence and requires current official Codex and Claude plugin/hook-contract
  verification.
- None of the five repositories establishes Apple Foundation Models API
  correctness, security semantics, SDK availability, or runtime behavior.
- No network-dependent check in this research transcript is proposed as a
  default repository test. Missing host binaries, credentials, SDKs, or
  hardware in later issues must be reported as blockers rather than converted
  into false passes.
