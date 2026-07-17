# DEV-135 Minimal Cross-Host Plugin Skeleton Design

Issue: [DEV-135](https://linear.app/devprentice/issue/DEV-135)

Status: approved in brainstorming and written-spec review on 2026-07-17

## Objective

Create the smallest honest, installable plugin package that establishes the
approved Claude-authored/Codex-generated metadata boundary without advertising
production skills before those skills exist.

DEV-135 proves deterministic generation, contract validation, packaging, and
Codex structural discovery. It does not implement or claim the five handoff
workflows, which remain owned by DEV-136 and DEV-137.

## Inputs and constraints

This design inherits:

- the current fork as authoritative from DEV-127;
- the one-corpus, Claude-authored/Codex-generated production pattern from
  DEV-129;
- the approved canonical/generated ownership, identity, and two candidate
  package layouts from DEV-132;
- the generated root guidance adapter and hardened Python standard-library
  sync entry point from DEV-133;
- the exact five-skill topology and no-plugin-worker decision from DEV-134;
- the owner-approved Codex-first validation policy recorded on DEV-133 and
  propagated to DEV-135; and
- the owner-approved DEV-135 decisions recorded in Linear comment
  `31eec926-16d5-4212-beda-933741615cc7`.

The root-source candidate `./` was conditional on cache integrity and real
activation/reference-loading proof on both Claude Code and Codex. Claude Code
testing is currently deferred by owner decision. Therefore DEV-135 selects the
already approved conventional fallback and does not weaken the root candidate's
acceptance condition.

## Selected approach

Use the conventional package root:

```text
plugins/apple-foundation-models-handoff
```

with marketplace source:

```text
./plugins/apple-foundation-models-handoff
```

The package contains only shared identity, Codex presentation metadata, and
their generated Codex manifest. Repository guidance, marketplaces, schemas,
generation code, tests, fixtures, research, and evidence remain outside the
installed plugin payload.

### Rejected alternatives

1. **Repository-root package source `./`.** Rejected because the approved
   two-host proof condition cannot be satisfied while Claude Code host testing
   is deferred.
2. **Pre-created empty skill directories.** Rejected because placeholder
   production surfaces would advertise unfinished work and a current Codex
   validator treats every non-hidden child of `skills/` as a real skill that
   must contain a valid `SKILL.md`.
3. **Placeholder skill documents.** Rejected by the DEV-135 out-of-scope and
   no-unfinished-skills requirements. DEV-136 creates complete real skills.

## Identity and presentation contract

### Shared identity

The canonical Claude manifest owns only shared identity:

| Field | Value |
| --- | --- |
| `name` | `apple-foundation-models-handoff` |
| `version` | `0.1.0` |
| `description` | Installable metadata scaffold for Apple Foundation Models handoff workflows; production skills are not included yet. |
| `author.name` | `Joseph Knickerbocker` |
| `author.url` | `https://github.com/jbknick` |
| `homepage` | `https://github.com/jbknick/agent-apple-foundation-handoff` |
| `repository` | `https://github.com/jbknick/agent-apple-foundation-handoff` |
| `license` | `LicenseRef-PolyForm-Noncommercial-1.0.0` |
| `keywords` | `apple`, `foundation-models`, `handoff`, `swift`, `agents` |

The manifest omits `skills`, hooks, MCP servers, apps, and commands. Those
omissions are intentional and test-enforced.

### Codex presentation input

`plugins/apple-foundation-models-handoff/metadata/codex-interface.json` owns:

| Field | Value |
| --- | --- |
| `displayName` | `Apple Foundation Models Handoff` |
| `shortDescription` | `Inspect the installable handoff plugin scaffold.` |
| `longDescription` | Metadata-only scaffold text that explicitly says the five production workflows are not included yet. |
| `developerName` | `Joseph Knickerbocker` |
| `category` | `Developer Tools` |
| `capabilities` | `[]` |
| `websiteURL` | `https://github.com/jbknick/agent-apple-foundation-handoff` |
| `defaultPrompt` | One bounded prompt asking Codex to inspect installed metadata and report currently available capabilities. |

An empty capabilities array is the only truthful value in DEV-135. The
installed current validator accepts the array while requiring the field to be
present. DEV-136 updates this input only when the five real skills exist.

### Marketplace identities

The canonical Claude marketplace is rooted at
`.claude-plugin/marketplace.json` and uses the conventional Claude shape:

- marketplace name `agent-apple-foundation-handoff`;
- owner `Joseph Knickerbocker`;
- one plugin entry named `apple-foundation-models-handoff`;
- source `./plugins/apple-foundation-models-handoff`;
- the same honest scaffold description and version `0.1.0`.

The canonical Codex marketplace input is rooted at
`metadata/codex-marketplace.json` and owns:

- marketplace name `agent-apple-foundation-handoff`;
- marketplace display name `Agent Apple Foundation Handoff`;
- stable one-entry ordering;
- source kind `local` and source path
  `./plugins/apple-foundation-models-handoff`;
- marketplace category `Developer Tools`;
- `policy.installation = AVAILABLE`;
- `policy.authentication = ON_INSTALL`; and
- no `policy.products` override.

The Codex presentation category and marketplace-entry category are distinct
fields with the same selected value. The generator must not collapse their
ownership.

## File tree and ownership

DEV-135 adds or updates exactly this production skeleton and its repository
support:

```text
.
├── CLAUDE.md                                      # canonical guidance, existing
├── AGENTS.md                                      # generated, existing and refreshed
├── .claude-plugin/
│   └── marketplace.json                           # canonical Claude marketplace
├── .agents/plugins/
│   └── marketplace.json                           # generated Codex marketplace
├── metadata/
│   └── codex-marketplace.json                     # canonical Codex marketplace input
├── plugins/apple-foundation-models-handoff/
│   ├── .claude-plugin/
│   │   └── plugin.json                            # canonical shared identity
│   ├── .codex-plugin/
│   │   └── plugin.json                            # generated Codex manifest
│   └── metadata/
│       └── codex-interface.json                   # canonical Codex interface input
├── schemas/
│   ├── codex-interface-input.schema.json          # canonical input contract
│   └── codex-marketplace-input.schema.json        # canonical input contract
├── scripts/
│   └── sync_generated_artifacts.py                # extended single entry point
├── tests/
│   ├── e2e/
│   │   └── codex_plugin_load.py                   # isolated Codex structural probe
│   ├── plugin_skeleton.bats                       # shell-level generator contract
│   ├── test_generated_artifacts.py                # generation and mutation tests
│   ├── test_plugin_contract.py                    # package and metadata tests
│   └── test_repository_guidance.py                # inherited guidance regressions
└── docs/
    ├── research/evidence/
    │   └── dev-135-plugin-skeleton-e2e.md         # normalized structural evidence
    └── superpowers/
        ├── specs/2026-07-17-dev-135-minimal-plugin-skeleton-design.md
        └── plans/2026-07-17-dev-135-minimal-plugin-skeleton.md
```

DEV-135 does not create `skills/`, `references/`, `agents/`, `hooks/`, `mcp/`,
`commands/`, plugin-local `scripts/`, assets, or a plugin-local README.

## Generation architecture

`scripts/sync_generated_artifacts.py` remains the only sync entry point and
keeps its current `--write` and `--check` modes.

### Render pipeline

1. Resolve the repository root through the existing controlled entry-point
   rules.
2. Read every canonical input through the existing non-symlink, regular-file,
   and stable-identity protections.
3. Parse JSON with duplicate-key rejection.
4. Validate canonical inputs against explicit custom contract functions that
   mirror the committed JSON Schemas without adding a runtime dependency.
5. Render all three generated outputs in memory:
   - `AGENTS.md` from `CLAUDE.md`;
   - the Codex manifest from the shared identity plus Codex interface input;
   - the Codex marketplace from shared identity plus Codex marketplace input.
6. Validate the rendered JSON outputs before any destination write.
7. Serialize JSON deterministically with stable key order, two-space
   indentation, UTF-8, and one trailing newline.

### Check mode

Check mode performs no writes. For every known generated destination it:

- rejects a symlink or non-regular obstruction;
- compares bytes with the in-memory render;
- reports missing or changed outputs as normalized drift;
- rejects generated-looking files outside the explicit three-path allowlist;
  and
- exits nonzero if any row is not synchronized.

### Write mode

Before the first write, write mode preflights every canonical input,
destination parent, and destination file. It then applies the existing
per-output safe temporary-file and atomic-replacement algorithm to each changed
output, rechecking identities at the same race-sensitive boundaries already
covered by DEV-133 tests.

This issue does not claim filesystem-wide transactionality across three files.
If a process or filesystem failure interrupts the batch, the next check must
report every partial difference as drift. A partial batch can never be reported
as synchronized.

## Schema and validation contract

The two JSON Schema files are committed, machine-readable descriptions of the
authored Codex-only inputs. The standard-library generator implements the
matching required-field, type, enum, path, and unknown-field checks directly.

Validation enforces at least:

- strict semver `0.1.0` for the initial identity;
- exact plugin/marketplace identity agreement;
- HTTPS repository/author/website URLs;
- the exact conventional source path;
- non-empty required presentation strings;
- the exact empty capabilities array; non-empty capability claims are rejected;
- one to three non-empty starter prompts of at most 128 characters;
- allowed policy enums and omitted product gating;
- no path traversal, absolute paths, symlinks, or external package links;
- no production surface fields that DEV-135 has not implemented; and
- no unknown fields that could silently become a second source of truth.

The committed schemas and custom validators are cross-tested so drift between
their enumerations, required keys, and additional-property policy fails the
repository suite.

## Package and host behavior

### Codex structural proof

An isolated `CODEX_HOME` test will:

1. capture and recheck the exact Codex 0.144.5 executable;
2. add the repository root as a local marketplace;
3. verify marketplace discovery and the exact marketplace name;
4. list the plugin as available;
5. install `apple-foundation-models-handoff@agent-apple-foundation-handoff`;
6. verify installed/enabled state and exact version;
7. compare shared identity, Codex interface, category, policy, source, and empty
   capabilities against canonical inputs; and
8. inspect the cache to prove the effective payload contains only the plugin
   package and excludes repository fixtures, tests, research, evidence,
   credentials, private paths, and generated temporary files.

Because DEV-135 contains no production skills, this test proves structural
discovery and installation only. It must not be cited as evidence that a
design, implement, review, debug, or validate workflow activated. DEV-139 owns
fresh-task activation evidence after DEV-136 and DEV-137.

### Deferred rows

Claude Code 2.1.91, `pre-commit`, and `markdownlint` are recorded as
`blocked/deferred_by_owner`, never as pass, inferred parity, or a substituted
gate. DEV-141 remains unable to produce a release-ready result until these
rows are run successfully during the requested circle-back.

## Test design

### Repository tests

`tests/test_plugin_contract.py` verifies:

- exact file tree and absence of unapproved surfaces;
- identity and version parity across canonical/generated metadata;
- distinct category-field ownership;
- honest zero-capability state and absence of `skills`;
- marketplace source and policy;
- schema/validator agreement;
- all referenced paths remain within the package or repository boundary; and
- no placeholders, credentials, private paths, runtime service/provider
  endpoints, or repository-only payload entries.

`tests/test_generated_artifacts.py` verifies:

- exact deterministic render for all outputs;
- clean check and idempotent repeated write;
- isolated canonical-input mutations for every required validation branch;
- drift from changed, missing, obstructed, or extra generated paths;
- symlink, non-regular, path-swap, and destination-parent attacks;
- preflight-before-write behavior when a later destination is invalid;
- normalized diagnostics and nonzero exits; and
- temporary-file cleanup after failures.

Existing DEV-133 guidance tests remain unchanged except where their explicit
planned-output assertions must become present-output assertions.

### Codex E2E evidence

The isolated Codex test records normalized commands, exit codes, host version,
marketplace/plugin JSON, installed cache path, allowlisted relative payload
paths, and hashes of both canonical and generated manifests. Evidence contains
no credentials, absolute private paths, or raw host state.

### Inherited regression gates

DEV-135 reruns:

- all repository unit tests;
- generator check and repeated generation;
- DEV-130 seven-scenario golden validation;
- DEV-131 26-test evaluation suite and 11-case proof;
- DEV-128 SDK 26.5 compile matrix when the installed SDK remains available;
- privacy/security scanners and clean-diff checks; and
- the current official Codex plugin validator against the built package.

## Atomic review and PR boundary

DEV-135 is one stacked PR based on DEV-134. Its intended reviewable commits
are:

1. **Design contract:** this approved design document only.
2. **Metadata and generation:** canonical inputs, schemas, generated outputs,
   generator extension, and focused TDD tests that keep the commit green.
3. **Codex evidence and plan conformance:** host-level evidence, any bounded
   repository validation harness required by DEV-135, and final documentation
   updates.

No commit will mix DEV-136 skill content, DEV-137 references, DEV-138
hardening beyond the DEV-135 generator contract, or DEV-139 workflow E2E.

## Definition-of-done interpretation

DEV-135 may be code-complete and reviewable when the skeleton, generation,
drift, schemas, package contract, and isolated Codex structural proof all pass.
Under the owner-approved interim policy, its Claude Code, `pre-commit`, and
`markdownlint` rows remain deferred and prevent a final release-ready claim in
DEV-141. No deferred row is converted to pass merely to close this issue.

The issue's evidence must distinguish:

- `pass`: a command actually ran against the pinned artifact and satisfied its
  oracle;
- `fail`: a command ran and contradicted the oracle;
- `blocked/deferred_by_owner`: the owner intentionally postponed the named
  host or binary gate; and
- `not_applicable`: only a genuinely inapplicable row, never a missing
  prerequisite or unimplemented capability.
