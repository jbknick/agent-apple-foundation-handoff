# Runtime V1 successor capability gate

This fixture is a repository-only proof gate, not a production runtime. It
tests one direct Codex `exec_command` result, one trusted `PostToolUse`
adapter, and one local Apple Foundation Models structured response.

## Trust and execution order

1. Run `--inspect-trust` against the exact captured Codex `0.145.0`
   executable and plugin tree.
2. Run a second `--inspect-trust` with `--hook-timeout-seconds 1`.
3. Review and bind all five returned identities under the owner's standing
   approval: the base plugin hash, base hook hash, C0 stimulus hash, timeout
   plugin hash, and timeout hook hash.
4. Persist only the approved base hook hash through `config/batchWrite` and
   verify a second `hooks/list` reports `trusted`.
5. Run `--through direct`; continue only when both rows pass.
6. Run `--through composed`; continue only after one real Apple result passes.
7. Run `--through complete` with the two separately inspected and bound timeout
   identities.

The owner-approved identities for the current DEV-253 evidence run are:

- Base plugin: `651610a480837a7fd684e6357680a4a777d5c1de97f3e00317c32db8a1fa6390`
- Base hook: `sha256:013602f5ba7931ff754954bd69fcd3dd1b01701bfb2ef08171e1592c27ee931b`
- Timeout plugin: `9a793dffff624513e887ac294764ed7cf65c51d4ef8f363c4fcc8343d83b6967`
- Timeout hook: `sha256:ce963851052ea772bca22d782aad103bfc0472c6a35e663be29582933f92ce9d`
- C0 stimulus: `dfb7f1221f87b5450ae6135e980c558b8cd45bacffd77df834a17c673fe4b0c0`

The implementation workflow prepares and verifies the harness but does not
invoke `codex exec`; an authorized outer harness must launch the live rows.
Never use a hook-trust bypass flag.

## Fixed boundaries

- Direct `exec_command` mode only; code mode is disabled.
- The loopback Responses endpoint is deterministic and non-generative. It
  performs no network inference and uses no real credential.
- The diagnostic command executes exactly once per row.
- Apple Foundation Models is the only added generation provider.
- A row creates one fresh local session, exposes no tools, and attempts at
  most one structured response.
- Only the owner-approved C0 diagnostic and locally derived transient C0
  source-fact schema constraints may enter Apple context.
- Neither the diagnostic nor source-fact schema constraints are committed or
  observed as raw evidence.

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
