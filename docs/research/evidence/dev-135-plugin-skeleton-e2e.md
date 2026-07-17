# DEV-135 Plugin Skeleton Structural Evidence

## Candidate identity

- Candidate branch: `codex/dev-135-minimal-plugin-skeleton`
- Exact tested implementation parent:
  `030ca996d646e591ef6d79f9919506793ea918e9`
- Tested candidate tree: the exact parent above plus
  `tests/e2e/codex_plugin_load.py`. This evidence document was assembled in the
  same uncommitted Task 4 tree; it does not invent or claim its own commit SHA.

## Deterministic generation and contract checks

The generator consumed five canonical inputs and owned three generated
outputs. Two consecutive write executions and one check execution each
reported `generated artifacts are synchronized`. The bytes of all three
generated outputs were identical before the first write, after the first
write, and after the second write.

The repository suite passed 46 of 46 tests. It included 20 generated-artifact
test methods and 38 isolated canonical-mutation cases. The current Codex plugin
validator also passed the metadata-only package.

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

The missing-Codex prerequisite path was also exercised separately and emitted
the exact normalized blocked result at exit `2`.

## Status matrix

| Evidence or gate | Status | Reason |
| --- | --- | --- |
| `E-CODEX-LOAD-001` | pass | isolated structural discovery, installation, enabled state, and cache integrity verified |
| `E-CODEX-ACTIVATE-001` | blocked | `production_skill_not_implemented` |
| `E-CLAUDE-LOAD-001` | blocked | `deferred_by_owner`; Claude was not invoked |
| `BATS` | pass | Bats `1.13.0`; `tests/plugin_skeleton.bats` passed 3 of 3 |
| `pre-commit` | blocked | `deferred_by_owner` |
| `markdownlint` | blocked | `deferred_by_owner` |

This is structural discovery and installation evidence only. It is not
capability proof: no design, implementation, review, debug, or validation
workflow exists in DEV-135, and no capability activation is claimed.

The BATS row was rerun after the approved `bats-core` installation. The exact
tracked suite passed all three tests: synchronized artifacts, idempotent
multi-output write mode, and generated Codex manifest drift rejection.
