# DEV-127 Repository Architecture Audit

Audit date: `2026-07-16`

## Scope and authority

This report describes the repository at the authoritative fork revision
`7ec92734127236e29ab88d66c1b41f663149ce0e`. The DEV-127 documentation commits
made after that revision record the audit; they do not establish product or
plugin architecture that was absent from the audited tree. The complete command
evidence is linked in the
[DEV-127 command transcript](evidence/dev-127-command-transcript.md).

The current fork is authoritative. The pinned `baleen37/bstack` revision
`34a04e16b8582d9ddc605563fea1f868732cca4e` is **Reference only** and is not a
source of Apple API truth or evidence that the fork already has the upstream
architecture.

Claims in this report use four classes:

- **Established:** directly observed in the authoritative fork or installed
  host tools.
- **Reference only:** observed only in the pinned upstream checkout.
- **Not established:** not demonstrated by authoritative-fork evidence and
  reserved for an explicit downstream decision or additional proof.
- **Blocked:** a requested check could not run successfully on this host.

## Executive finding

**Established.** The audited revision tracks exactly three files:
`COMMERCIAL-LICENSE.md`, `LICENSE`, and `README.md`. These are the canonical
repository documents.

**Established.** The fork contains no generated artifacts and no adapter
artifacts. Consequently, the current canonical-versus-generated model has only
the three canonical documents; it does not yet define a generation boundary.

**Not established.** The following capabilities are not established in this
fork: plugin shape, repository runtimes, repository-native validation,
cross-host loading, and generation. Installed host tools and successful loading
of an upstream plugin do not fill those repository gaps.

**Reference only.** The upstream Claude-to-Codex generators and synchronization
checks demonstrate one possible production structure, not a structure adopted
by this fork.

**Blocked.** Full-Xcode validation could not run because the active developer
directory is the Command Line Tools installation rather than a full Xcode
installation.

## Authoritative tracked-file inventory

At `7ec92734127236e29ab88d66c1b41f663149ce0e`, `git ls-tree` returned exactly
the following inventory:

| Path | Classification | Basis |
| --- | --- | --- |
| `COMMERCIAL-LICENSE.md` | Canonical repository document | Tracked directly in the authoritative fork; no generator or generated-file declaration exists. |
| `LICENSE` | Canonical repository document | Tracked directly in the authoritative fork; no generator or generated-file declaration exists. |
| `README.md` | Canonical repository document | Tracked directly in the authoritative fork; no generator or generated-file declaration exists. |

**Established.** No `AGENTS.md`, `CLAUDE.md`, `package.json`, `.claude-plugin`,
`.codex-plugin`, `.agents`, `plugins`, `schemas`, `scripts`, `tests`, or
`.github/workflows` path exists at the audited revision. DEV-127's research and
planning documents are later audit artifacts and therefore are not evidence of
an earlier plugin implementation.

## Canonical, generated, and adapter classification

For this audit, a canonical artifact is an authoritative source maintained in
the fork, a generated artifact is reproducibly derived from a canonical source,
and an adapter artifact exposes canonical behavior through a host-specific
surface.

| Artifact class | Authoritative-fork members | Finding |
| --- | --- | --- |
| Canonical | `COMMERCIAL-LICENSE.md`, `LICENSE`, `README.md` | **Established.** These three tracked root documents are canonical repository documents. |
| Generated | None | **Established.** No generated artifacts or generation declarations exist. |
| Adapter | None | **Established.** No Claude Code, Codex, or other host adapter artifacts exist. |

This classification does not infer future ownership from upstream conventions.
Any downstream issue that introduces generated or adapter files must first name
their canonical source, generation direction, drift check, and edit policy.

## Repository capabilities and gaps

| Area | Classification | Current evidence and constraint |
| --- | --- | --- |
| Repository identity and licensing | **Established** | The fork tracks a README and two license documents and configures `origin` for `jbknick/agent-apple-foundation-handoff`. |
| Plugin shape | **Not established** | There is no plugin root, marketplace, manifest, skill, command, agent, hook, or other plugin artifact. |
| Repository runtimes and dependencies | **Not established** | No package definition, dependency declaration, build definition, or executable repository tooling exists. Host installations of Claude Code, Codex, and Swift do not establish a repository runtime. |
| Schemas and validation | **Not established** | There are no schemas, tests, workflows, or repository-native validation commands. |
| Generation and drift control | **Not established** | There are no generators, generated outputs, sync scripts, or drift checks. |
| Claude Code loading of this fork | **Not established** | The fork has no Claude plugin to validate, discover, install, enable, or exercise. |
| Codex loading of this fork | **Not established** | The fork has no Codex plugin to discover, install, enable, or exercise. |
| Apple SDK compilation | **Blocked** | Full-Xcode validation is unavailable with the active Command Line Tools developer directory. The observed Swift CLI alone does not prove examples that do not yet exist. |

The absence of these capabilities is an architecture constraint, not permission
to fabricate defaults. Downstream issues must make and record the relevant
decisions before implementation, and must prove implemented capabilities with
reproducible checks rather than file existence or Markdown validation alone.

## Pinned upstream bstack comparison

**Reference only.** At pinned revision
`34a04e16b8582d9ddc605563fea1f868732cca4e`, upstream bstack contains Claude
marketplace and plugin metadata, generated Codex marketplace and plugin
metadata, shared skills, JSON schemas, synchronization scripts, and BATS tests.
Its Codex-artifact drift check passed in the isolated checkout.

The upstream structure includes Claude-to-Codex generators such as
`scripts/generate-codex-plugin-manifests.sh` and
`scripts/generate-codex-marketplace.sh`, plus synchronization and drift-check
scripts. That upstream Claude-to-Codex generator model is **Reference only**.
It is not part of this fork, has not been selected as this fork's architecture,
and must not be copied into an authoritative claim.

The comparison supports a narrower conclusion: a canonical-Claude,
generated-Codex model is technically demonstrated by the pinned reference.
Whether this project adopts that model, modifies it, or selects another model
remains **Not established** until the responsible downstream decision is
recorded and implemented.

## Cross-host loading evidence

**Established.** The audit host had Claude Code `2.1.91`, Codex CLI `0.144.5`,
and Apple Swift `6.3.2` available when evidence was collected. This establishes
the observed host-tool versions only.

**Reference only.** Using temporary configuration directories, Claude Code
validated, discovered, installed, and enabled the representative upstream
`me@bstack` plugin. With an isolated `CODEX_HOME`, Codex discovered, installed,
and enabled the same representative upstream plugin. These checks demonstrate
that the installed CLIs can load the pinned upstream structure.

**Not established.** Those upstream checks do not prove that the authoritative
fork has a cross-host plugin, that its future Claude and Codex surfaces are
equivalent, or that its future capabilities work end to end. They also do not
prove that every ordinary user-level Claude Code or Codex configuration file
remained unchanged, because the transcript did not capture before-and-after
diffs of those ordinary configuration locations.

**Blocked.** `xcodebuild -version` exited `1` because full Xcode was not the
active developer directory. Any downstream validation that requires full Xcode
must report that condition as a blocker unless the host prerequisite changes.

## Downstream decisions still required

The audit deliberately does not pre-select the following decisions:

1. DEV-132 must establish the plugin topology and the authoritative ownership
   boundary between shared canonical content, generated host metadata, and any
   host adapters.
2. DEV-133 must inherit the selected ownership boundary when defining schemas
   and contracts; it must not treat the pinned upstream schema layout as fork
   authority.
3. DEV-135 must define generation direction, exact generated outputs,
   deterministic generation commands, and a drift check before generated files
   become part of the repository model.
4. DEV-139 must define reproducible cross-host E2E proof for the implemented
   fork. Upstream plugin discovery or installation alone is insufficient proof.

Across those issues, repository runtime and dependency choices, validation
entry points, fixture ownership, host-isolation requirements, and behavior when
required SDKs or binaries are unavailable remain **Not established** unless a
prior approved decision supplies them. Each issue must record the decision and
propagate its impact before dependent work begins.

## Files downstream must not edit directly

The list is empty.

**Established.** No generated files exist in the authoritative fork, so there
are currently no generated files for downstream work to avoid editing
directly. This empty list is not permanent policy: when generation is approved,
the owning issue must add the exact generated paths and their canonical sources
before those outputs are committed.

## Validation contract for this revision

This report is valid for the authoritative tree at
`7ec92734127236e29ab88d66c1b41f663149ce0e` and the pinned comparison at
`34a04e16b8582d9ddc605563fea1f868732cca4e`. Its repository findings can be
reproduced by:

1. listing the authoritative tree with `git ls-tree -r --name-only
   7ec92734127236e29ab88d66c1b41f663149ce0e`;
2. checking the probed plugin, runtime, schema, script, test, and workflow paths
   at that revision;
3. confirming the pinned upstream identity before using any upstream result as
   **Reference only**; and
4. running the report's semantic and branch-scope gates recorded in the linked
   command transcript and DEV-127 implementation plan.

Passing document semantics and branch-scope checks validates this audit
revision only. It does not establish plugin loading, generated-artifact
freshness, Apple API correctness, Swift compilation, or cross-host behavioral
equivalence. Any tree change that introduces a plugin, runtime, generator,
schema, test, or adapter requires a new capability-specific validation contract
and must update this classification instead of relying on the old absence
evidence.
