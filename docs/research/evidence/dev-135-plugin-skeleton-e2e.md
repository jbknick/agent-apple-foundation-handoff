# DEV-135 Plugin Skeleton Structural Evidence

## Candidate identity

- Candidate branch: `codex/dev-135-minimal-plugin-skeleton`
- Base: main `c749d14129888c643b66646158735bf58e6fc603`
- Exact tested source commit:
  `6a2425968db11153a9e9c61c919fbe27d824c6ce`
- Exact tested source tree:
  `3b83adc9a0cb8546694378f128f41cc116f45d3f`
- The follow-up commit changes only this evidence document; it does not change
  the tested source tree above.

## Deterministic generation and contract checks

The generator consumed five canonical inputs and owned three generated
outputs. Two consecutive write executions and one check execution each
reported `generated artifacts are synchronized`. The bytes of all three
generated outputs were identical before the first write, after the first
write, and after the second write.

The repository suite passed 56 of 56 tests. It included 21 generated-artifact
test methods and 38 isolated canonical-mutation cases. The current Codex plugin
validator also passed the metadata-only package.

The empty-directory regression was observed RED for both reserved generated
namespaces: each synchronized isolated check incorrectly exited `0`. GREEN
rejected both paths with the normalized `generated artifacts: unexpected
generated path` diagnostic while the existing unexpected-file, nested-parent
symlink, and generated-output symlink checks remained passing.

The structural-probe race regressions were also observed RED. A pathname
replacement during a regular-file read and an in-place mutation during that
read both returned without `ProbeFailure`; the captured executable metadata was
unused, so a same-path executable replacement emitting the same exact version
was accepted. A follow-up RED marker proved that checking the version before
the replacement snapshot invoked an already-drifted executable. GREEN uses one
exact device/inode/type/mode/size/mtime/ctime snapshot: regular-file reads must
match it at pre-open, opened, post-read, and current-path boundaries, while the
host version invocation is bracketed by matching executable snapshots. All four
focused pathname, in-place, pre-version replacement, and during-version
replacement tests passed without exposing a private path.

Canonical and generated metadata retained these exact values:

| Contract | Observed value | Result |
| --- | --- | --- |
| Plugin identity | `apple-foundation-models-handoff` | pass |
| Plugin version | `0.1.0` | pass |
| Marketplace identity | `agent-apple-foundation-handoff` | pass |
| Canonical source | `./plugins/apple-foundation-models-handoff` | pass |
| Interface category | `Developer Tools` | pass |
| Marketplace category | `Developer Tools` | pass |
| Installation policy | `AVAILABLE` | pass |
| Authentication policy | `ON_INSTALL` | pass |
| Canonical/generated capabilities | `[]` | pass |
| Skills | absent | pass |
| Five future direct positive workflows | absent | pass |
| Bounded non-positive preselection router | absent | pass |

## Codex structural load

The pinned host prerequisite was exact Codex CLI `0.144.5`. Two independent
runs each used a new isolated `CODEX_HOME`, executed the four approved local
marketplace/list/install/list flows, exited `0`, and emitted byte-identical
JSON. The required `jq` structural selector passed.

Exact normalized JSON:

```json
{"cacheFiles":[".claude-plugin/plugin.json",".codex-plugin/plugin.json","metadata/codex-interface.json"],"canonicalManifestSha256":"2ef1c67b4c5d4788b5316dd645aa9e580fea18b6ec5cbfb8759b355af31ae618","capabilities":[],"capabilityActivation":"blocked/production_skill_not_implemented","enabled":true,"evidenceId":"E-CODEX-LOAD-001","generatedManifestSha256":"2cf94a87d9e25e687435e423d3e1f11bf848e5fac3b1ae1399e83c70085047b8","host":"codex","hostPath":"<host-path>","hostVersion":"0.144.5","marketplace":"agent-apple-foundation-handoff","pluginId":"apple-foundation-models-handoff@agent-apple-foundation-handoff","pluginVersion":"0.1.0","status":"pass"}
```

The installed path resolved below the isolated `CODEX_HOME`. Source and cached
payloads each contained only the following regular, non-symlink files, and each
cached SHA-256 exactly equalled its source SHA-256:

| Allowlisted relative file | Verified source and cache SHA-256 |
| --- | --- |
| `.claude-plugin/plugin.json` | `2ef1c67b4c5d4788b5316dd645aa9e580fea18b6ec5cbfb8759b355af31ae618` |
| `.codex-plugin/plugin.json` | `2cf94a87d9e25e687435e423d3e1f11bf848e5fac3b1ae1399e83c70085047b8` |
| `metadata/codex-interface.json` | `d6a9fa8f1b4932d5976905e6da28b80e9759c71a17a77b601b0e945f0e09f035` |

The historical missing-Codex prerequisite path was exercised separately and
emitted the exact normalized blocked result at exit `2`.

## Inherited regression gates

- DEV-131 passed 26 of 26 unit tests and the 11 of 11 proof matrix; its zero
  denominator remained `not_applicable`.
- DEV-130 compiled with warnings as errors, matched the exact golden output
  `SUMMARY passed=8 failed=0`, and repeated byte-identically.
- DEV-128 ran against installed SDK `26.5`: all six positive gates passed and
  both strict expected blockers failed with their required capability-specific
  diagnostics.

## Status matrix

| Evidence or gate | Status | Reason |
| --- | --- | --- |
| `E-CODEX-LOAD-001` | pass | isolated structural discovery, installation, enabled state, and cache integrity verified |
| `E-CODEX-ACTIVATE-001` | blocked | `production_skill_not_implemented` |
| `E-CLAUDE-LOAD-001` | blocked | `deferred_by_owner`; Claude was not invoked |
| `BATS` | pass | Bats `1.13.0`; `tests/plugin_skeleton.bats` passed 3 of 3 |
| `DEV-131` | pass | 26 of 26 unit tests and 11 of 11 proof cases |
| `DEV-130` | pass | exact 8 of 8 golden cases; zero failures; repeat byte-identical |
| `DEV-128` | pass | SDK 26.5 six positive gates and two strict expected blockers |
| `pre-commit` | blocked | `deferred_by_owner` |
| `markdownlint` | blocked | `deferred_by_owner` |

This is structural discovery and installation evidence only. It is not
capability proof: none of the five future direct positive design, implement,
review, debug, or validate workflows exists in DEV-135, the bounded
non-positive preselection router is also absent, and no activation or router
execution is claimed. That preselection boundary is not a sixth positive
workflow and is separate from the DEV-142 through DEV-145 cost router,
`PostToolUse` hooks, and Swift bridge chain.

The BATS row was rerun after the approved `bats-core` installation. The exact
tracked suite passed all three tests: synchronized artifacts, idempotent
multi-output write mode, and generated Codex manifest drift rejection.
