# DEV-143 Local Apple Foundation Models Bridge Design

Issue: [DEV-143](https://linear.app/devprentice/issue/DEV-143/i5-implement-the-production-apple-foundation-models-local-bridge)

Decision date: `2026-07-21`

Approved direction: user approval (`lgtm`) for the narrow local bridge described
below.

## Purpose and authority

DEV-143 implements the sole production Apple Foundation Models provider boundary
for the DEV-142 `diagnostic-condensation-v1` contract. It accepts one already
completed diagnostic result through a local process interface and returns exactly
one typed terminal result. It does not own host-hook discovery, result
replacement, benchmark measurement, parent fallback, or tool execution.

The immutable authority is:

- `docs/superpowers/specs/2026-07-21-dev-142-runtime-cost-routing-and-benchmark-design.md`;
- `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`; and
- the DEV-128 installed-SDK evidence for `FoundationModels`,
  `SystemLanguageModel`, `LanguageModelSession`, and `@Generable`.

## Selected architecture

The bridge is a standalone Swift package rooted at
`runtime/apple-foundation-models-bridge`. Its executable target is named
`apple-foundation-models-bridge`. It reads exactly one UTF-8 JSON request from
standard input, writes exactly one UTF-8 JSON terminal envelope to standard
output, writes no payloads to standard error, and exits once.

```text
DEV-144 Codex adapter
  -> one DEV-142 request JSON line
  -> apple-foundation-models-bridge
  -> deterministic validation and policy gates
  -> one injected session or FoundationModels session attempt
  -> success | declined | fail JSON line
  -> adapter owns replacement or byte-identical original fallback
```

The executable will be built and invoked with `swift run
apple-foundation-models-bridge`; DEV-144 must capture this command as one
argument vector and must not invoke a shell. Packaging metadata changes are out
of scope unless the final verified Codex plugin-install flow demonstrates that
the runtime cannot be located without them.

## Process protocol

Input is the DEV-142 request schema (`schemaVersion = 1`,
`policyVersion = diagnostic-condensation-v1`, and
`action = condense_diagnostic_output`). The request must contain the stable
request identity, source-tool and command classification, data-policy grant,
input count, original-result digest, exit provenance, and eligible diagnostic
content defined by that schema.

The bridge repeats DEV-142 validation before it creates a session. It rejects
unknown keys, malformed JSON, multiple JSON values, missing or duplicate values,
future versions, unknown data classes, invalid request identity, and invalid
provenance. It declines pre-generation for every DEV-142 eligibility reason,
including non-`Bash` tools, unapproved command class, denied data policy,
input outside 8,192 through 65,536 bytes, estimated savings below 4,096 bytes,
unavailable Apple runtime, unsupported locale, and context occupancy above 75%.

Output uses the DEV-142 result schema with the original request identity and
original-result SHA-256 digest preserved. Its mutually exclusive outcomes are:

- `applied`: validated diagnostic condensation no larger than 4,096 bytes and
  at least 4,096 realized bytes saved;
- `declined`: an expected pre-generation eligibility or availability outcome;
- `fail`: generation, cancellation, deadline, decode, schema, or invariant
  failure.

Every non-`applied` result is a terminal bridge result, not a replacement
instruction. The host adapter preserves its own immutable original bytes and
uses those bytes for fallback.

## Apple session and structured output

`BridgeSession` is a protocol with one asynchronous `condense` operation and a
cancellation/deadline input. `FoundationModelsBridgeSession` is the only
production implementation; it imports `FoundationModels`, checks
`SystemLanguageModel.default.availability`, then creates a
`LanguageModelSession` for one request.

The primary response type is an internal `@Generable` diagnostic condensation
record with only the fields needed by DEV-142: normalized summary, diagnostics,
omitted-warning count, and source provenance. The bridge validates the generated
record after generation against the DEV-142 result rules and byte bounds. If the
installed SDK cannot compile the structured response call, implementation must
use the versioned JSON parser/validator fallback described in the plan and label
the structured-output path `blocked`; it must not invent an API or claim live
structured output.

The session receives only the allowed classified diagnostic content and fixed
instruction text for `condense_diagnostic_output`. It has no tools, network,
provider selection, persistent transcript, arbitrary user prompt, or retry path.

## Failure, privacy, and provenance policy

The bridge maps availability, locale, context, guardrail decline, cancellation,
deadline, generation, decoding, validation, and unexpected errors to the exact
DEV-142 reason-code set. It never includes raw tool output, prompt text, model
output, private path, credential, trace, or Apple diagnostic in the terminal
failure payload or committed proof.

The process may emit normalized diagnostic class and exit code only. It must
leave the request identity, original digest, exit status, command outcome,
interruption state, and approved provenance unchanged. It makes at most one Apple
attempt; uncertainty is terminal `fail`, never an in-bridge retry or a hidden
parent-model fallback.

## Test and proof design

The default Swift test suite injects a deterministic fake `BridgeSession` and
requires no Apple availability, credentials, PCC, network, paid service, device,
or live generation. It covers every DEV-142 decline gate, malformed input,
multiple-input rejection, identity and digest drift, cancellation, deadline,
unavailable runtime, malformed generated record, invalid schema, insufficient
realized savings, and one valid applied result.

Protocol tests run the executable as a child process and assert exactly one JSON
terminal record, no second attempt, bounded standard error, and no raw sensitive
fixture content in committed evidence. `swift test` and `swift build` are the
required deterministic gates; the repository Python, Bats, generator, schema,
fixture, and clean-diff gates remain required at the merged tree.

Live completion proof is a separate opt-in command on supported Apple hardware.
It must show, using only normalized metadata and hashes, one real
`LanguageModelSession` request and one schema-valid bridge response. Missing Apple
Intelligence, compatible hardware, supported OS, entitlement, or stable SDK is
`blocked`; a compile-only or fake-session result cannot satisfy this gate.

## Scope boundaries

DEV-143 may create only the runtime package, its focused Swift tests, protocol
fixtures, and evidence documentation needed to prove the bridge. It must not add
Codex hooks, modify workflow-skill behavior, create a provider abstraction, add
dependencies or remote services, expose generic generation, or change DEV-142
policy values.

DEV-144 consumes this process protocol only after DEV-143 merges. It owns Codex
input parsing, plugin lifecycle installation, replacement mechanics, and Codex
benchmark evidence.
