# Runtime V1 successor capability gate

## Verdict

`blocked:timed_out`

Evidence SHA-256:
`0839c003aba5a11a3eabfb4488dfbecac0e39e0f5143375f08736d8dcd994ef1`

## Tested boundary

Codex `0.145.0` direct `exec_command` result replacement through one trusted
`PostToolUse` hook, composed with the local SDK 26.5 Apple Foundation Models
bridge. Direct tool mode was enabled, code mode and web search were disabled,
and only the owner-approved C0 stimulus was granted.

## Acceptance mapping

- `plugin_off_baseline`: `pass:untouched_original_observed`
- `direct_fake_applied`: `pass:replacement_observed`
- `composed_live_apple_applied`: `blocked:timed_out`

## Proven

- Each observed row executed the diagnostic command once and made two parent
  provider requests with zero additional parent-model turns.
- The deterministic direct replacement reached the next parent request,
  excluded the original result, and did not spool.
- The live Apple bridge process started and reached the closed timeout outcome.
- The timed-out live row preserved the exact untouched original result,
  applied no replacement, and did not spool.
- The timeout did not establish whether an Apple response attempt began;
  `appleAttempts` is unknown and proves neither zero nor one attempt.
- All transient workspaces reported complete cleanup, and committed evidence
  contains zero unsafe findings.

## Unproven

- A real `SystemLanguageModel.default` structured response was not observed.
- No validated Apple condensation reached the next parent request.
- The live successful-path exclusion of the verbose original result was not
  observed.
- Parent-model token savings were not measured.
- Runtime V1 successor capability was not proven.

## Stop decision

The live Apple row was not retried. The complete fallback matrix was not
started after the composed prerequisite blocked. DEV-254 remains blocked by
the DEV-253 dependency and must not begin.
