# DEV-137 reference-library packaging and prerequisite evidence

## Scope and claim boundary

This record covers Task 5 only: structural Codex installation/cache identity
and the optional, explicitly directed reference-selection prerequisite. It is
not workflow-triggered activation, does not satisfy `E-CODEX-ACTIVATE-001` or
`DEV137-CODEX-PROGRESSIVE-001`, and cannot complete DEV-137.

- Reference candidate commit: `d27cc16d62fd0e23e5e62441d17122d622c09492`
- Reference candidate tree: `a8c10274d81690deedd361161a1d4d916b70b72c`
- Source retrieval date: `2026-07-17`
- Codex host: `codex-cli 0.144.5` at normalized `<host-path>`
- Selected model for every Codex execution: `gpt-5.6-sol`
- Model fallback: prohibited and not used
- Claude: not invoked

DEV-137 remains In Progress with blocker
`production_skills_not_integrated` until DEV-136 rebases above DEV-137 and the
mandatory combined-tip Task 6 gate passes.

## Reference payload identity

The structural probe installed eight exact regular files into each fresh
isolated cache and proved the following five reference files byte-identical to
source:

| Reference file | SHA-256 |
| --- | --- |
| `references/apple-api-availability.md` | `a2ddfd157d4c9f48897b7b652d4c71ebb8660104899e1866c1ec64fedec1f8ab` |
| `references/architecture-and-state.md` | `c017fa85bf158d4d25dab292db2ac79773950541f43dce7034aaf0c301e83a68` |
| `references/evaluation-and-observability.md` | `f28a5d4dc32755867d4b8e19030c248ab4cbdc5d0a0773fe3466bc4489c9d0b4` |
| `references/orchestration-patterns.md` | `eaeeed0a33dea4f9af70116d191be5bc9a23ff869ecf26cd4406341687fabbc3` |
| `references/security-context-and-recovery.md` | `1ff0393f68720c79a50b0a7dd488354c995673686c72667aa89f8350e6d1f5c3` |

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
| Cache payload | pass, exactly 8 regular files |
| Relative reference links | pass, 37 occurrences; every reference has an incoming sibling edge |
| Approved official sources | pass, 30 unique links; live audit 1/1 |
| Swift labels | pass, 4 blocks with exactly one allowed visible label each |
| `compiled_sdk_26_5` | pass, 1/1 block type-checked against SDK 26.5 |
| Directed-reference adversarial suite | pass, 38/38 |
| Focused reference/package suite | pass, 20/20 |
| Repository unit suite | pass, 59; the opt-in network row skipped here and passed separately |
| Generated synchronization | pass |
| DEV-130 inherited regression | pass, 7/7 |
| DEV-131 inherited regression | pass, 26/26; corpus 11/11; 8 evidence files |
| BATS | pass, 3/3 |

## Codex structural result

`E-CODEX-LOAD-001` passed twice from fresh isolated homes. The normalized JSON
outputs were byte-identical with SHA-256
`a4b23e4d8744d6f85e36a23a6a927701aefdc8941ed893c145ec27275bf6c465`.
Both runs proved marketplace discovery, installation, enabled state, exact
eight-file source/cache identity, all five reference hashes, and an empty
capability list. The result retains
`blocked/production_skills_not_integrated` for capability activation.

## Optional directed-reference result

The newest final-code `DEV137-CODEX-REF-001` run failed closed at task
`pattern-final-owner` with normalized reason
`bulk_reference_content_read` on exact model `gpt-5.6-sol`. The runner exited
`1`; its normalized JSON SHA-256 is
`db9cc39117f47abcea7c2010e13c5ebbfd31064c484b644b1624c5fa5a44f146`.
That newest result is authoritative and is not converted to a prerequisite
blocker or pass.

The immediately preceding final-code run failed closed at
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

The runner's 38-case synthetic adversarial suite verifies successful event
pairing, exact canonical root containment, rejection of failed commands,
directories, globs, bulk or unrelated reads, whole-command rejection of shell
dataflow and indirect file-list consumers, signed command and nested-mapping
cwd resolution, closed blocker classification, finally-style executable drift
overrides, and fictional-signature rejection across every agent message before
accepting the final bounded result.

Raw prompts, responses, JSONL, reasoning, tool arguments/results, credentials,
private configuration, literal host paths, and host diagnostics were neither
emitted nor committed. The runner retained them only in process memory and
discarded them before emitting normalized status.

## Host and blocker ledger

| Row | Status | Boundary |
| --- | --- | --- |
| `E-CODEX-LOAD-001` | pass | Structural install/cache only |
| `DEV137-CODEX-REF-001` | fail / `bulk_reference_content_read` at `pattern-final-owner` | Optional explicitly directed reference selection only; never completion evidence |
| `E-CODEX-ACTIVATE-001` / `DEV137-CODEX-PROGRESSIVE-001` | blocked / `production_skills_not_integrated` | Mandatory combined-tip gate after DEV-136 rebases above DEV-137 |
| DEV-137 issue state | In Progress | Remains blocked until the combined-tip gate passes |
| `E-CLAUDE-LOAD-001` / activation | blocked/deferred_by_owner | Claude not invoked |
| BATS | pass, 3/3 | Existing generator regression |
| pre-commit | blocked/deferred_by_owner | Not invoked |
| markdownlint | blocked/deferred_by_owner | Not invoked |
| Xcode 27 / Evaluations / Instruments | blocked | Current host is SDK 26.5 Command Line Tools |

## Limitations

Structural installation and cache equality do not prove a production workflow
activated. The newest optional directed probe failed and cannot substitute for
Task 6. Model behavior is probabilistic; any future semantic mismatch,
unrelated reference read, fictional API invention, or executable drift remains
fail rather than blocked or pass.
