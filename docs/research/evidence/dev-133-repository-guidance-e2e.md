# DEV-133 repository-guidance review evidence

## Current evidence identity

- Issue: `DEV-133`
- Branch: `codex/dev-133-repository-guidance`
- Reviewed main: `829d5f71ac5cb9609f96dde4a7ae73c32f42e3cd`
- Exact tested source commit: `8d856fd32e43cb21b594f5d6d292b42c580e7edc`
- Deterministic execution date: `2026-07-19`
- Repository identity: `<repo>`
- Host identity: `<host-path>` for each executable candidate

The current review ran deterministic repository checks against the exact source
commit above. It did not run a new model-backed semantic session. The earlier
host rows are retained below only as dated historical evidence and do not prove
the corrected current guidance.

## Current source artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `CLAUDE.md` | `ce7345cf05c1220bbc9371cf314c08fed5249cddb95207d90b96f8ca1c787b3f` |
| `AGENTS.md` | `0e149aea836a919a786324df168f38f12979a3d29e44e8a65a8afe93f64cacdb` |
| `scripts/sync_generated_artifacts.py` | `b1212533c7a1234a2d65787f1301a9702af089b7e3c84365cffd7e0ed7f26c2d` |
| `tests/test_repository_guidance.py` | `2c263def429c386f1042f49d2382f2a2f9202f92fb308768343e7d101e38befe` |
| `docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md` | `c2ad1ebb647c2722a3b6932770ff8ff9e1a6a2975b7334773957c5da9910a66a` |

## Current guidance contract

1. The current repository-guidance artifact set contains one authored
   canonical input, `CLAUDE.md`, and one generated root output, `AGENTS.md`.
2. Plugin metadata, generated manifests, skills, and references are planned
   later-issue work and are absent under DEV-133.
3. Five positive workflows cover design, implementation, review, debugging,
   and validation. One bounded non-positive preselection router may only
   clarify, decline, or hand off requests outside that set.
4. The non-positive router is not a sixth positive skill and is distinct from
   the later DEV-142 through DEV-145 cost router, `PostToolUse` hook, and Swift
   bridge chain. DEV-133 implements no runtime chain.
5. `synchronize(root, write)` returns `False` with only the normalized canonical
   diagnostic for invalid canonical input; generated-output diagnostics remain
   separate.
6. The generated adapter is derived only through
   `scripts/sync_generated_artifacts.py`, is a regular root file, and remains at
   or below 90 lines and 6500 bytes.
7. Structural guidance and host prerequisites never prove plugin capability.

## Current deterministic validation

| Check | Exact command or contract | Result |
| --- | --- | --- |
| Generated synchronization | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check` | `pass` |
| Repository guidance tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v` | `pass tests=21 failures=0` |
| Public invalid-input API | focused `test_synchronize_normalizes_invalid_canonical_input` | `pass return=false diagnostic=canonical-only` |
| Root generated guide | regular-file count and size checks | `pass files=1 lines=90 bytes=5878` |
| Current implementation plan | compact contract and command review | `pass lines=182 bytes=8259 historical checklists/model recipes absent` |
| DEV-131 tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v` | `pass tests=26 failures=0` |
| DEV-131 proof | `PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py` | `pass cases=11 oracle_matches=11 evidence=pass rubric=pass` |
| DEV-130 compile | `swiftc -warnings-as-errors -parse-as-library` over both DEV-130 sources | `pass` |
| DEV-130 golden and repeat | compare first output with the golden, then compare a second execution byte-for-byte | `pass scenarios=8 failures=0 repeat=identical` |
| Scope | diff from reviewed main against the exact DEV-133 allowlist | `pass paths=6` |
| Cache and diff hygiene | no repository `__pycache__`/`.pyc`; `git diff --check` | `pass` |

## Current prerequisite snapshot

This snapshot checks executable presence and strict version output only. It is
not a semantic host run and not plugin capability evidence.

| Candidate or tool | Current normalized status | Meaning |
| --- | --- | --- |
| Approved Claude Code candidate | `present version=2.1.91` | Approved candidate exists; current semantic E2E was not rerun. |
| Default Claude Code candidate | `present version=2.1.140` | Diagnostic-only candidate; it cannot substitute for `2.1.91`. |
| Codex CLI candidate | `present version=0.144.5` | Approved candidate exists; current semantic E2E was not rerun. |
| `pre-commit` | `blocked reason=missing-binary` | Deferred prerequisite, not a pass. |
| `markdownlint` | `blocked reason=missing-binary` | Deferred prerequisite, not a pass. |

No dependency was installed and no alternate model, retry, or diagnostic Claude
candidate was used to convert a deferred or blocked row into a pass.

## Historical semantic rows, not rerun

The rows below were executed on `2026-07-17` against historical source commit
`0ed96ba9c65f645dc796061caacc413556926257`. They were not rerun on the current
source commit and are not current acceptance evidence.

| Host | Historical version | Historical result | Current interpretation |
| --- | --- | --- | --- |
| Claude Code | `2.1.91` | `blocked reason=auth-unavailable assertions=0` | Still no semantic pass; current row deferred. |
| Codex CLI | `0.144.5` | `pass assertions=7` | Historical only; current row deferred. |

The historical seven-field contract incorrectly treated planned generated
manifest paths as present outputs. The current contract supersedes that claim,
so the historical Codex pass cannot validate the corrected ownership model.
Raw prompts, responses, reasoning, tool content, diagnostics, executable paths,
configuration, and session data remain excluded.

## Scope, privacy, and nonclaims

- Exact DEV-133 scope is six paths: `CLAUDE.md`, generated `AGENTS.md`, the
  shared generator, its tests, this evidence file, and the DEV-133 plan.
- The adapter is generated only from canonical `CLAUDE.md`; it was not edited
  directly. Private-path, raw-host-artifact, cache, and diff checks pass.
- DEV-133 remains guidance-only. This evidence does not claim plugin metadata,
  skills/references, loading, discovery, installation, activation, routing
  runtime, hooks, bridge code, model capability, or release action.
- It does not prove an Apple device, hardware, entitlement, full Xcode, or
  Apple Foundation Models runtime result beyond inherited deterministic fixtures.
- Claude semantic E2E, `pre-commit`, and `markdownlint` remain deferred or
  blocked. DEV-133 therefore remains In Review rather than relabelling them as
  passed.
