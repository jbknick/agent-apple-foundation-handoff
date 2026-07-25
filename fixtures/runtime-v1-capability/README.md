# Runtime V1 successor capability gate

This fixture is a repository-only proof gate, not a production runtime. It
tests one direct Codex `shell_command` result, one trusted `PostToolUse`
adapter, and one local Apple Foundation Models structured response.

## Trust and execution order

1. Run `--inspect-trust` against the exact captured Codex `0.145.0`
   executable and plugin tree.
2. Review and approve the returned plugin, hook, and C0 stimulus hashes.
3. Persist only that hook hash through `config/batchWrite` and verify a second
   `hooks/list` reports `trusted`.
4. Run `--through direct`; continue only when both rows pass.
5. Run `--through composed`; continue only after one real Apple result passes.
6. Inspect and separately approve the one-second timeout derivative hashes.
7. Run `--through complete`.

The implementation workflow prepares and verifies the harness but does not
invoke `codex exec`; an authorized outer harness must launch the live rows.
Never use a hook-trust bypass flag.

## Fixed boundaries

- Direct `shell_command` mode only; code mode is disabled.
- The loopback Responses endpoint is deterministic and non-generative. It
  performs no network inference and uses no real credential.
- The diagnostic command executes exactly once per row.
- Apple Foundation Models is the only added generation provider.
- A row creates one fresh local session, exposes no tools, and attempts at
  most one structured response.
- Only the owner-approved C0 diagnostic text may enter Apple context.
- The deterministic expected condensation remains outside Apple context.

## Fallback, privacy, and cleanup

A decline or failure emits no hook output. Codex must then send its unchanged
normal result envelope to the parent model without rerunning the command.
Missing host, SDK, compiler, model, hardware, locale, trust, or cleanup is
`blocked`; an invariant violation is `fail`.

Provider bodies, hook input, diagnostics, Apple prompts and responses,
transcripts, configuration, credentials, and private paths remain transient.
Only normalized hashes, counters, statuses, timings, and cleanup state may be
committed. Cleanup failure blocks the row.

A passing capability gate authorizes a separate production plan. It does not
prove parent-token savings and does not authorize production implementation,
packaging, publication, or release.
