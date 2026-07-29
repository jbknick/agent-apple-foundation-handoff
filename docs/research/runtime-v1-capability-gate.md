# Runtime V1 successor capability gate

## Verdict

`pass:capability_proven`

Evidence SHA-256:
`1be6addeed48ddceb2e9f398877d1d8307bf35bf41f0372553578d409f3e3b7a`

## Tested boundary

Codex `0.145.0` direct `exec_command` result replacement through one trusted
`PostToolUse` hook, composed with the local SDK 26.5 Apple Foundation Models
bridge. Direct tool mode was enabled, code mode and web search were disabled,
and only the owner-approved C0 stimulus was granted.

## Acceptance mapping

- `plugin_off_baseline`: `pass:untouched_original_observed`
- `direct_fake_applied`: `pass:replacement_observed`
- `composed_live_apple_applied`: `pass:replacement_observed`
- `decline_unapproved_stimulus`: `pass:untouched_original_observed`
- `bridge_malformed`: `pass:untouched_original_observed`
- `bridge_crash`: `pass:untouched_original_observed`
- `adapter_crash`: `pass:untouched_original_observed`
- `hook_timeout`: `pass:untouched_original_observed`

## Proven

- Every row executed the diagnostic command once and made two parent
  provider requests with zero additional parent-model turns.
- The deterministic direct replacement reached the next parent request,
  excluded the original result, and did not spool.
- One real `SystemLanguageModel.default` structured response was observed and
  validated after exactly one Apple attempt.
- The validated Apple condensation reached the next parent request, excluded
  the verbose original result, and did not spool.
- The unapproved stimulus declined before Apple.
- Every malformed, crashed, or timed-out failure row preserved the exact
  untouched original result and applied no replacement.
- All transient workspaces reported complete cleanup, and committed evidence
  contains zero unsafe findings.

## Unproven

- Parent-model token savings were not measured.
- The production Runtime V1 consultation path was not implemented or proven.
- Packaging and release readiness were not evaluated.

## Unblock decision

DEV-253 proves the local successor capability and unblocks DEV-254 only after
the evidence commit passes formal review and exact-head CI, the PR is merged,
the exact resulting `main` push CI succeeds, Linear is completed, and the
repository is synchronized and clean.
