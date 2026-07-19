# DEV-137 reference-library packaging and prerequisite evidence

## Scope and claim boundary

This record binds the Round 2 offline simplification proof to one source commit and
retains older structural Codex and explicitly directed reference-selection
outcomes as historical evidence only. It is not workflow-triggered activation,
does not satisfy `E-CODEX-ACTIVATE-001` or
`DEV137-CODEX-PROGRESSIVE-001`, and cannot complete DEV-137.

- Final Round 2 source commit: `6391619163c8f1afed1c76fd5dd024e170b161c9`
- Final Round 2 source tree: `78c118b036e3a2074b2c45612bbd7cfe9117b210`
- Deterministic verification date: `2026-07-20`
- Current live Codex/model/network run: not invoked
- Historical host candidate commit: `d27cc16d62fd0e23e5e62441d17122d622c09492`
- Historical host candidate tree: `a8c10274d81690deedd361161a1d4d916b70b72c`
- Historical Codex host: `codex-cli 0.144.5` at normalized `<host-path>`
- Historical selected model: `gpt-5.6-sol`; fallback was prohibited and not used
- Claude: not invoked

DEV-137 remains In Progress with blocker
`production_skills_not_integrated` until the mandatory combined-tip 25-case
DEV-136 workflow-triggered gate passes. That combined evidence remains blocked
and was not accessed or run during this correction.

## Reference payload identity

The current source commit contains exactly eight approved package files and the
following five reference identities. These current hashes are offline source
identity only; the structural cache probe was not rerun for this correction.

| Reference file | SHA-256 |
| --- | --- |
| `references/apple-api-availability.md` | `3bda66a1fd1f5d92afd437918a955c0103ad8cad399f29456271eea684f885c5` |
| `references/architecture-and-state.md` | `3eabd71891ff3b3d6960816df3e027e0d410cc6cf0ecf33dad87c02c90912839` |
| `references/evaluation-and-observability.md` | `9c8de725a9c559d72468413651130b6525f350515aa67e1aa488ca238378acd4` |
| `references/orchestration-patterns.md` | `3eec171cbaab5ea086e27902931ebeb321cf4d02ef19cd240d738e418d7a9ab0` |
| `references/security-context-and-recovery.md` | `42d390e8647c532df9edc6414a908305ca1455e6282cf18c3a29bd6fa4579796` |

Additional pinned identities:

- canonical manifest SHA-256:
  `2ef1c67b4c5d4788b5316dd645aa9e580fea18b6ec5cbfb8759b355af31ae618`
- generated Codex manifest SHA-256:
  `2cf94a87d9e25e687435e423d3e1f11bf848e5fac3b1ae1399e83c70085047b8`
- installed SDK 26.5 interface SHA-256:
  `ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc`

## Counts and deterministic results

| Check | Result |
| --- | --- |
| Reference topology | pass, exactly 5 regular Markdown files |
| Cache payload | pass, offline contract/oracle confirms exactly 8 regular files; current isolated cache not run |
| Relative reference links | pass, 43 occurrences; every reference has an incoming sibling edge |
| Approved official sources | pass offline, 30 unique links; opt-in network resolution skipped |
| Swift labels | pass, 4 blocks with exactly one allowed visible label each |
| `compiled_sdk_26_5` | pass, 1/1 block type-checked against SDK 26.5 |
| Focused disclosure module | pass, 28/28: 19 closed-parser, 4 probe-boundary, and 5 disclosure-host tests |
| Host identity group | pass, 10/10 |
| Focused reference group | pass, 14 total with 13 executed/pass and 1 opt-in network skip |
| Guidance and plugin regression | pass, 38/38; generated adapter exactly 90 lines |
| Direct-script blocked-PATH proof | pass, 2/2 exact normalized result dictionaries; both exits `2` |
| Repository unit suite | pass, 137 tests with 136 executed/pass and 1 opt-in network skip |
| Python compilation | pass, 3/3 verification modules |
| Generated synchronization | pass |
| DEV-128 inherited regression | pass, 6/6 positives and 2/2 exact expected blockers |
| DEV-130 inherited regression | pass, compile/golden/repeat and 8/8 scenarios; golden includes one additional `SUMMARY` line |
| DEV-131 inherited regression | pass, 26/26; corpus 11/11; 8 evidence files |
| DEV-138 inherited regression | pass, 36/36 tests and exact 43-row oracle |
| BATS | pass, 3/3 |
| Diff/scope/cache hygiene | pass; source commit changes exactly 3 authorized paths, branch delta remains 16 paths, no repo Python cache, no untracked paths |

Round 2 removed only superseded verification machinery. Static AST and `rg`
reachability found no repository consumer of the deleted generic/recursive
parser symbols; `run_case` uses `parse_disclosure_events` as its sole parser.
The authoritative size reductions are:

| File | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| `tests/e2e/codex_reference_disclosure.py` | 3,642 lines | 845 lines | 2,797 lines |
| `tests/test_codex_reference_disclosure.py` | 1,447 lines | 689 lines | 758 lines |
| `docs/superpowers/plans/2026-07-17-dev-137-progressive-disclosure-reference-library.md` | 1,732 lines | 262 lines | 1,470 lines |

## Codex structural result

Historical `E-CODEX-LOAD-001` passed twice from fresh isolated homes at
candidate `d27cc16d62fd0e23e5e62441d17122d622c09492`, tree
`a8c10274d81690deedd361161a1d4d916b70b72c`. The normalized JSON
outputs were byte-identical with SHA-256
`a4b23e4d8744d6f85e36a23a6a927701aefdc8941ed893c145ec27275bf6c465`.
Both runs proved marketplace discovery, installation, enabled state, exact
eight-file source/cache identity, all five reference hashes, and an empty
capability list. The result retains
`blocked/production_skills_not_integrated` for capability activation. It does
not prove source/cache identity for the Round 1 source commit.

## Optional directed-reference result

Every result in this section predates the Round 1 source commit and remains
historical. The newest result is bound to the historical candidate named
above; earlier results bind to still earlier revisions.

The newest historical two-call-prompt `DEV137-CODEX-REF-001` run failed closed
at task `pattern-final-owner` with normalized reason
`bulk_reference_content_read` on exact model `gpt-5.6-sol`. The runner exited
`1`; its normalized JSON SHA-256 is
`db9cc39117f47abcea7c2010e13c5ebbfd31064c484b644b1624c5fa5a44f146`.
That newest historical result is authoritative for its candidate and is not
converted to a prerequisite blocker or pass. Exactly one fresh full run was
made from that code; it was not retried. Task 5 was therefore failed/blocking
at that historical head.

The immediately preceding shell-wrapper-hardened run and the pre-wrapper
final-code run before it produced the same task, reason, exit, and normalized
hash. The run before those failed closed at
`fictional-transfer-baton-api` with the same normalized reason, exit `1`, and
normalized JSON SHA-256
`4ddd8f7dae9d2815187fd2c35f31a27606cc949c9d7f49d719ce34e707fa4637`.
The run before it passed all 3/3 cases with exactly one
expected owner reference per task and no unrelated reference read. It exited
`0` with normalized JSON SHA-256
`b4b0182c07e94b62ec0461d434deac1c5dd0c63bef87b2bc7ee1896299afd7e4`.
The review sequence before that pass included a failed confirmation at
`sdk-26-5-transcript` with reason `task_execution_failed`, exit `1`, and
normalized JSON SHA-256
`bc1d51a3abe71c5eb8f49bfa8635d69917c03e3e7a32af153c765d76c81ed024`,
plus an earlier 3/3 pass with the same normalized pass hash. This sequence is
retained candidly; no result was reclassified and no alternate model was
attempted. None of these runs claims workflow activation, production
capability, or DEV-137 completion.

An earlier full probe failed closed at task `sdk-26-5-transcript` with reason
`bulk_reference_content_read`. A normalized diagnostic reproduction showed an
allowed directory discovery followed by the single expected Apple API owner;
it was diagnostic only and is not represented as a pass. The strict
unrelated-content guard was preserved. A still earlier retained run was
`blocked/model_auth_or_task_execution_unavailable` with normalized JSON
SHA-256
`915d49e418c020aec1fa8d7b1fae72b4f588d430a6b50d7e315624bb98bc0b99`.
No alternate model or fallback was attempted.

The runner's 44-case synthetic adversarial suite verifies successful event
pairing, exact canonical root containment, rejection of failed commands,
directories, globs, bulk or unrelated reads, whole-command rejection of shell
dataflow and indirect file-list consumers, signed command and nested-mapping
cwd resolution, fail-closed `bash`/`sh`/`zsh` wrapper handling across positional
and nested payload layouts, an owner-neutral direct-read prompt contract,
closed blocker classification, finally-style executable drift overrides, and
fictional-signature rejection across every agent message before accepting the
final bounded result.

Raw prompts, responses, JSONL, reasoning, tool arguments/results, credentials,
private configuration, literal host paths, and host diagnostics were neither
emitted nor committed. The runner retained them only in process memory and
discarded them before emitting normalized status.

## Host and blocker ledger

| Row | Status | Boundary |
| --- | --- | --- |
| `E-CODEX-LOAD-001` | historical pass at `d27cc16`; current source not run | Structural install/cache only; not current Round 1 evidence |
| `DEV137-CODEX-REF-001` | historical fail / `bulk_reference_content_read` at `pattern-final-owner`; current source not run | Optional explicitly directed reference selection only; never completion evidence |
| `E-CODEX-ACTIVATE-001` / `DEV137-CODEX-PROGRESSIVE-001` | blocked / `production_skills_not_integrated` | Mandatory combined-tip 25-case gate remains blocked |
| DEV-137 issue state | In Progress | Remains blocked until the combined-tip gate passes |
| `E-CLAUDE-LOAD-001` / activation | blocked/deferred_by_owner | Claude not invoked |
| BATS | pass, 3/3 | Existing generator regression |
| pre-commit | blocked/deferred_by_owner | Not invoked |
| markdownlint | blocked/deferred_by_owner | Not invoked |
| Xcode 27 / Evaluations / Instruments | blocked | Current full Xcode is 26.6 (17F113) with SDK 26.5, not Xcode 27 |

## Limitations

The current correction has offline deterministic evidence only. Historical
structural installation/cache equality does not prove the corrected package or
a production workflow activated, and the historical optional directed failure
cannot substitute for the blocked combined 25-case gate. Model behavior is
probabilistic; any future semantic mismatch, unrelated reference read,
fictional API invention, or executable drift remains fail rather than blocked
or pass.
