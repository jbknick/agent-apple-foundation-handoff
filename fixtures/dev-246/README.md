# DEV-246 synthetic Codex capability probe

This fixture tests only whether exact Codex CLI `0.145.0` can prevent an
eligible synthetic Bash result from entering the next parent-model request
while supplying a compact replacement.

The fixture contains no production bridge, user data, credentials, repository
content, or external inference. It uses fixed synthetic sentinels and records
only SHA-256 digests and normalized status metadata.

## Safety and trust

- Run only the captured `0.145.0` executable.
- Use an isolated `CODEX_HOME`.
- Do not copy authentication files into that home without explicit owner
  authorization.
- Review and trust the exact installed hook before execution.
- Do not use transcript content, model prose, hook feedback, or
  `systemMessage` as replacement proof.
- Temporary homes and plugin materialization must be cleaned on every terminal
  path.

## Verdicts

- `pass`: direct next-request evidence contains the compact digest, omits the
  original digest, invokes one hook, and adds no parent-model turn.
- `blocked`: authentication, trust, or direct-boundary evidence is unavailable,
  or the host does not support replacement.
- `fail`: host identity drifts, evidence is malformed, privacy invariants fail,
  or execution cardinality changes.

A blocked or failed verdict keeps DEV-143 and every downstream runtime issue
closed. It authorizes no alternative runtime.
