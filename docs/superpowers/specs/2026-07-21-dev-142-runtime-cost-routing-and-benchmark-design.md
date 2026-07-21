# DEV-142 Runtime Cost-Routing and Benchmark Contract Design

Issue: [DEV-142](https://linear.app/devprentice/issue/DEV-142/runtime-cost-routing-and-benchmark-contract)

Decision date: `2026-07-21`

Approved direction: the user selected `narrow cross host` and approved the
resulting design with `lgtm`.

## Purpose and authority

This specification defines the deterministic policy and benchmark contract for
the Apple-first diagnostic-condensation chain approved by DEV-130, DEV-131,
and DEV-132:

```text
host PostToolUse adapter
  -> DEV-142 deterministic cost router
  -> DEV-143 local Apple Foundation Models bridge
  -> host-visible result
```

DEV-142 owns the versioned action, host-tool, command-class, data, size,
estimated-savings, response-validation, status, paired-telemetry, correctness,
and release-calculation contracts. It defines deterministic fixtures and a
benchmark corpus, but it adds no runtime hook, host adapter, Swift bridge,
provider, MCP server, command, agent, dependency, or live-model claim.

DEV-143 owns the sole local Swift bridge. DEV-144 owns the Codex adapter.
DEV-145 owns the Claude adapter. Those issues must implement this contract
without widening it. DEV-139 through DEV-141 may integrate proven components
but do not change these semantics.

The exact action remains:

```text
condense_diagnostic_output
```

Apple Foundation Models is the sole MVP local provider. The router begins only
after the original host tool completed. It never reruns that tool and makes no
first-parent-turn savings claim.

## Source and proof boundary

The contract was checked on `2026-07-21` against:

- current official [Codex hooks documentation](https://developers.openai.com/codex/hooks),
  including `PostToolUse`, canonical `Bash` matching, replacement through
  hook feedback, and plugin lifecycle-hook discovery;
- current official [Codex plugin packaging documentation](https://developers.openai.com/codex/plugins/build/),
  including plugin-root `hooks/hooks.json`, plugin trust review, and
  `PLUGIN_ROOT` / `PLUGIN_DATA`;
- current official [Claude Code hooks documentation](https://code.claude.com/docs/en/hooks),
  including `PostToolUse`, `Bash`, `tool_response`, and `updatedToolOutput`;
- the captured local executables Claude Code `2.1.91` and Codex CLI `0.144.5`;
  and
- the installed SDK 26.5 interfaces already pinned by DEV-128.

Current web documentation is architectural authority, not executed evidence
for an older captured host. DEV-144 and DEV-145 must prove their exact adapter
payloads with the captured baseline executable. If a baseline cannot replace a
result through the specified interface, its row is `blocked`; no nearby host
version or current documentation may substitute.

## Selected architecture

Each host adapter performs five bounded stages:

1. capture one completed `Bash` result and its immutable original bytes;
2. parse the command into a versioned command class and construct a request
   from allowlisted trusted-local fields only;
3. apply every deterministic DEV-142 eligibility gate before bridge invocation;
4. make at most one DEV-143 bridge attempt and validate the untrusted response;
5. replace the host-visible result only for `applied`; otherwise return the
   original host-visible result byte-for-byte.

The immutable original bytes are never sent to a parent-model audit channel.
They remain available only to the adapter for exact fallback. Audit and
benchmark evidence contains normalized metadata, classifications, hashes, and
counts; it excludes raw prompts, tool results, model output, private paths,
credentials, traces, and transcripts.

The cost router is a pure decision boundary. It does not execute commands,
inspect the transcript, grant authority, infer data classification, choose a
provider, or own the task's final response.

## Versioned policy identity

The initial policy identity is:

```text
policySchemaVersion = 1
policyVersion = diagnostic-condensation-v1
action = condense_diagnostic_output
resultType = diagnostic_condensation
```

All four values are exact and case-sensitive. Missing, empty, duplicate,
unknown, or future values fail closed. A future policy must use a new
`policyVersion`; it may not silently reinterpret version 1 fixtures or
telemetry.

## Exact host-tool allowlist

The only eligible hook event and canonical tool name are:

```text
hookEventName = PostToolUse
toolName = Bash
```

Aliases, prefix matches, MCP tools, file-edit tools, hosted tools, nested
agents, and unknown tools are ineligible. Host-specific input shapes are
normalized by DEV-144 and DEV-145 before the shared policy runs.

## Narrow cross-host command allowlist

The router recognizes a single POSIX command invocation. It tokenizes without
evaluation and matches an exact executable/subcommand grammar. Version 1
accepts only the unqualified basenames shown below. Absolute or relative
executable paths are rejected even when their basename matches; widening that
surface requires a separately versioned toolchain-identity contract.

The approved command families are:

| Class | Exact approved prefixes |
| --- | --- |
| `test` | `swift test`; `xcodebuild test`; `npm test`; `npm run test`; `pnpm test`; `pnpm run test`; `python3 -m unittest`; `python3 -m pytest` |
| `build` | `swift build`; `xcodebuild build`; `npm run build`; `pnpm build`; `pnpm run build`; `python3 -m build` |
| `typecheck` | `swiftc -typecheck`; `npm run typecheck`; `pnpm typecheck`; `pnpm run typecheck`; `python3 -m mypy` |
| `lint` | `swift format lint`; `npm run lint`; `pnpm lint`; `pnpm run lint`; `python3 -m ruff check` |

The complete version 1 suffix grammar is:

| Prefix family | Allowed suffix after the exact prefix |
| --- | --- |
| `npm` / `pnpm` | No additional token. In particular, no `--` passthrough. |
| `swift test` | Zero or more uniquely occurring pairs from `--configuration debug|release`, `--package-path <repo-dir>`, `--scratch-path <repo-dir>`, and `--filter <safe-selector>`, in any order. |
| `swift build` | Zero or more uniquely occurring pairs from `--configuration debug|release`, `--package-path <repo-dir>`, and `--scratch-path <repo-dir>`, in any order. |
| `swiftc -typecheck` | One or more `<swift-source>` operands and no option. |
| `swift format lint` | Optional `--recursive`, optional `--strict`, then one or more `<repo-path>` operands. Each option occurs at most once. |
| `xcodebuild test` / `xcodebuild build` | Zero or more uniquely occurring options from `-project <xcodeproj>`, `-workspace <xcworkspace>`, `-scheme <safe-selector>`, `-configuration Debug|Release`, `-sdk <safe-selector>`, `-destination <safe-selector>`, `-derivedDataPath <repo-dir>`, and `-quiet`, in any order. `-project` and `-workspace` are mutually exclusive. |
| `python3 -m unittest` | Empty; or one or more `<python-test-id>` values; or `discover` followed by zero or more uniquely occurring pairs from `-s <repo-dir>`, `-p <safe-glob>`, and `-t <repo-dir>`. A single `-v` or `-q` may precede any of those forms. |
| `python3 -m pytest` | Zero or more uniquely occurring flags from `-q`, `-v`, `-x`, `--maxfail=<positive-integer>`, `-k <safe-expression>`, and `-m <safe-expression>`, followed by zero or more `<python-test-path>` operands. |
| `python3 -m build` | Empty, `--sdist`, `--wheel`, or both flags once in either order. |
| `python3 -m mypy` | Optional `--strict`, optional `--no-incremental`, then one or more `<repo-path>` operands. Each option occurs at most once. |
| `python3 -m ruff check` | Optional `--no-fix`, optional `--output-format concise|full`, then one or more `<repo-path>` operands. `--fix`, `--unsafe-fixes`, and every other token are rejected. |

Grammar terminals are closed:

- `<repo-path>` is a normalized, nonempty, NUL-free relative path whose real
  target or nearest existing parent remains beneath the captured repository
  root; it contains no `.` or `..` segment.
- `<repo-dir>` is a `<repo-path>` whose resolved target is a directory, or a
  not-yet-created derived-data/scratch directory with a contained existing
  parent.
- `<swift-source>` is a contained regular `<repo-path>` ending in `.swift`.
- `<xcodeproj>` and `<xcworkspace>` are contained `<repo-path>` values ending
  in `.xcodeproj` and `.xcworkspace`, respectively.
- `<python-test-path>` is a contained `<repo-path>`, optionally followed by a
  pytest `::` selector whose components match `[A-Za-z_][A-Za-z0-9_]*`.
- `<python-test-id>` is one or more dot-separated identifiers matching
  `[A-Za-z_][A-Za-z0-9_]*`.
- `<safe-selector>` is 1-128 characters from ASCII letters, digits, space,
  `_`, `-`, `.`, `,`, `=`, `:`, `/`, `[`, and `]`, with no leading or trailing
  space.
- `<safe-expression>` is 1-128 characters from ASCII letters, digits, space,
  `_`, `-`, `.`, `(`, `)`, and `:`, with balanced parentheses and no leading
  or trailing space.
- `<safe-glob>` is 1-128 characters from ASCII letters, digits, `_`, `-`, `.`,
  `*`, and `?`; it contains no path separator.

After POSIX tokenization, options and their values remain distinct tokens
except the exact `--maxfail=<positive-integer>` form. Duplicate options,
missing values, empty operands, tokens outside this grammar, or filesystem
identity drift decline. The parser does not expand globs, environment values,
or shell syntax.

Version 1 always rejects:

- blank, multiline, or invalidly quoted commands;
- `;`, `&&`, `||`, pipes, redirections, backgrounding, here documents,
  subshells, command substitution, process substitution, or shell expansion;
- leading assignments and wrappers including `env`, `timeout`, `sudo`,
  `xargs`, `sh -c`, `bash -c`, and `zsh -c`;
- `cd`, directory-changing command chains, script aliases outside the four
  exact package-script names, and unrecognized flags or operands;
- absolute input paths that cannot be proven inside the repository boundary;
  and
- any command whose class cannot be selected from trusted tokens alone.

Rejecting a command is an expected `declined` outcome. The router never tries
to prove safety by executing or partially evaluating the command.

## Canonical request envelope

An eligible adapter constructs one request with:

```text
schemaVersion
policyVersion
callID
toolName
toolVersion
stateVersion
action
commandClass
originalResultType
originalResultDigest
exitStatus
interrupted
inputBytes
estimatedSavingsBytes
fields[]
```

`exitStatus` is an integer from 0 through 255 or `null`; it is `null` only
when the host reports an interrupted command without a numeric status.
`interrupted` is a boolean. The response must reproduce both values exactly.
`inputBytes` and `estimatedSavingsBytes` are nonnegative integers recomputed by
the bridge and response validator rather than trusted from model output.

`fields[]` admits only the DEV-130 names:

```text
severity
code
message
file
line
column
```

Each field carries a typed `trustedLocal` origin plus C0 or C1 classification,
purpose, Apple-on-device destination, retention, and redaction state. Command
class, exit status, interruption status, field counts, and request bindings are
control metadata, not free-form diagnostic content.

File values sent to Apple are normalized repo-relative paths. Absolute paths,
paths that escape the repository, symlink-ambiguous paths, private host paths,
and fields whose origin or classification cannot be proven make the whole
route decline. Version 1 never silently drops an unknown, unclassified,
disallowed, or mixed-provenance diagnostic field. Only byte ranges recognized
by a closed deterministic parser as explicitly discardable formatting noise
may be omitted before field construction; the parser records their byte count
and they may contain no non-whitespace text.

## Data-policy gate

Only C0 public or C1 task-private trusted-local diagnostics are eligible. C2,
C3, unknown, mixed-provenance, remote, provider-derived, transcript-derived,
or unclassified fields decline before Apple invocation.

The preflight scanner rejects credentials, signing material, tokens, private
keys, secrets, unrelated third-party data, raw environment values, and literal
private paths. Redaction is not permission: a redacted field must still have an
allowlisted name, trusted-local origin, approved purpose, Apple-on-device
destination, bounded retention, and current policy version.

The Apple response cannot broaden this grant or authorize replacement.

## Size, savings, and Apple budget gates

All byte counts use the exact UTF-8 encoding of the canonical allowlisted
diagnostic content, not the enclosing host JSON.

Version 1 uses these exact bounds:

```text
minimumInputBytes = 8192
maximumInputBytes = 65536
maximumCondensedBytes = 4096
minimumEstimatedSavingsBytes = 4096
minimumRealizedSavingsBytes = 4096
maximumAppleResponseTokens = 1024
maximumAppleContextOccupancy = 0.75
```

The request declines before Apple invocation when its eligible content is
below 8 KiB or above 64 KiB. Before bridge invocation, the router computes:

```text
estimatedSavingsBytes = inputBytes - maximumCondensedBytes
```

The subtraction uses checked unsigned arithmetic. Underflow, overflow, a
non-integer input, or `estimatedSavingsBytes < 4096` declines. The exact 4096
boundary is eligible. This is the version 1 minimum estimated-savings gate;
the post-generation realized-savings gate remains independently required.
Version 1 does not chunk, truncate, sample, or make multiple model calls.

Before generation, DEV-143 must count the request, instruction, schema, and
reserved response tokens with the installed Apple API. Their sum must be less
than or equal to `floor(contextSize * 0.75)`. A missing context size, token
count, locale, availability result, or arithmetic input declines. Architecture
family labels such as "SDK 26.x" do not satisfy this executed gate.

After generation, the serialized canonical result must be at most 4 KiB and at
least 4 KiB smaller than the original eligible content. Otherwise the result
is invalid for replacement and the original host result is preserved.

These byte gates establish deterministic eligibility and realized contraction;
they do not prove parent-provider token savings. Only paired provider telemetry
may prove the release cost claim.

## Response and correctness contract

The untrusted bridge response binds:

```text
schemaVersion
policyVersion
callID
toolName
toolVersion
stateVersion
action
commandClass
originalResultType
originalResultDigest
resultType
outcome
exitStatus
interrupted
summary
diagnostics[]
warningCount
omittedWarningCount
```

Every request binding must match exactly. `resultType` must equal
`diagnostic_condensation`. The response is rejected for unknown keys where the
schema is closed, invalid types, duplicate diagnostic identities, unsupported
severity, invented paths, or a mismatched command outcome.

A correct condensation preserves:

- the command class, success/failure outcome, exit status, and interruption;
- every distinct fatal and error diagnostic, including code, message,
  repo-relative file, line, and column when present;
- failed test identifiers and the final test/build/typecheck/lint summary;
- the total warning count and actionable representatives of distinct warnings;
  and
- enough provenance to bind the result to exactly one original tool call.

Fatal and error diagnostics may be de-duplicated only when all preserved fields
match. They may not be omitted. If all fatal/error diagnostics and required
summary data cannot fit within the output bounds, the route declines. Warnings
may be deterministically de-duplicated after fatal/error preservation, with
exact `warningCount` and `omittedWarningCount` values.

The bridge may summarize wording but may not invent a cause, fix, file, symbol,
test, count, status, or next action. Model output alone never proves
correctness; the deterministic validator and paired benchmark scorer own that
decision.

## Host replacement and fallback

On `applied`, DEV-144 and DEV-145 render the validated canonical result into
their host's documented tool-result shape. The rendered result contains no raw
Apple rationale and no unvalidated field.

Claude targets the currently documented `updatedToolOutput` path while
preserving the required Bash response object shape. Codex targets the currently
documented `PostToolUse` replacement feedback path. Current official Codex
documentation describes `continue: false` replacement, but neither target is
baseline-proven here. DEV-144 and DEV-145 must prove the exact `0.144.5` and
`2.1.91` payloads and ensure normal parent work continues without an extra
parent turn or nested-code rejection.

For every `declined`, `fail`, cancellation, timeout, invalid Apple response,
host-output mismatch, or replacement-unavailable branch, the parent sees the
immutable original result byte-for-byte. A bounded normalized reason is
recorded only in metadata; it is not prepended or appended to the fallback.
No branch reruns the original tool or makes a second bridge attempt.

## Exact status semantics

Per-invocation status is one of:

| Status | Meaning |
| --- | --- |
| `applied` | All gates passed, one Apple attempt produced a valid result, realized savings passed, and the baseline host replaced the original exactly once. |
| `declined` | An expected eligibility, availability, data, size, savings, or model-decline gate preserved the original without claiming a defect. |
| `fail` | A contract invariant, adapter, validator, bridge, or replacement operation malfunctioned; the original was still preserved. |

Benchmark-row status may additionally be `blocked` when a required captured
host, exact baseline version, SDK/module/model availability, provider usage,
authentication, or normalized telemetry prerequisite is absent. `blocked` is
not an invocation status and is never converted to a pass, skip, decline, or
zero-valued measurement.

Reason codes are versioned enums. Version 1 includes at least:

```text
tool_not_allowed
command_not_allowed
compound_command
data_policy_denied
input_below_minimum
input_above_maximum
apple_unavailable
locale_unsupported
context_budget_exceeded
generation_declined
cancelled
deadline_exceeded
invalid_response
insufficient_realized_savings
host_replacement_unavailable
host_replacement_failed
contract_invariant_failed
```

Unknown reason codes fail schema validation.

## Deterministic fixture corpus

DEV-142 owns 24 eligible synthetic benchmark fixtures: one success and one
failure representative for twelve selected command forms, with three command
forms in each of `test`, `build`, `typecheck`, and `lint`. The selected forms
span Swift/Xcode, npm/pnpm, and Python. Parser contract tests separately cover
every approved prefix and every rejection family, so benchmark sampling does
not weaken allowlist coverage.

Eligible fixtures are 8-64 KiB after canonical field selection and include:

- repeated noise that may be removed;
- unique fatal/error diagnostics that must survive;
- file/line/column, code, failed-test, exit, and interruption variants;
- repeated and distinct warnings with exact counts; and
- Unicode cases whose byte and token counts differ materially.

Invalid/fallback fixtures cover every data, size, command, context, response,
savings, cancellation, timeout, and host-replacement gate. Boundary rows cover
exactly 8191/8192 and 65536/65537 input bytes, 4096/4097 output bytes, 4095/4096
realized savings bytes, and the 75% Apple occupancy edge.

Fixtures contain synthetic data only. Each fixture and expected normalized
result is hash-bound. Runtime or live-host evidence may commit only normalized
metadata after DEV-131 path, content, structured-key, classification, and hash
scans pass.

## Paired cost and correctness benchmark

Each eligible workflow runs two otherwise identical arms:

```text
pluginOff
pluginOn
```

Pair identity binds workflow, fixture, parent model, provider, provider
normalization version, host version, toolchain, policy version, and command
class. A mismatch blocks the pair.

Each arm records null-capable normalized fields for provider-reported input,
cached-input, output, reasoning, total parent-model tokens, parent turns,
Apple attempts, replacements, declines, fallbacks, latency, and correctness.
Plugin-off Apple attempts and replacements must be zero. Plugin-on may make at
most one Apple attempt for an eligible original result.

Version 1 has exactly two provider normalization identities:

```text
openai-responses-usage-v1
anthropic-messages-usage-v1
```

For `openai-responses-usage-v1`, provider `input_tokens` already includes its
cached-input subset and `output_tokens` already includes its reasoning subset:

```text
inputTokens = input_tokens
cachedInputTokens = input_tokens_details.cached_tokens
outputTokens = output_tokens
reasoningTokens = output_tokens_details.reasoning_tokens
totalParentModelTokens = inputTokens + outputTokens
```

`cachedInputTokens <= inputTokens` and `reasoningTokens <= outputTokens` are
required. The subset fields are reported but never added a second time.

For `anthropic-messages-usage-v1`, cache-read and cache-creation tokens are
provider-reported input categories outside `input_tokens`; thinking is already
charged within `output_tokens` and is not exposed as a separately additive
normalized field:

```text
inputTokens = input_tokens
cachedInputTokens = cache_read_input_tokens + cache_creation_input_tokens
outputTokens = output_tokens
reasoningTokens = null
totalParentModelTokens = inputTokens + cachedInputTokens + outputTokens
```

Every source field is a nonnegative integer and every addition uses checked
unsigned arithmetic. If the named provider does not expose the required source
fields for both arms, changes their semantics, or exposes a reasoning category
that is neither a documented subset nor separately normalizable, the pair is
`blocked`. Provider estimates, local tokenizers, byte conversions, and inferred
cache values are prohibited.

Savings apply only to parent-model consumption after `PostToolUse`. Apple-local
tokens and latency are reported separately and excluded from the parent-token
reduction numerator and denominator. Discovery, installation, activation,
bytes, mock token counts, or local Apple tokens cannot substitute for provider
usage.

For each valid pair:

```text
reduction =
  (pluginOff.totalParentModelTokens - pluginOn.totalParentModelTokens)
  / pluginOff.totalParentModelTokens
```

The required matrix is the Cartesian product of the 24 eligible fixtures and
the two captured baseline hosts, for exactly 48 valid pairs and 96 arms. The
release gate is the conjunction of:

```text
validRequiredPairs = 48
blockedRequiredPairs = 0
median(reduction across valid eligible pairs) >= 0.10
correctnessRegressions = 0
additionalParentModelTurns = 0
```

A zero or missing plugin-off denominator, missing provider field, normalization
mismatch, invalid arm, or unavailable required host makes that pair `blocked`.
It is never dropped from the required matrix or imputed as zero. Extra
exploratory pairs are reported separately and never enter the release median.

Correctness compares the plugin-on parent outcome with both the fixed expected
answer and its paired plugin-off outcome. The scorer checks command outcome,
all required fatal/error identities, failed tests, actionable next step, no
invented facts, and final task completion. A shorter answer is not inherently
correct.

## Validation ownership

DEV-142 implementation must add only contracts, schemas, fixtures, deterministic
validators/scorers, and documentation required to freeze this design. Its tests
must prove:

- policy identity, closed enums, and exact action;
- all allowed and rejected host-tool/command cases;
- data, byte, Apple-context, realized-savings, and response-binding gates;
- immutable fallback and at-most-one-attempt/no-rerun invariants;
- 24 eligible fixtures plus complete invalid/boundary fixtures;
- paired normalization, median calculation, correctness, parent-turn, and
  blocker semantics; and
- repository generation, privacy, scope, and normalized-evidence boundaries.

DEV-142 does not claim a live Apple result, installed runtime hook, host result
replacement, or provider cost reduction. DEV-143 through DEV-145 must reuse the
same fixture hashes and policy version; changing fixtures to accommodate an
implementation defect is not permitted.

## Explicit non-goals

Version 1 does not add:

- chunking, streaming, sampling, recursive condensation, or multiple Apple
  attempts;
- generic provider abstractions, cloud models, PCC, GLM, Kimi, local
  OpenAI-compatible servers, credentials, paid services, or network calls;
- arbitrary shell interpretation, broad ecosystem aliases, Cargo, Go, .NET,
  Yarn, Bun, custom package-script names, or user-defined command patterns;
- transcript inspection, task routing, final-response ownership, effect
  authorization, confirmation, or tool execution;
- raw live prompts, results, rationales, traces, `.xcresult`, or private host
  state in committed evidence; or
- release, publish, merge, tag, or semantic-version changes.

Any future expansion requires a separately reviewed policy version, fixture
amendment, threat-model review, and paired acceptance proof.
