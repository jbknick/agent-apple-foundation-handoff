# Runtime V1 benchmark contract

`codex-runtime-v1-cost-v1` is the independent Codex-only release contract for
the merged Runtime V1 plugin. It requires exactly 24 fixture pairs and 48 arms
using Codex `0.145.0`, `gpt-5.6-sol`, medium reasoning, and
`openai-responses-usage-v1`.

Each arm is bound to one exact immutable DEV-142 corpus ID, rendered SHA-256,
command class, and command form. It accepts only the five exact
`turn.completed.usage` keys. Cache-read, cache-write, and reasoning values are
validated as subsets. Cache-write is recorded separately; neither cache subset
is added to provider input, and reasoning is not added to provider output.
Parent usage is exactly `input_tokens + output_tokens`, normalized by the
read-only DEV-142 helper.

The release gate accepts only 24 closed raw arm pairs. It revalidates and
scores every pair itself; caller-supplied pair summaries have no authority.
It passes only with the exact corpus ID set, a median reduction of at least
100,000 PPM, zero correctness regressions, added parent requests or turns,
command reruns, cleanup failures, and unsafe committed-evidence findings,
plus at least one real Apple attempt and one validated applied row. Missing,
extra, substituted, duplicate, blocked, zero-denominator, schema-drift, or
cleanup-incomplete input blocks. A correctness or operational invariant
violation fails.

This fixture is deterministic and offline. It runs no Codex or Apple process
and stores no prompts, responses, reasoning, diagnostics, credentials, raw
events, provider bodies, Apple bodies, or private paths. Live execution and
the complete normalized evidence envelope belong to the authorized outer
harness. Closed evidence is valid only when its 48 raw arms rederive its exact
pair summaries, release object, counts, status, and reason codes.
