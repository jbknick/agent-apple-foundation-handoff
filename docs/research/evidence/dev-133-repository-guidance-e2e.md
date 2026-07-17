# DEV-133 repository-guidance E2E evidence

## Evidence identity

- Issue: `DEV-133`
- Branch: `codex/dev-133-repository-guidance`
- Reviewed base: `ca767a0c50e1b527fed5c87e0922bf51cf655295`
- Tested source head: `0ed96ba9c65f645dc796061caacc413556926257`
- Execution date: `2026-07-17`
- Repository identity: `<repo>`
- Host identity: `<host-path>` for each captured executable

The same answer-free, seven-field semantic contract was used for both fresh
host rows. Host inputs, transport envelopes, event streams, last messages, and
diagnostics remained transient. The validator compared machine-readable host
fields with the tracked repository guidance after each invocation.

## Source artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `CLAUDE.md` | `74880413e9a7e2be2c743b362094147780f9a6971d2770585b5ce5e7cff81474` |
| `AGENTS.md` | `0fadd0ed908fb05fb486116fa9c4335b21d7c11e575c1f7321ceccd0729ad992` |
| `scripts/sync_generated_artifacts.py` | `d7ed3a0ce419a615f32150d412146de687661dabbfb83f0eda7fae39f767e8b4` |
| `tests/test_repository_guidance.py` | `66e3e964b4835498de2808b2026e78cd4de0e73ba619f8b729d7e02e252cf05f` |

## Semantic assertion contract

1. The only authored canonical repository-guidance path is `CLAUDE.md`.
2. The exact generated, non-editable path set is `AGENTS.md`,
   `.codex-plugin/plugin.json`, and `.agents/plugins/marketplace.json`.
3. The write/check commands are
   `python3 scripts/sync_generated_artifacts.py --write` and
   `python3 scripts/sync_generated_artifacts.py --check`.
4. The repository test command is
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v`.
5. The preferred planned plugin source is `./`, conditionally; the deterministic
   fallback is `./plugins/apple-foundation-models-handoff`.
6. A request to edit a generated Codex manifest directly must be refused;
   change the approved canonical source and run synchronization instead.
7. Structural repository guidance does not prove plugin capability.

## Fresh-host rows

| Host | Identity | Strict version | Status | Assertions | Exit | Post-capture recheck |
| --- | --- | --- | --- | ---: | ---: | --- |
| Claude Code | `<host-path>` | `2.1.91` | `blocked reason=auth-unavailable` | 0 | 1 | `pass` |
| Codex CLI | `<host-path>` | `0.144.5` | `pass` | 7 | 0 | `pass` |

The Claude row reached the approved executable and version prerequisite, but
authentication was unavailable before a usable semantic result. It is an
explicit host blocker, not a repository pass. The Codex row satisfied all seven
assertions. Both rows retained the originally captured executable identity and
strict version through their post-invocation checks.

## Deterministic validation

| Check | Exact command or contract | Normalized result |
| --- | --- | --- |
| Generated adapter synchronization | `python3 scripts/sync_generated_artifacts.py --check` | `pass` |
| Repository guidance tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v` | `pass tests=18 failures=0` |
| DEV-131 regression tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v` | `pass tests=26 failures=0` |
| DEV-131 proof runner | `PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py` | `pass cases=11 oracle_matches=11 evidence=pass rubric=pass` |
| DEV-130 compile | `swiftc -warnings-as-errors -parse-as-library fixtures/dev-130/HandoffSecurityPolicy.swift fixtures/dev-130/AdversarialScenarios.swift -o <temp>/dev130-adversarial` | `pass` |
| DEV-130 golden comparison | execute normalized `<temp>/dev130-adversarial`, then compare with `fixtures/dev-130/expected-output.txt` | `pass scenarios=7 failures=0` |
| `pre-commit` prerequisite | captured command resolution only | `blocked reason=missing-binary` |
| `markdownlint` prerequisite | captured command resolution only | `blocked reason=missing-binary` |

No dependency was installed to hide either missing optional prerequisite.

## Scope, privacy, cache, and cleanliness

- Exact DEV-133 allowlist: `pass paths=6` for `AGENTS.md`, `CLAUDE.md`, this
  evidence file, the DEV-133 plan, the shared generator, and its guidance tests.
- Task 3 commit scope: `pass paths=1`; this evidence file is the only tracked
  Task 3 path.
- Guidance placement: `pass agents_files=1`; the sole `AGENTS.md` is a regular
  root file.
- Private-path and executable-path scan: `pass matches=0`.
- Raw host-artifact and sensitive-content scan: `pass matches=0`.
- Cache scan: `pass`; no `__pycache__` directory or `.pyc` file exists in the
  repository.
- Transient host/test storage: `pass`; automatic temporary storage was removed.
- Pre-evidence source state: `clean` at the tested source head.
- Final commit and worktree cleanliness are rechecked after this document is
  committed and are part of the handoff evidence.

## Explicit nonclaims

- This evidence does not claim plugin metadata creation, host loading,
  discovery, installation, activation, progressive reference loading, model
  capability, or any other plugin capability.
- It does not prove an Apple Foundation Models runtime, Apple device, hardware,
  entitlement, SDK compile beyond the inherited DEV-130 fixture, or Xcode-host
  result.
- It does not claim a Claude semantic pass while authentication is blocked.
- It does not claim `pre-commit` or Markdown-lint success while their binaries
  are missing.
- No push, pull request, merge, tag, publish, release, or issue-status change
  was performed.
