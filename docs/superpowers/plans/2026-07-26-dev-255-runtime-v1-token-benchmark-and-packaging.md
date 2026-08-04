# DEV-255 Runtime V1 Token Benchmark and Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the merged production Runtime V1 reduces actual parent-model usage by at least 10% median across 24 required pairs without correctness regressions, extra turns, reruns, unsafe evidence, or unsupported packaging.

**Architecture:** Keep DEV-142's historical two-host benchmark immutable and add one separate Codex-only `codex-runtime-v1-cost-v1` validator. An authorized outer harness runs identical plugin-off/plugin-on tasks through the merged production plugin, validates the exact Codex `turn.completed.usage` contract, maps it into DEV-142's existing `openai-responses-usage-v1` oracle without double counting subsets, scores correctness and operational invariants, and writes only closed normalized evidence.

**Tech Stack:** Python 3 standard library and `unittest`; merged DEV-254 Codex plugin; Codex CLI `0.145.0`; Swift 6.3.3; macOS SDK 26.5; actual Codex/provider usage; JSON and SHA-256.

**Linear issue:** [DEV-255](https://linear.app/devprentice/issue/DEV-255/v2-prove-runtime-v1-token-reduction-and-packaging-readiness)

**Spec source:** `docs/superpowers/specs/2026-07-26-runtime-v1-successor-linear-backlog-design.md`

**Blocked by:** DEV-254.

---

## Predecessor assumptions and mandatory refresh

DEV-254 is merged at `6d336044b0c21dfeca485b6676a18d50bf085487` and this plan was refreshed against that production manifest, hook, Python adapter, Swift bridge, production harness, DEV-142 corpus, and DEV-142 usage normalization. Before implementation, recheck that this commit remains an ancestor of `HEAD`, DEV-254 is complete in Linear, and the paths below remain unchanged. The benchmark contract is:

```text
one production Codex plugin
one direct Bash command per arm
pluginOff appleAttempts = 0
pluginOn appleAttempts <= 1
no command rerun
exactly two normal parent requests and one completed parent turn per arm
gpt-5.6-sol with medium reasoning
exact Codex 0.145.0 turn.completed.usage fields
closed normalized evidence only
```

The verified Codex `0.145.0` plugin-off dry row used an isolated `CODEX_HOME`,
`gpt-5.6-sol`, medium reasoning, one completed turn, and completed cleanup. Its
terminal event is exactly:

```json
{
  "type": "turn.completed",
  "usage": {
    "input_tokens": 0,
    "cached_input_tokens": 0,
    "cache_write_input_tokens": 0,
    "output_tokens": 0,
    "reasoning_output_tokens": 0
  }
}
```

The zeroes above show types only; live values must be provider-reported
nonnegative integers. Official `rust-v0.145.0` source establishes that
`input_tokens` is the provider input total, cached-input and cache-write input
are subsets of that input total, reasoning output is a subset of output, and
total parent usage is `input_tokens + output_tokens`.

The captured Codex subprocess stderr has one closed, source-bound exception.
For exact Codex `0.145.0` and official source commit `25af12f7`, compare the
completed subprocess stderr as bytes before parsing or using stdout, OTel, or
any other arm artifact. Accept only `b""` or the exact 39-byte
`b"Reading additional input from stdin...\n"` notice. The nonempty alternative
is permitted only for the source-defined `OptionalAppend` path when stdin is
non-terminal. Do not decode, trim, normalize newlines or whitespace, strip
ANSI escapes, or accept prefixes, suffixes, repetition, or multiple lines.
After the exact comparison, immediately discard the raw stderr buffer; retain
at most the normalized `stderrBytes` value `0 | 39`. Any other stderr bytes
block the preflight or arm as `blocked:codex_stderr_unclassified`. A Codex
version or source-commit change invalidates this exception and requires a plan
refresh before any provider-backed row.

Map the five Codex fields into DEV-142 without changing DEV-142:

```python
dev142_usage = normalize_usage("openai-responses-usage-v1", {
    "input_tokens": usage["input_tokens"],
    "cached_tokens": usage["cached_input_tokens"],
    "output_tokens": usage["output_tokens"],
    "reasoning_tokens": usage["reasoning_output_tokens"],
})
cache_write_input_tokens = usage["cache_write_input_tokens"]
```

Require the exact five usage keys, exact `int` values (not `bool`) in
`0..2**64-1`, `cached_input_tokens <= input_tokens`,
`cache_write_input_tokens <= input_tokens`, and
`reasoning_output_tokens <= output_tokens`. Cache-read and cache-write are each
validated as subsets; do not assume they are disjoint and do not add either to
the provider input total. Do not add reasoning output to output. Record
cache-write separately in normalized arm evidence and require DEV-142's
`total_parent_model_tokens == input_tokens + output_tokens`.

Missing or extra keys, a non-integer/negative/overflowing value, a violated
subset, a mapping mismatch, multiple/missing terminal events, or a changed
event shape stops preflight with
`blocked:provider_usage_schema_or_semantic_drift`. Missing telemetry is a
blocker, never estimated. Any later merged production, Codex schema, or
normalization drift requires another Sol/High plan refresh.

## 2026-07-29 Task 3 observation-boundary amendment

Formal review confirmed that the production adapter already derives closed
`consultation_completed` and `replacement_emitted` events, but its executable
path passes `observe=lambda _value: None`. The current Task 3 runner therefore
cannot truthfully derive `appleAttempts`, a replacement-prepared application
fact, or Apple/hook latency and correctly stops with
`blocked:apple_attempt_counter_unobservable`. Task 3 is incomplete until that
production observation prerequisite and the remaining outer-runner gaps below
are closed; no counter may be inferred from plugin installation, hook trust,
process completion, replacement text, or model output.

Standing DEV-255 approval authorizes Task 3 implementation changes only in
these four paths:

```text
plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py
tests/test_runtime_v1_production.py
tests/e2e/codex_runtime_v1_benchmark.py
tests/test_codex_runtime_v1_benchmark.py
```

It also authorizes mechanically refreshing the exact
`productionPluginSha256` and `pythonAdapterSha256` values bound in the runner
and tests after those reviewed bytes change. The Codex manifest, hook manifest,
Swift source, generated runtime contract, DEV-142 fixtures/contracts/evidence,
and every other production path remain unchanged. This approval does not
authorize a live Codex or Apple run, evidence publication, commit, push, merge,
tag, release, or a second Apple attempt.

The Sol/High decision for the remaining effect-proof boundary is to accept
rigorous non-body triangulation. A direct live second-request body hash is not
required and must not be captured: Codex `0.145.0` preserves the original
`PostToolUseFeedbackOutput` in JSONL and `log_preview`, applies the hook
replacement only through `to_response_item`, and intentionally excludes bodies
from the authorized OTel request counter. The model-authored last message is
also not effect authority. Instead, the outer runner may derive
`validated_applied = true` only from all of these independently owned facts:

```text
application observation status = replacement_emitted
application observation appleAttempts = 1
application observation appleValidResults = 1
current-candidate Codex 0.145.0 local-provider forwarding preflight = pass
live OTel normal parent requests = 2
live JSONL completed parent turns = 1
live JSONL command executions = 1
live final parent outcome DEV-142 score = pass
```

The current-candidate preflight must use the captured Codex `0.145.0`
executable and exact installed production bytes. With only synthetic transient
content, its local provider records that the current adapter's exact stdout
replacement SHA-256 is the only `function_call_output` in request two, the
original tool-result bytes are absent from the whole second request, and
exactly two `/responses` requests and one completed turn occur. It deletes both
request bodies before returning a closed
normalized pass/block result. Existing DEV-253 production-mechanism evidence is
a predecessor check, not a substitute for this current-byte proof. Any Codex
source, executable, candidate, plugin-tree, hook, adapter, or forwarding-preflight
identity drift blocks every applied row.

This is intentionally a composite application proof, not a claim that OTel
observed a provider body. For the configured benchmark path only, the adapter
must serialize the already validated closed hook response once, write all of
those exact bytes to stdout, flush successfully, and only then durably write
the terminal `replacement_emitted` receipt containing the same SHA-256 and byte
count. No fallible mutation or recheck may occur after that receipt. A receipt
failure cannot roll back the already emitted consultation and must not be
reported as a consultation decline or fallback; it blocks measurement and
evidence for the arm. A stdout, receipt, request-count, turn, cleanup, or
parent-outcome failure therefore prevents the outer arm from deriving
`validated_applied`.

## 2026-07-29 blocked forwarding-preflight diagnosability amendment

The clean current-candidate forwarding preflight stopped before any Apple,
remote-provider, dry-row, or benchmark-arm attempt with the required public
terminal `status = blocked` and
`reason = replacement_forwarding_unproven`. That public status and reason
remain unchanged. The runner must not retry the preflight, retain raw evidence,
or weaken any forwarding assertion.

The normalized forwarding-preflight result may add one optional
`failureStage`. It is forbidden on a passing result, required when the public
result is `blocked:replacement_forwarding_unproven`, and has this exact closed
enum:

```text
preflight_setup
process_execution
provider_teardown
observation_cleanup
process_stderr
process_exit
jsonl
request_count
direct_tool_contract
function_output
command_counter_presence
command_counter_value
original_exclusion
receipt
identity_trust
unexpected_exception
```

Set the pending stage immediately before entering its boundary:
`preflight_setup` covers isolated-root creation and the synthetic bridge,
observation, command-counter, environment, and local-provider setup outside an
identity/trust boundary; `identity_trust` supersedes it during initial
installation/trust and the final identity/trust rechecks, and
`preflight_setup` is re-entered after initial trust; `process_execution` covers
the exact exec-argument construction and one subprocess invocation, including
spawn errors and timeout; `provider_teardown` covers local-provider context
exit after the subprocess returns; `observation_cleanup` covers observation
file and directory deletion after receipt validation and immediate buffer
discard; `process_stderr` covers only the source-bound raw-stderr
classification and immediate discard; `process_exit` covers the accepted-
stderr process return code; `jsonl` covers the closed event stream and usage
parser, including completed-turn and command counts; `request_count` covers
the exact two-request count before direct-tool validation;
`direct_tool_contract` covers direct-tool request shape and availability;
`function_output` covers only the validator's stable
`provider_request_invalid` failure after the request count passes;
`command_counter_presence` covers
the command-counter file presence check; `command_counter_value` covers its
exact value;
`original_exclusion` covers the unique forwarded function output and
whole-second-request original exclusion; and `receipt` covers exact wrapper
serialization plus the application observation status, digest, and byte-count
cross-check. A caught exception outside a classified boundary maps only to
`unexpected_exception`; never retain or serialize its type, message,
traceback, arguments, or chained exception.

`blocked:cleanup_incomplete` remains the separate cleanup terminal and does not
use `failureStage`. Cleanup still runs after every pass or block and can
supersede an earlier pending forwarding block. The normalized diagnostic may
retain only `failureStage` plus the already authorized path-free bounded
identity/status scalars. It must not retain or expose prompts, responses,
reasoning, paths, provider request bodies, stdout, stderr, JSONL, command
output, observation content, exception text, or digests derived from any of
those prohibited bodies.

Add deterministic runner tests that force every closed stage once, prove the
public status and reason remain exactly
`blocked:replacement_forwarding_unproven`, prove no retry, and prove the
matching `failureStage` is the only added diagnostic. Force an otherwise
unclassified exception and require `unexpected_exception` without its message.
Force cleanup failure separately and require
`blocked:cleanup_incomplete` with no `failureStage`. Scan every normalized
terminal serialization and test artifact for prompt, response, private-path,
request-body, stdout, stderr, JSONL, command-output, observation, traceback,
and exception-message leakage.

## 2026-08-02 one-time superseding native-host amendment

The clean `ed9f5f22dba931639ec153e97afcebbb95f49744` usage dry run captured the
Codex `0.145.0` npm JavaScript launcher and stopped at the forwarding
preflight with `blocked:replacement_forwarding_unproven` and
`failureStage = process_stderr`. That terminal remains nonpassing and must
not be relabeled, deleted, or used as release evidence. It may be superseded
solely for DEV-255 release and forward progress by committing this amendment
to a new clean candidate, capturing the different exact native
`vendor/aarch64-apple-darwin/bin/codex` executable from the same pinned
package, requiring its strict single-line version to remain `0.145.0`, and
running exactly one superseding `--through usage-dry-run` invocation.

This is a new host identity row, not a retry within the prior invocation. Both
normalized terminals remain in Linear history; retain no raw stderr or other
prohibited evidence. Neither invocation may retry its forwarding preflight or
original command. The prior row made no Apple attempt or benchmark-arm run,
and the superseding row must still stop before either unless its dry run
passes. Any non-pass from the superseding invocation is terminal: do not retry
it, substitute another host executable, or rerun a benchmark arm. No runner,
production, fixture, or test code change is required because the existing
exact-executable capture accepts the newly supplied native path; this
amendment and the resulting clean candidate identity are the complete change
boundary.

## 2026-08-02 forwarding-preflight ambient-log-filter root-cause amendment

The JavaScript-launcher, native-host, and subsequent PTY differential rows
remain separate nonpassing `blocked:replacement_forwarding_unproven` terminals
with `failureStage = process_stderr`. They must not be relabeled, deleted,
retried, or used as release evidence. The PTY row falsified terminal mode as a
sufficient correction. Raw stderr remained immediately discarded and was not
inspected or retained.

Pinned Codex `0.145.0` source commit `25af12f7` proves the causal configuration
edge: `codex-rs/exec/src/lib.rs` calls `EnvFilter::try_from_default_env()` before
falling back to the quiet `EXEC_DEFAULT_LOG_FILTER`. The current host check
proved only that the `RUST_LOG` key is present; its value and content were not
read, retained, or serialized. The forwarding preflight constructed its row
environment with `{**os.environ, **environment, ...}`, and every actual
benchmark arm began with `dict(os.environ)`, while the validated production
`_run_row` starts from `dict(environment)` and adds only approved row variables.
An uncontrolled ambient logging configuration therefore crossed into every
controlled Codex child and could override Codex's quiet exec filter. That
environment-boundary violation is the proven root bug; the prior stderr
contents and exact emitter remain unknown.

Correct the shared root boundary by replacing every ambient environment copy
with one explicit controlled baseline that reads only host `PATH` and sets
`NO_COLOR = 1`, `PYTHON_COLORS = 0`, and `PYTHONDONTWRITEBYTECODE = 1`. Build
the forwarding preflight and every actual arm from that baseline plus only the
isolated install, fixture, observation, OTel, and other explicit approved row
variables. Revert the falsified PTY differential to the original
`subprocess.DEVNULL` stdin and `stdin_nonterminal = True`. Keep stdout and
stderr captured and keep the exact source-bound classifier unchanged. Add
deterministic regressions that inject ambient `RUST_LOG` and an unrelated
unapproved sentinel and prove neither reaches either the preflight subprocess
or the actual arm's `invoke_with_otel_counter` boundary, while required
isolated keys and explicit controls remain present. Do not inspect raw stderr,
broaden accepted stderr, change forwarding or request assertions, retry an old
row, or add an executable identity.

After focused and full deterministic gates plus a formal high-reasoning review
pass on a new clean candidate, run exactly one new native
`--through usage-dry-run` invocation using the already approved exact Codex
`0.145.0` identity. This is a new root-cause-fix candidate row, not a retry or
substitution within any prior terminal row. Preserve every prior normalized
terminal in Linear history. The new invocation still performs at most one
forwarding preflight and one original command; any non-pass is terminal and
does not authorize another host substitution, preflight retry, Apple attempt,
or benchmark arm outside the existing runner gates.

## 2026-08-02 gpt-5.6-sol code-mode preflight correction

The ambient-environment correction candidate's forwarding preflight reached
the request validator and stopped with the separate nonpassing
`blocked:replacement_forwarding_unproven` terminal and
`failureStage = direct_tool_contract`. Preserve that terminal in Linear
history; it is not release evidence and must not be relabeled or retried.

Pinned Codex `0.145.0` source commit `25af12f7` proves the first divergent
condition. `codex-rs/models-manager/models.json` selects
`tool_mode = "code_mode_only"`, `shell_type = "shell_command"`, and
`multi_agent = "v2"` for `gpt-5.6-sol`; the effective-tool-mode selection
keeps that model-selected mode even when the corresponding feature flags are
disabled. The existing preflight provider emits a top-level
`function_call` named `exec_command`, and its validator requires the exact
six-tool predecessor function contract. That contract is unsupported for the
pinned model and is the proven cause of `direct_tool_contract`.

Correct only the preflight's synthetic provider path. Parameterize the
existing local responses server with a backward-compatible event-factory
default so all predecessor production and capability rows retain their exact
direct-function behavior. For this DEV-255 preflight, the first response must
emit one `custom_tool_call` named `exec` whose fixed input contains exactly
one awaited `tools.exec_command({cmd: APPROVED_COMMAND})`, then exactly one
`text(result.output)`, with no other call. The second response remains the
single completion message.

Before using either transient request, require exactly two requests. Each
request must expose exactly one outer custom `exec` code tool, while unrelated
optional tools may differ; reject missing or duplicate outer `exec` tools and
reject every top-level `exec_command` or `shell_command`. Across the pair,
require exactly one closed `custom_tool_call` with the approved call ID,
`exec` name, and exact fixed input, followed in request two by exactly one
closed matching `custom_tool_call_output`. Reject every `function_call` or
`function_call_output`, extra nested call, changed command, mismatched call
ID, duplicate output, and original-result leakage. Pinned source proves the
runtime serializes that custom output as exactly two `input_text` items: the
first must match only `Script completed`, the source-formatted one-decimal
wall time, and the exact `Output:` suffix; the second contains the forwarded
bytes. Reject failed, running, terminated, malformed, extra, image, or string
output variants. Extract the forwarded text only from the second item while
applying original-result exclusion to the whole second request. Keep the exact
command-counter value of one, hook receipt binding, untouched-original
exclusions, request-body
deletion, and every stderr, privacy, retry, and identity boundary unchanged.
This correction must not accept or hide the unsupported predecessor direct
call path. Keep the normalized stage enum stable: `direct_tool_contract`
covers outer-code-tool and custom-call incompatibility, and `function_output`
covers a malformed or mismatched custom output after the pair count passes.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff and release-evidence review pass, commit a new clean
candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new source-corrected candidate row,
not a retry of any preserved terminal. A non-pass is terminal and authorizes
no executable substitution, preflight retry, Apple attempt, or benchmark arm
outside the existing gates.

## 2026-08-02 Responses Lite tool-location correction

The clean `918617f47d8406a33c50c88c980d9f035fbb9855` candidate preserved all
prior fixes but stopped at the forwarding request validator with the separate
nonpassing `blocked:replacement_forwarding_unproven` terminal and
`failureStage = direct_tool_contract`. Preserve that terminal in Linear
history. It is not release evidence, must not be relabeled, and must not be
retried.

Pinned Codex `0.145.0` source commit `25af12f7` proves the next first
divergence. The `gpt-5.6-sol` model record sets
`use_responses_lite = true`. In `codex-rs/core/src/client.rs`,
`build_responses_request` serializes the generated tool JSON into one leading
`ResponseItem::AdditionalTools` with `role = "developer"`, splices that item
at the start of `input`, and sets the top-level `tools` member to `None`.
The current validator instead requires `request.tools` to be a list, so it
rejects the source-supported request before validating the already corrected
custom call lifecycle.

Correct only the DEV-255 forwarding validator and its synthetic request
fixtures. For each of the exact two requests, require the top-level `tools`
key to be absent and require the first input item to be exactly one closed
`additional_tools` object with exactly `type`, `role`, and `tools`, developer
role, and a list-valued embedded tool set. Reject a missing, duplicate,
non-leading, wrong-role, extra-key, or malformed prefix; simultaneous
top-level tools including explicit null; and any additional tool-definition
container elsewhere in the request input. Validate the exact one custom
`exec` outer tool and the
top-level `exec_command` and `shell_command` exclusions against only that
embedded list. Unrelated optional embedded tools may differ between requests.

Keep the exact ordered `custom_tool_call` then matching
`custom_tool_call_output` lifecycle in request two, the two-item completed
script output parser, the single command counter, whole-request original
exclusion, receipt binding, request deletion, normalized failure stages,
identity checks, no-retry rule, and every stderr and privacy boundary
unchanged. Do not accept a top-level tool list as compatibility behavior.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff and release-evidence review pass, commit one new
clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new Responses Lite-corrected
candidate row, not a retry of `918617f47d8406a33c50c88c980d9f035fbb9855`
or any earlier terminal. A non-pass is terminal and authorizes no executable
substitution, preflight retry, Apple attempt, or benchmark arm outside the
existing gates.

## 2026-08-03 PostToolUse code-mode replacement correction

The clean `8b26f12f613184f5c66c5c52236ec0fc0bce326d` candidate preserved every
prior correction but stopped after the original command executed once with
the separate nonpassing `blocked:replacement_forwarding_unproven` terminal
and `failureStage = original_exclusion`. Preserve that terminal in Linear
history. It is not release evidence, must not be relabeled, and must not be
retried.

Pinned Codex `0.145.0` source commit `25af12f7` proves the first divergent
condition. `PostToolUseFeedbackOutput.code_mode_result` deliberately returns
the original nested-tool result for ordinary feedback, so a successful
`continue: false` / `stopReason` response cannot replace the code-mode promise.
The official hook tests instead prove that `decision = "block"` rejects that
promise with `reason` after the command executes and excludes the original
result. `code-mode/runtime/module_loader.rs::resolve_tool_response` rejects
with the exact raw `error_text` string.

Correct the shared PostToolUse boundary only for a validated applied
consultation: return exactly `{"decision":"block","reason":stop_reason}`.
Every decline, malformed result, bridge failure, observation failure, and
other exception continues to return `None`, preserving the exact untouched
original. The fixed preflight code-mode script must execute the one approved
nested command once, forward `result.output` on success, and catch a blocked
promise to forward exactly `String(error)`. Keep one Apple attempt, no retry,
and every existing command, context, identity, stderr, cleanup, and privacy
boundary unchanged.

Bind replacement proof directly to the forwarded condensation bytes. The
application observation records the exact `reason` byte count and SHA-256
after independently validating the closed block response and its serialized
stdout bytes. The outer preflight compares its sole forwarded second input
item directly to those observation values and keeps whole-request original
exclusion. Delete the impossible reconstruction of a
`continue` / `stopReason` wrapper; no provider request body, raw hook output,
Apple output, prompt, response, reasoning, path, or transcript may enter
committed evidence.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff and release-evidence review pass, commit one new
clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new source-corrected candidate row,
not a retry of `8b26f12f613184f5c66c5c52236ec0fc0bce326d` or any earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 clean production identity correction

The clean `3b98d7c1f19b68c1263db652a700edbf1e473294` candidate stopped before
Codex forwarding with the separate nonpassing
`blocked:production_identity_unapproved` terminal. Preserve that terminal in
Linear history. It is not release evidence, must not be relabeled, and must
not be retried.

Read-only comparison proved that the approved production plugin digest had
been derived in a Python process that first wrote ignored `__pycache__` files
inside the plugin tree. The digest therefore described a contaminated local
tree rather than the reviewed clean payload. The adapter and other four file
identities were exact and unchanged. Refresh only the production plugin
digest from the clean tree and add one deterministic equality check between
all current production identities and the closed approved map. Keep
`PYTHONDONTWRITEBYTECODE = 1` for every runner and test invocation; do not
exclude arbitrary files from the tree hash or weaken exact identity checks.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff review pass, commit one new clean candidate and run
exactly one native Codex `0.145.0` `--through usage-dry-run` row. This is a new
identity-corrected candidate row, not a retry of
`3b98d7c1f19b68c1263db652a700edbf1e473294` or any earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 deterministic Codex stderr correction

The clean `fe10e01a57ce2aae1c0a074c0effaa4bf3ddc666` candidate stopped with the
separate nonpassing `blocked:replacement_forwarding_unproven` terminal and
`failureStage = process_stderr`. Preserve that terminal in Linear history. It
is not release evidence, must not be relabeled, and must not be retried. No
raw stderr was retained.

Pinned Codex `0.145.0` source commit `25af12f7` proves that `codex exec`
installs a tracing formatter on process stderr and derives its filter from
`RUST_LOG`; without an explicit value its default admits error-level runtime
diagnostics. The benchmark already rejects ambient `RUST_LOG`, requires the
JSONL event stream and exit status, independently validates both provider
requests, and binds command, hook, observation, and replacement receipts.
Set the controlled child environment to the exact fixed value
`RUST_LOG = "off"`. This suppresses only Codex tracing formatter output;
direct process stderr remains captured and must still be empty or match the
one pinned 39-byte nonterminal-stdin notice. Do not broaden the stderr
classifier, retain raw diagnostics, or weaken any JSONL, exit, receipt,
counter, cleanup, or evidence gate.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff review pass, commit one new clean candidate and run
exactly one native Codex `0.145.0` `--through usage-dry-run` row. This is a new
deterministic-environment candidate row, not a retry of
`fe10e01a57ce2aae1c0a074c0effaa4bf3ddc666` or any earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 provider-counter normalized substage correction

The clean `4d53360bad53259c113ae05ad41a66677a0c4328` candidate passed the complete
replacement-forwarding preflight, then stopped in the first plugin-off dry arm
with the separate nonpassing `blocked:provider_request_counter_invalid`
terminal. Preserve that terminal in Linear history. It is not release
evidence, must not be relabeled, and must not be retried.

The current counter gate collapses three independent closed conditions into
one terminal: nonzero Codex process exit, invalid normalized OTel payload, or
no completed OTel batch. Split only that terminal into the closed normalized
`failureStage` values `process_exit`, `telemetry_payload`, and
`telemetry_batch`, evaluated in that order. Retain no return code, batch count,
payload, request, stderr, prompt, response, path, or transcript. Do not change
the request counter, OTel configuration, provider, arm, usage, correctness,
cleanup, or evidence acceptance rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff review pass, commit one new clean candidate and run
exactly one native Codex `0.145.0` `--through usage-dry-run` row. This is a new
normalized-diagnostic candidate row, not a retry of
`4d53360bad53259c113ae05ad41a66677a0c4328` or any earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 isolated parent-authentication correction

The clean `1ae8c8bfd201bd29a08aabe613f7d86805b5cf6f` candidate passed the complete
replacement-forwarding preflight, then stopped in the first plugin-off dry arm
with `blocked:provider_request_counter_invalid` and
`failureStage = process_exit`. Preserve that terminal in Linear history. It is
not release evidence, must not be relabeled, and must not be retried.

A separate read-only prerequisite check proves the captured Codex `0.145.0`
executable is authenticated in the normal Codex home but reports not logged in
inside the fresh isolated arm home. The local forwarding provider does not
need parent authentication, which explains why forwarding passes while the
first real provider-backed arm exits before telemetry acceptance.

For each measured arm only, capture the existing source `auth.json` as a
regular non-symlink file with mode `0600`, a bounded nonzero size, and a stable
metadata snapshot. Copy it without decoding, hashing, logging, or serializing
its contents into the mode-`0700` temporary arm root, force the staged copy to
mode `0600`, and require `codex login status` to succeed while discarding its
stdout and stderr. Delete the staged file immediately after the single Codex
invocation, recheck the source metadata, and require the isolated root cleanup
already mandated for every arm. Never copy user configuration, plugin state,
or other private files; never include credential contents, hashes, paths, or
status output in evidence. Missing, malformed, changed, unauthenticated, or
unclean authentication is `blocked`, never `pass`.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning security and diff review pass, commit one new clean
candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new authentication-corrected candidate
row, not a retry of `1ae8c8bfd201bd29a08aabe613f7d86805b5cf6f` or any earlier
terminal. A non-pass is terminal and authorizes no executable substitution,
preflight retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 OTLP LogRecord event-name correction

The clean `51548386f409f71ab5d8ac91e1ce90b670e46b6d` candidate passed replacement
forwarding, isolated authentication, and the measured-arm Codex process, then
stopped with `blocked:provider_request_counter_invalid` and
`failureStage = telemetry_payload`. Preserve that terminal in Linear history.
It is not release evidence, must not be relabeled, and must not be retried.

Codex `0.145.0` source commit `25af12f7` pins `opentelemetry-proto = 0.31.0`.
The official stable OTLP `LogRecord` schema includes optional field 12,
`event_name`, serialized in OTLP/JSON as `eventName`; the current closed record
allowlist predates that field. Accept only an optional nonempty string
`eventName` no longer than the official recommended 256-character bound. Do
not use it to count requests or let it replace the required unique
`event.name = codex.api_request` and unique string `endpoint` attributes.
Reject malformed values, all other extra fields, duplicate attributes, and
missing API-request discriminators exactly as before. Retain no event name,
payload, request, prompt, response, path, or transcript.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning schema and diff review pass, commit one new clean
candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new OTLP-schema-corrected candidate
row, not a retry of `51548386f409f71ab5d8ac91e1ce90b670e46b6d` or any earlier
terminal. A non-pass is terminal and authorizes no executable substitution,
preflight retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 closed OTLP payload-stage diagnostic

The clean `a30f2c38c24f583c23334a0ac47cc9b874820961` candidate preserved the
official `eventName` correction but stopped with the same separate nonpassing
`blocked:provider_request_counter_invalid`, `failureStage = telemetry_payload`
terminal. Preserve it in Linear history. It is not release evidence, must not
be relabeled, and must not be retried.

The closed receiver currently discards which parser boundary rejected the
payload. Retain only one additional closed `payloadStage` selected where the
rejection occurs: `transport`, `json`, `envelope`, `resource`, `scope`,
`record`, `attribute`, `value`, or `discriminator`; use `unknown` only if the
counter reports invalid without a stage. Store no field name, field value,
payload, count, request, prompt, response, path, or transcript. Keep the same
strict schema, request discriminator, counter, process, arm, usage,
correctness, cleanup, and evidence acceptance rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff review pass, commit one new clean candidate and run
exactly one native Codex `0.145.0` `--through usage-dry-run` row. This is a new
normalized-diagnostic candidate row, not a retry of
`a30f2c38c24f583c23334a0ac47cc9b874820961` or any earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 additive OTLP Resource entity references

The clean `4c1108fdcfdfc006d49e7692ebace1c22008ddfc` candidate's one authorized
native usage dry row stopped at the closed `telemetry_payload / resource`
terminal. Preserve that normalized terminal in Linear history; do not retry
or relabel it.

The pinned OpenTelemetry Proto v1.6.0 stable Resource package adds the official
JSON field `entityRefs` (proto `entity_refs`), explicitly at Development
status, with `EntityRef` members containing only `schemaUrl`, `type`, `idKeys`,
and `descriptionKeys`. Accept and validate that additive official schema field
at the shared resource boundary. Retain none of its values and do not change
the request discriminator, counter, process, arm, usage, correctness, cleanup,
or evidence acceptance rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning source and diff review pass, commit one new clean
candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new schema-corrected candidate, not a
retry of `4c1108fdcfdfc006d49e7692ebace1c22008ddfc` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 empty OTLP AnyValue compatibility

The clean `821c69d676391752c3242f66f278ee871b994f13` candidate's one authorized
native usage dry row passed the Resource correction and stopped at the closed
`telemetry_payload / value` terminal. Preserve that normalized terminal in
Linear history; do not retry or relabel it.

The pinned OpenTelemetry Proto v1.6.0 stable `AnyValue` schema explicitly
permits its oneof to be unspecified, represented by an empty JSON object.
Accept that exact empty object at the shared AnyValue boundary. Continue to
reject multiple or unknown union members, and continue to require exact
nonempty string values for the `event.name` and `endpoint` request
discriminators. Retain no attribute value and do not change counter, process,
arm, usage, correctness, cleanup, or evidence acceptance rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning source and diff review pass, commit one new clean
candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new schema-corrected candidate, not a
retry of `821c69d676391752c3242f66f278ee871b994f13` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 nested empty OTLP value-list compatibility

The clean `c12445e9fc7c823d6b501ee890c9759e626783bf` candidate's one authorized
native usage dry row preserved the empty AnyValue correction but stopped at
the same closed `telemetry_payload / value` terminal. Preserve that result in
Linear history; do not retry or relabel it.

The pinned OpenTelemetry Proto v1.6.0 stable `ArrayValue` and `KeyValueList`
messages both permit an empty repeated `values` field. ProtoJSON omits empty
repeated fields, so their exact compatible nested representation is `{}`.
Accept an omitted `values` member as the existing empty list at those two
shared boundaries. Continue to reject unknown members and malformed present
lists, and retain exact string request discriminators and all existing
counter, process, arm, usage, correctness, cleanup, and evidence rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning source and diff review pass, commit one new clean
candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new schema-corrected candidate, not a
retry of `c12445e9fc7c823d6b501ee890c9759e626783bf` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 closed OTLP AnyValue substage diagnostic

The clean `9e0814446f4977f6451b1cded636c7eb4db15275` candidate's one authorized
native usage dry row stopped at the same broad `telemetry_payload / value`
terminal after the two official default-omission corrections. Preserve that
result in Linear history; do not retry or relabel it.

Replace only the broad `value` diagnostic with one closed parser-boundary
stage: `value_container`, `value_string`, `value_bool`,
`value_integer_bytes`, `value_double`, `value_array`, `value_kvlist`, or
`value_union`. Retain no key, value, payload, count, request, prompt, response,
path, or transcript. Do not change accepted schema, request discrimination,
counter, process, arm, usage, correctness, cleanup, or evidence rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff review pass, commit one new clean candidate and run
exactly one native Codex `0.145.0` `--through usage-dry-run` row. This is a
new diagnostic candidate, not a retry of
`9e0814446f4977f6451b1cded636c7eb4db15275` or an earlier terminal. A non-pass
is terminal and authorizes no executable substitution, preflight retry, Apple
attempt, or benchmark arm outside the existing gates.

## 2026-08-03 ProtoJSON null AnyValue compatibility

The clean `4f0e3e1392a02306a21904a31913387c23b5ce60` diagnostic candidate's one
authorized native usage dry row stopped at the closed
`telemetry_payload / value_container` terminal. Preserve that result in
Linear history; do not retry or relabel it.

Official ProtoJSON parsers accept JSON `null` for any field and leave the
field unset. Accept `null` only as the same empty AnyValue state already
accepted as `{}`; continue to reject `null` inside repeated fields. Explicitly
require the `event.name` and `endpoint`
discriminator values to remain exact one-member string AnyValues so `null`
cannot prove or count a provider request. Retain no field or value and do not
change counter, process, arm, usage, correctness, cleanup, or evidence rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning source and diff review pass, commit one new clean
candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new schema-corrected candidate, not a
retry of `4f0e3e1392a02306a21904a31913387c23b5ce60` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 closed correctness-oracle diagnostic

The clean `9eaebdec4157e32972ebf4a7dd875b9baa1a245e` candidate's one authorized
native usage dry row passed the actual provider-request counter and stopped at
the separate `fail:correctness_oracle_failed` terminal. Preserve that result
in Linear history; do not retry or relabel it.

Retain one closed `failureStage`: `command_result` for the exact executed
command, exit status, output bytes, and digest binding; or `parent_outcome` for
the final canonical response and DEV-142 score. Retain no command, output,
digest, prompt, response, score detail, path, or transcript. Do not change
either oracle, the accepted result, counter, process, arm, usage, correctness,
cleanup, or evidence rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff review pass, commit one new clean candidate and run
exactly one native Codex `0.145.0` `--through usage-dry-run` row. This is a new
diagnostic candidate, not a retry of
`9eaebdec4157e32972ebf4a7dd875b9baa1a245e` or an earlier terminal. A non-pass
is terminal and authorizes no executable substitution, preflight retry, Apple
attempt, or benchmark arm outside the existing gates.

## 2026-08-03 closed command-result diagnostic

The clean `16a2e6c30367791a4afa9f5cc414123bfb27390f` diagnostic candidate's one
authorized native usage dry row stopped at the closed
`correctness_oracle_failed / command_result` terminal. Preserve that result
in Linear history; do not retry or relabel it.

Retain one closed `oracleStage`: `parent_output_file`, `event_shape`,
`command_count`, `command_text`, `exit_status`, `output_type`, `output_bytes`,
or `fixture_digest`. Retain no command, output, digest, prompt, response, path,
or transcript. Preserve the exact existing composite predicate and do not
change accepted results, provider counts, process, arm, usage, correctness,
cleanup, or evidence rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning diff review pass, commit one new clean candidate and run
exactly one native Codex `0.145.0` `--through usage-dry-run` row. This is a new
diagnostic candidate, not a retry of
`16a2e6c30367791a4afa9f5cc414123bfb27390f` or an earlier terminal. A non-pass
is terminal and authorizes no executable substitution, preflight retry, Apple
attempt, or benchmark arm outside the existing gates.

## 2026-08-03 pinned Codex command rendering

The clean `e65bb32e3e0dde4f4e6a3958cf5029e160866b6b` diagnostic candidate's one
authorized native usage dry row stopped at the exact
`correctness_oracle_failed / command_result / command_text` terminal.
Preserve that result in Linear history; do not retry or relabel it.

Pinned Codex `0.145.0` source passes the protocol's rendered command into the
JSONL `CommandExecutionItem`, and official Codex JSONL examples render direct
commands through a system shell with `-lc`. Treat the reported command as
matching only when it equals the approved command exactly or parses to exactly
`/bin/bash -lc <approved-command>` or `/bin/zsh -lc <approved-command>`.
Reject relative shells, other shells or flags, extra arguments, malformed
quoting, and any different inner command. Do not change command count, exit,
output, digest, parent outcome, provider count, arm, or evidence rules.

After focused and full deterministic gates, generated-artifact checks, and a
formal high-reasoning source and diff review pass, commit one new clean
candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new source-corrected candidate, not a
retry of `e65bb32e3e0dde4f4e6a3958cf5029e160866b6b` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 isolated macOS login-shell PATH

The clean `ea40d41b2f21735071234470956b184b1843fd97` candidate's one authorized
native usage dry row passed the rendered-command correction and stopped at
`correctness_oracle_failed / command_result / exit_status`. Preserve that
result in Linear history; do not retry or relabel it.

A local process-only reproduction proves `/bin/zsh -lc` applies macOS login
initialization and resolves the system Swift ahead of an inherited prepended
fixture directory. For each already-isolated arm root, create a private
`ZDOTDIR/.zprofile` that prepends only that arm's existing fixture `bin` after
system initialization. Do not set `HOME`, read or modify user shell files, add
executables, change the approved command, or retain the ephemeral path. Keep
all command, exit, output, digest, provider, arm, and evidence oracles exact.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new environment-corrected candidate,
not a retry of `ea40d41b2f21735071234470956b184b1843fd97` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 pinned non-login shell command rendering

The clean `275c142e8ac4d86a61f1cfe3637221ace9449f85` candidate's one
authorized native usage dry row stopped at the exact
`correctness_oracle_failed / command_result / command_text` terminal.
Preserve that result in Linear history; do not retry or relabel it.

Pinned Codex `0.145.0` source commit `25af12f7` proves that the
`shell_command` path supports both login and non-login execution. Its shell
contract derives exactly `[shell_path, "-lc", command]` for login execution
and `[shell_path, "-c", command]` for non-login execution, and the JSONL
command item serializes that exact argv with `shlex_join`. Accept a reported
command only when it equals the approved command exactly or parses to exactly
`/bin/bash|/bin/zsh -c|-lc <approved-command>`. Reject relative or other
shells, other or combined flags, missing or extra arguments, malformed
quoting, and any changed inner command. Keep command count, exit, output,
digest, parent outcome, provider count, arm, and evidence rules unchanged.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning source and diff review
pass, commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new source-corrected candidate, not a
retry of `275c142e8ac4d86a61f1cfe3637221ace9449f85` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 closed parent-outcome diagnostic

The clean `8e530a902241c1b50fac9ed426f102f8da2e1395` candidate's one
authorized native usage dry row passed the complete command-result oracle and
stopped at the separate `correctness_oracle_failed / parent_outcome`
terminal. Preserve that result in Linear history; do not retry or relabel it.

Retain one closed `oracleStage`: `output_binding` for output size,
final-message, candidate, coordinate, and binding-digest invariants;
`parent_json` for duplicate-safe UTF-8 JSON syntax; `parent_schema` for the
exact eight-field object; `result_contract` for the fixed DEV-142 result
contract; or `quality_score` for the DEV-142 correctness score. Retain no
field name, value, reason code, hash, output, prompt, response, path, or
transcript. Preserve the exact existing composite predicate and do not change
accepted results, provider counts, process, arm, usage, correctness, cleanup,
or evidence rules.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new diagnostic candidate, not a retry
of `8e530a902241c1b50fac9ed426f102f8da2e1395` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 closed measured-arm cleanup diagnostic

The clean `c043bef06861c45dafdbdb99cc80a75269588042` candidate's one
authorized native usage dry row progressed beyond the command-result and
parent-outcome oracles, then stopped at `blocked:cleanup_incomplete`.
Preserve that result in Linear history; do not retry or relabel it.

For measured arms only, retain one closed `cleanupStage`: `parent_auth` for
failure to delete and prove absence of the staged opaque authentication file,
or `isolated_root` for failure to remove and prove absence of the temporary
arm root. Retain no path, exception, metadata, count, credential, output, or
host detail. Forwarding-preflight cleanup keeps its existing generic
stage-free terminal, and the defensive missing-pending blocker remains
generic. Cleanup still supersedes every pending arm result at the same
boundaries; do not change cleanup execution, precedence, acceptance, or
evidence rules.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new diagnostic candidate, not a retry
of `c043bef06861c45dafdbdb99cc80a75269588042` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution, preflight
retry, Apple attempt, or benchmark arm outside the existing gates.

## 2026-08-03 native parent-output schema correction

The clean `9fee07ebc908faa4162ac5540bf530c8ebf12d23` candidate's one
authorized native usage dry row passed command execution and cleanup, then
stopped at `correctness_oracle_failed / parent_outcome / result_contract`.
Preserve that result in Linear history; do not retry or relabel it.

Pinned Codex `0.145.0` source commit `25af12f7` exposes the native global
`--output-schema <file>` option and proves that it forwards the supplied JSON
Schema as a strict Responses output format. Materialize one deterministic,
fixture-independent, private regular schema file inside each existing arm
root and pass it exactly once. The schema may contain only the existing public
eight-field shape, nested diagnostic shape, supported types, enums, bounds,
required sets, and closed-object rules. It contains no command, fixture,
expected fact, score, hash, prompt, response, path, or private value.

Keep the unchanged DEV-142 `validate_result` and `score_condensation` calls as
the independent application-owned acceptance authorities. In particular,
string-list and diagnostic-identity uniqueness, warning accounting, path
safety, byte limits, and semantic correctness remain application checks;
`uniqueItems` is not in the provider's supported strict-schema subset. Schema
creation, byte identity, regular-file mode, argument binding, or cleanup
failure blocks before acceptance and has no schema-free fallback. This adds
no command, tool call, provider, Apple attempt, parent request, or model turn.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new source-corrected candidate, not a
retry of `9fee07ebc908faa4162ac5540bf530c8ebf12d23` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-03 forwarding identity boundary diagnostic

The clean `d69849e1b8581166bdd33d561f6de25294bf4b41` candidate's one
authorized native usage dry row passed with exactly two parent requests. Its
single complete benchmark execution then stopped terminally at
`blocked:replacement_forwarding_unproven / identity_trust` and wrote no
evidence file. Preserve both facts in Linear history; do not retry or relabel
either execution.

Keep the unchanged forwarding blocker and add only one closed `identityStage`
when `failureStage` is `identity_trust`: `staged_plugin`, `plugin_install`,
`workspace`, `initial_hook_trust`, `executable_recheck`, `installed_plugin`,
`production_identities`, `hook_recheck`, or `forwarding_proof`. The stages map
in order to the existing identity/trust boundaries. Split the compound
installed-tree and production-identity predicate only to preserve that
left-to-right diagnostic boundary. Cleanup still supersedes the pending
identity diagnostic.

Never retain or serialize an exception, path, hash, version, source, error
body, raw prompt, command, response, JSONL, telemetry content, Apple output,
credential, or transcript. No identity rule, trust rule, command, request,
turn, Apple attempt, retry, correctness oracle, evidence acceptance, privacy
boundary, or release gate changes.

## 2026-08-03 native optional-package capture correction

The clean `da063ecadc7c8d944a2b1a8391d4a4bd335640ad` candidate's one
authorized native usage dry run stopped before a row with
`blocked:host_prerequisite_unavailable` and wrote no evidence file. Preserve
that immutable terminal in Linear history; do not retry or relabel it.

The official installation separates the `@openai/codex@0.145.0` launcher from
its `@openai/codex-darwin-arm64` optional-dependency alias. Require that alias
to target exactly `npm:@openai/codex@0.145.0-darwin-arm64` and the installed
native payload metadata to be exactly `@openai/codex` version
`0.145.0-darwin-arm64`. Supersede only the prior package-location assumption:
capture the native executable at the aliased payload's
`vendor/aarch64-apple-darwin/bin/codex` suffix and pass its resolved
`<host-path>` directly to `--codex-executable`. Do not invoke the JavaScript
launcher, select through `PATH`, or search for a substitute after capture.

Use a fail-closed `set -eu` capture. Require both package identities and exact
versions, a regular executable native target, strict `codex-cli 0.145.0`
output, and an immediate unchanged resolution, snapshot, and version recheck.
Any mismatch is blocked without substitution or retry. Commit no installation
root, private absolute path, or package contents; retain only normalized
package identities, versions, suffix, `<host-path>`, and approved identity
metadata. No runner, interface, evidence, command, provider, model, turn,
Apple-attempt, privacy, correctness, or release rule changes.

After documentation, generated-artifact, full regression, SDK 26.5,
evidence-safety, diff, and ancestry gates plus formal high-reasoning exact-diff
review pass, commit exactly this plan-only change as one new clean candidate.
Under `set -eu`, capture and immediately recheck the optional-package native
binary, then run exactly one candidate-bound native Codex `0.145.0`
`--through usage-dry-run`. This is a new host-identity row, not a retry of
`da063ecadc7c8d944a2b1a8391d4a4bd335640ad` or an earlier terminal. Every
non-pass is terminal and authorizes no executable substitution or retry; only
a pass authorizes that candidate's single complete benchmark execution.

Commit `cd1f2eef6d510ce3aee31e6a4dbd62a6325b0646` was superseded before
capture, native execution, a benchmark row, Apple attempt, or evidence
artifact because its plan described the alias key as a payload identity. It is
not a failed terminal, and its candidate-bound authorization does not transfer.
After the same gates and formal review pass, commit this exact plan-only
identity correction as one new clean candidate with exactly one fresh native
usage-dry-run budget under the unchanged non-pass terminal rules.

## 2026-08-03 zero-attempt Apple preflight attribution

The clean `5f1680852ba55b5375551eb1bc5d2e8217281e2b` candidate's native dry
row passed, then its single complete run produced all 24 pairs and 48 arms but
failed release with median reduction `-19996` PPM, zero Apple attempts, and
zero validated applied rows. Correctness regressions, additional requests and
turns, command reruns, cleanup failures, and unsafe evidence findings were all
zero. Preserve this terminal in Linear; do not retry or relabel it. Its
validated untracked fail evidence was moved recoverably out of the required
output path and is not release evidence.

Bump only the optional benchmark observation to schema version 2 and add a
closed nullable `preflightStage`. A valid zero-attempt fallback requires
exactly one of `apple_unavailable`, `locale_unsupported`,
`generation_preflight_unavailable`, or `context_budget_exceeded`; applied,
one-attempt fallback, blocked or uncertain observation, and plugin-off require
`null`. Derive the value only from a closed bridge result with zero attempts.
Every missing, unknown, or contradictory value blocks as an observation
invariant failure.

Keep the value transient. Strip it before existing arm validation and evidence
construction, and leave the committed evidence schema and release arithmetic
unchanged. The complete terminal may add only fixed four-key nonnegative
`preflightStageCounts`, whose sum equals plugin-on zero-attempt arms. It is
diagnostic metadata, not Apple availability proof, a release input, or an
attempt/applied substitute. No prompt, response, Apple output, error, path,
credential, transcript, raw observation, additional command, request, turn,
attempt, rerun, retry, provider, scorer, oracle, or release-rule change.

After focused and full tests, SDK 26.5 compilation, generated-artifact,
evidence-safety, diff, ancestry, and formal high-reasoning exact-diff review
pass, commit one new clean diagnostic candidate. Run exactly one native usage
dry row; only a pass authorizes its one complete execution. Every non-pass is
terminal without substitution, retry, or relabeling.

## 2026-08-03 transient preflight wiring correction

Candidate `303292936127c58aff5678c8ba9026da77ce519a` stopped during its
single authorized dry execution with an unclassified runner exception before
a normalized row. Preserve that terminal in Linear; do not retry or relabel
it. Static inspection found the transient `preflight_stage` keyword on the
unchanged applied-state derivation call while the subsequent `ArmObservation`
constructor omitted it.

Move only that keyword to `ArmObservation` and structurally assert the applied
derivation's exact unchanged keyword set plus observation ownership. No schema,
hook, bridge, evidence, command, request, turn, attempt, retry, provider,
oracle, scorer, privacy, or release rule changes. After focused and full
gates, SDK and generated checks, exact-diff review, and a clean new commit,
authorize exactly one new native dry row under the unchanged terminal rules.

## 2026-08-03 closed process-exit structure diagnostic

The clean `e45c2e0a59aaaaeea5bab85c669fd4f184973ae4` candidate's native dry
row passed, then its single complete execution stopped at
`blocked:provider_request_counter_invalid` with
`failureStage = process_exit`. Preserve that terminal in Linear history; do
not retry or relabel it.

Pinned Codex `0.145.0` source commit
`25af12f7e61572b0bc18ddb1008be543b91519b0` proves that a nonzero exec
process may follow a matching nonretry error notification, a failed or
interrupted turn, or a server-request response failure. Its JSONL stream does
not retain enough correlation state to infer those causes. Retain only one
closed structural `processExitStage`: `error_then_turn_failed` for an exact
top-level error followed by an exact final `turn.failed`; `turn_failed` for an
exact final failed turn without a top-level error; `terminal_absent` for an
otherwise valid started stream containing only supported nonterminal item
events; or `unclassified` for every other byte or structure.

Parse duplicate-safe UTF-8 JSON only while the captured stdout remains
transient. Check message presence and type but never inspect, compare, hash,
copy, retain, or classify its text; keep intermediate item bodies opaque.
Clear captured stdout unconditionally, including on malformed UTF-8, JSON,
or structure. Require `processExitStage` exactly when
`failureStage = process_exit` and forbid it otherwise. Retain no stdout,
message, item, count, return code, path, output, prompt, response, Apple
output, telemetry content, credential, or transcript.

Keep process-exit precedence, stderr handling, counter, command, request,
turn, Apple-attempt, oracle, cleanup, evidence, retry, and release rules
unchanged. After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning security and diff
review pass, commit one new clean diagnostic candidate and run exactly one
native Codex `0.145.0` `--through usage-dry-run` row. Only a pass authorizes
its single complete execution; every non-pass is terminal without retry,
substitution, or relabeling.

## 2026-08-03 closed normalized-arm invariant diagnostic

The clean `29b7b6ef8f58087fedbd4f470a615554ba7164d8` candidate's one
authorized native usage dry row passed command and parent correctness plus
cleanup, then stopped at `blocked:arm_invariant_invalid`. Preserve that result
in Linear history; do not retry or relabel it.

Retain the existing normalized-arm predicate and its left-to-right precedence
exactly. On failure, retain only one closed `invariantStage`: `role`,
`parent_requests`, `command_executions`, `parent_turns`, `apple_attempts`,
`role_state`, `correctness`, `stderr`, `hook_latency_samples`,
`hook_role_state`, or `cleanup`. Retain no observed value, count, boolean,
latency, stderr size, output, prompt, response, path, or error. Keep generic
latency validation and the unchanged DEV-142 arm validator outside this
diagnostic. Do not add a validated-applied type rule or require correctness to
be true at this structural boundary.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new diagnostic candidate, not a retry
of `29b7b6ef8f58087fedbd4f470a615554ba7164d8` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-03 remaining cleanup-producer diagnostic

The clean `1e6c6742cd119409c863e198b1e25dd150f80b3b` candidate's one
authorized native usage dry row stopped at generic
`blocked:cleanup_incomplete` with neither `invariantStage` nor
`cleanupStage`. Preserve that result in Linear history; do not retry or
relabel it.

Static enumeration leaves exactly the forwarding-preflight root cleanup and
the measured arm's defensive missing-pending branch as generic producers.
The new terminal supersedes the earlier decision to keep those locations
stage-free because that ambiguity now prevents root-cause diagnosis. Extend
the closed `cleanupStage` only with `forwarding_root` and `arm_pending`.
Forwarding-root cleanup keeps its existing superseding precedence and never
adds `failureStage`; the defensive branch keeps the same
`cleanup_incomplete` reason. Retain no path, error, value, count, metadata,
credential, output, prompt, response, or transcript. Do not change cleanup
execution, accepted outcomes, retries, commands, requests, turns, Apple
attempts, usage, correctness, or evidence rules.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new diagnostic candidate, not a retry
of `1e6c6742cd119409c863e198b1e25dd150f80b3b` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-03 parent-request retry correction

The clean `f7e104e4e471e93d67203842c7742ebffeb9435f` candidate's one
authorized native usage dry row stopped at
`blocked:arm_invariant_invalid` with `invariantStage:parent_requests`.
Preserve that result in Linear history; do not retry or relabel it.

Pinned Codex `0.145.0` source commit `25af12f7` defaults the OpenAI provider
to four request retries and five stream retries, and native telemetry counts
each attempt. The approved benchmark requires exactly two parent requests and
no retry. Pass `model_providers.openai.request_max_retries=0` and
`model_providers.openai.stream_max_retries=0` exactly once on the existing
single native invocation. Keep the raw request counter and exact two-request
invariant unchanged; a transient request or stream failure stops the arm.
This adds no command, provider, Apple attempt, parent request, model turn,
fallback, filtering, or relabeling.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new source-corrected candidate, not a
retry of `f7e104e4e471e93d67203842c7742ebffeb9435f` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-03 nonreserved no-retry provider correction

The clean `d819d8489490f25f00f55afbef94c13641eb1fea` candidate's one
authorized native usage dry row stopped at
`blocked:codex_stderr_unclassified`. Preserve that result in Linear history;
do not retry or relabel it.

Pinned Codex `0.145.0` source commit `25af12f7` rejects every configured
`model_providers.openai` entry because `openai` is a reserved built-in ID.
The prior retry correction therefore failed during strict configuration load
before an arm could run. Do not inspect or retain the emitted stderr.

Replace the rejected overrides with one nonreserved
`runtime-v1-openai-no-retry` provider that exactly clones the pinned built-in
OpenAI provider: name, Responses wire API, version header, organization and
project environment-header mappings, OpenAI authentication, WebSocket
support, absent explicit base URL, and absent environment key. Only its ID and
zero request and stream retry budgets differ. Select it exactly once for the
existing invocation. This remains the same authenticated OpenAI parent
service and preserves auth-mode base-URL selection; it adds no endpoint,
credential, provider service, inference fallback, command, request, turn,
Apple attempt, telemetry field, or evidence field. Keep the raw request
counter, exact two-request invariant, provider evidence label, correctness,
privacy, and failure-stop rules unchanged.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new source-corrected candidate, not a
retry of `d819d8489490f25f00f55afbef94c13641eb1fea` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-03 parent HTTP telemetry correction

The clean `21efe675e27746963f2b07a18725057fe597674f` candidate's one
authorized native usage dry row stopped at
`blocked:arm_invariant_invalid` with `invariantStage:parent_requests`.
Preserve that result in Linear history; do not retry or relabel it.

Pinned Codex `0.145.0` source commit `25af12f7` routes a provider with
WebSocket support through Responses WebSocket, including startup prewarm.
That supported transport emits `codex.websocket_request`; it does not emit
the `codex.api_request` events consumed by the approved raw parent-request
counter. The supported HTTP Responses path emits one `codex.api_request` per
HTTP attempt. Set only the benchmark provider clone's
`supports_websockets=false` so the existing invocation deterministically uses
HTTP Responses without WebSocket prewarm or fallback.

Keep the same authenticated OpenAI service, auth-mode base URL, headers,
model, Responses wire API, zero configured request and stream retry budgets,
raw counter, and exact two-request invariant. The zero budgets do not disable
pinned unauthorized-auth recovery; any recovery attempt remains visible to
the raw counter and terminally fails the exact-two invariant. Do not count
WebSocket events, filter attempts, relabel counts, or change telemetry,
commands, turns, Apple attempts, usage, correctness, privacy, or evidence.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. This is a new transport-corrected candidate,
not a retry of `21efe675e27746963f2b07a18725057fe597674f` or an earlier
terminal. A non-pass is terminal and authorizes no executable substitution or
retry.

## 2026-08-03 closed Codex stderr diagnostic

The clean `743e0a92836c545e162c93f3e17d8e91fe02ab30` candidate's one
authorized native usage dry row passed with exactly two parent requests. Its
single complete benchmark execution later stopped at
`blocked:codex_stderr_unclassified` and wrote no evidence file. Preserve both
facts in Linear history; do not retry or relabel either execution.

Pinned Codex `0.145.0` source commit `25af12f7` limits JSON exec process
stderr to bounded startup, configuration, authentication, OTel, output, and
stdin producers when the controlled environment sets `RUST_LOG=off`. Retain
the current first-refusal precedence and accept only empty stderr or the exact
pinned 39-byte nonterminal-stdin notice. For every other value, clear the
captured field first and retain only one closed `stderrStage`: `override`,
`codex_home`, `rules`, `config_load`, `login_restriction`, `otel_exporter`,
`output_schema`, `output_file`, `stdin`, or `unknown`.

Known-prefix attribution requires the exact Codex version and pinned source
identity. Identity drift, non-bytes, and unmatched values map to `unknown`.
Never retain or serialize a suffix, value, byte count, hash, path, credential,
prompt, response, telemetry content, Apple output, or transcript. Unaccepted
stderr still blocks before process and provider-counter validation; accepted
stderr preserves the existing provider-counter precedence. This changes no
command, request, turn, Apple attempt, counter, oracle, cleanup, privacy,
evidence acceptance, retry, fallback, or release rule.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. Only a pass authorizes one complete benchmark
execution. This is a new diagnostic candidate, not a retry of
`743e0a92836c545e162c93f3e17d8e91fe02ab30` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-03 forwarding-root absence-oracle correction

The clean `b90b70e8b4d8146942fe98007f4acf18edb2f7e5` candidate's one
authorized native usage dry row stopped at `blocked:cleanup_incomplete` with
`cleanupStage = forwarding_root`. Preserve that result in Linear history; do
not retry or relabel it.

Static inspection proves the shared isolated-root cleanup currently treats
every `shutil.rmtree` `OSError` as incomplete before evaluating its existing
root-absence oracle. Cleanup acceptance is the proved absence of the isolated
root, not an error-free filesystem API return. Invoke `shutil.rmtree` exactly
once, retain no exception or path detail, then evaluate the existing
`root.exists()` oracle exactly once. Root presence keeps the unchanged generic
or stage-specific blocker and cleanup-superseding precedence; root absence is
cleanup success and leaves any earlier body exception authoritative.

Add one regression where the real remover deletes the root and then reports
`OSError`; require clean context exit and proved absence. Preserve the existing
tests where an `OSError` leaves the root present and cleanup remains blocked.
This changes no deletion attempt count, command, request, turn, Apple attempt,
retry, provider behavior, correctness oracle, privacy rule, evidence field, or
release gate.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. Only a pass authorizes one complete benchmark
execution. This is a new cleanup-corrected candidate, not a retry of
`b90b70e8b4d8146942fe98007f4acf18edb2f7e5` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-03 forwarding-root failure-location diagnostic

The clean `13c30bf6b397fc55d30df3269d1d5d24a3ea656a` candidate's one
authorized native usage dry row repeated `blocked:cleanup_incomplete` with
`cleanupStage = forwarding_root`. The absence-oracle correction behaved
fail-closed: the root remained after the single removal attempt. Preserve the
terminal in Linear history; do not retry or relabel it.

Use Python `3.14`'s `shutil.rmtree(onexc=...)` callback as the authoritative
failure location. For forwarding-root cleanup only, lexically map its transient
path to exactly one closed `cleanupFailureStage`: `root`, `staged_plugin`,
`codex_home`, `marketplace`, `workspace`, `synthetic_bridge`,
`command_counter`, or `unknown`, then immediately re-raise the identical
exception. Relative, outside-root, traversal-bearing, malformed, non-path, or
unrecognized values map to `unknown`.

Never retain or serialize the callback path, basename, exception type,
message, errno, count, metadata, or contents. Attach the closed stage only
when the forwarding root remains after an `OSError`; absence remains cleanup
success, and root presence keeps the unchanged blocker and cleanup-superseding
precedence. This diagnostic adds no deletion attempt, retry, fallback, command,
request, turn, Apple attempt, correctness change, evidence acceptance, privacy
change, or release rule.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. Only a pass authorizes one complete benchmark
execution. This is a new cleanup-diagnostic candidate, not a retry of
`13c30bf6b397fc55d30df3269d1d5d24a3ea656a` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-03 value-free parent parsing grammar correction

The clean `4700074fd34383c03f1c25de1103bd632f327e7b` candidate's one
authorized native usage dry row passed with exactly two parent requests. Its
single complete 24-pair benchmark execution later failed terminally at
`correctness_oracle_failed / parent_outcome / quality_score` and wrote no
evidence file. Preserve both facts in Linear history; do not retry or relabel
either execution.

Static inspection identifies a prompt-contract gap: the DEV-142 scorer requires
exact field values, ordered facts, diagnostic identities, and warning
arithmetic, while the parent task names only the eight output fields and does
not define the reviewed result grammar. Amend only the generic task text with
value-free precedence. An exact eight-field result passes through unchanged;
an exact applied `diagnostic_condensation` wrapper returns only its exact
eight-field `condensation`; otherwise parse only the closed start-of-line
DEV-142 protocol, first scalar occurrences, literal `|` fact lists, source-row
diagnostic and warning-representative JSON, base-10 warning count, and omitted
warning arithmetic. Ignore every other line and never paraphrase, invent,
normalize, reorder, deduplicate, infer from exit status, repair, or guess.

The task retains the same exact approved command once and no other tool call.
It contains no case ID, rendered hash, expected answer, case-derived value, raw
result, transcript, telemetry content, private path, or credential. Preserve
the exact corpus, output schema, scorer, correctness oracle, hook, provider,
request and turn counts, Apple-attempt rule, cleanup, privacy, evidence, and
release gates.

After focused and full deterministic gates, SDK compilation,
generated-artifact checks, and a formal high-reasoning diff review pass,
commit one new clean candidate and run exactly one native Codex `0.145.0`
`--through usage-dry-run` row. Only a pass authorizes one complete benchmark
execution. This is a new prompt-corrected candidate, not a retry of
`4700074fd34383c03f1c25de1103bd632f327e7b` or an earlier terminal. A
non-pass is terminal and authorizes no executable substitution or retry.

## 2026-08-04 composite Codex stderr attribution correction

Candidate `06103a54008ef85f67fc60a6785552f3100ac6d7` passed its native
usage dry row. Its single complete run stopped at
`blocked:provider_request_counter_invalid / process_exit /
error_then_turn_failed`; one explicitly authorized exceptional unchanged
complete execution later stopped at `blocked:codex_stderr_unclassified /
stdin`. Preserve both terminals in Linear history; do not retry or relabel
either execution.

Pinned Codex `0.145.0` source commit `25af12f7` proves that a positional
prompt with non-terminal stdin first emits the exact accepted 39-byte
OptionalAppend notice, and a later failure can append another stderr producer.
The current first-prefix diagnostic therefore attributes a composite buffer
to the benign `stdin` prefix and hides the later producer.

After clearing captured stderr, when and only when the transient value is
bytes and the exact Codex version, source commit, and non-terminal-stdin
bindings match, remove exactly one leading exact 39-byte notice from a larger
transient value solely for closed stage attribution. The larger value remains
blocked. Empty stderr and the exact standalone notice remain the only accepted
values. Do not decode, trim, normalize, search, use regular expressions,
recursively remove notices, retain a suffix, add a stage, or change evidence.
Wrong version, source, or stdin-mode composite values map to `unknown`; a
second notice remains `stdin` after the single removal.

Add regressions for every existing known suffix, an unknown suffix, all three
authorization-guard failures, duplicate notices followed by another known
prefix, unconditional buffer clearing, and closed terminal serialization.
After focused and full deterministic gates, SDK compilation,
generated-artifact and evidence-safety checks, ancestry and diff checks, and
formal high-reasoning exact-diff review, commit one clean successor and run
exactly one native usage dry row. Only a pass authorizes its single complete
execution; every non-pass is terminal without retry, substitution, or
relabeling.

## 2026-08-04 minimized Apple context correction

Candidate `7b5baf194f98eb108c7580c3e93eee53e9a6370e` passed its native usage
dry row. Its single complete 24-pair/48-arm run then failed release with
median reduction `-18501` PPM, zero correctness regressions, zero additional
requests or turns, zero command reruns, zero cleanup or unsafe-evidence
findings, zero Apple attempts, and zero validated applied rows. Every one of
the 24 plugin-on zero-attempt rows had the closed preflight attribution
`context_budget_exceeded`. Preserve that terminal in Linear history; do not
retry or relabel it. Its validated fail artifact is not release evidence and
was moved recoverably out of the required output path.

Static inspection proves that `makeConstrainedSchema` already binds every
generated scalar to the exact minimized `sourceFacts` value and
`validatedCondensation` requires the reconstructed value to equal those
frozen facts. The Apple prompt nevertheless interpolates the entire verbose
`diagnosticText`, duplicating context that cannot add an accepted value. The
preflight counts fixed instructions, that verbose prompt, the constrained
schema, and the unchanged 1024-token response reserve before enforcing the
unchanged 75% context limit. That redundant transfer is the shared cause of
the uniform pre-generation decline.

Replace only the interpolated Apple prompt with one fixed value-free prompt:
`Return the exact literal values required by the constrained schema.` Keep
the bridge input shape for compatibility, but do not use `diagnosticText`
inside `consult`. Preserve the exact schema constants and ranges, fixed
instructions, token-count calls, response reserve, 75% guard, no-tools
session, greedy single response with a 1024-token maximum, one-attempt rule,
exact equality validation, error mapping, and untouched-original fallback.
This narrows Apple context and excludes the verbose original from the
successful path; it does not change an interface, oracle, evidence rule, or
release threshold.

Add one structural production regression for the fixed prompt, verbose-input
exclusion, bridge-input compatibility, schema constraints, equality oracle,
token-count path, and one-response/no-tools invariants. Mechanically refresh
only `productionPluginSha256` and `swiftSourceSha256`. After focused and full
deterministic gates, SDK 26.5 warnings-as-errors compilation,
generated-artifact and evidence-safety checks, diff and ancestry checks, and
formal high-reasoning exact-diff review, commit one clean successor and run
exactly one native usage dry row. Only a pass authorizes its single complete
execution; every non-pass is terminal without retry, substitution, or
relabeling.

## 2026-08-04 parent-boundary condensation correction

Candidate `ba56a20f3df9b658bc950578987178c0202a5676` passed its native usage
dry with one observed plugin-off arm and supported parent usage. Its single
complete invocation then stopped with the exact terminal
`correctness_oracle_failed / parent_outcome / quality_score`, wrote no
benchmark evidence, and cleaned its isolated host and run roots. Preserve
that terminal in Linear history; do not retry or relabel it.

The terminal does not identify the failing arm. The prior plugin-off dry pass,
the deterministic plugin-off-then-plugin-on execution order, and the static
interface mismatch make the plugin-on boundary the strongest inference, not
observed proof. Independently, static inspection proves that the application
validates a full applied DEV-142 result whose condensation exactly equals the
frozen `sourceFacts`, but then forwards the entire nested control-plane
envelope. The parent must unwrap that envelope to produce the strict
eight-field outcome even though the value-free task already accepts a bare
eight-field object unchanged.

Keep full DEV-142 result construction, routing, binding validation, exact
source-fact equality, size and savings gates, and every fallback application-
side. Only after `contract.validate_result(routed)` succeeds, serialize
`routed["condensation"]` as canonical UTF-8 JSON and use those exact bytes as
the block reason and replacement observation binding. Forward no wrapper
metadata or verbose original. Every decline, failure, malformed result, or
exception continues to return `None` and preserve the exact untouched
original.

Update the installed production proof to accept only a duplicate-free,
canonical eight-field condensation equal to `source_facts` derived from its
exact original input. It must reject the former full wrapper, altered facts,
missing or extra keys, duplicate keys, invalid UTF-8, noncanonical bytes, and
trailing content. Do not change the parent task, Swift bridge or hash, corpus,
scorer, correctness oracle, evidence schema, release arithmetic, command,
request, turn, Apple-attempt, or retry rules. Mechanically refresh only
`productionPluginSha256` and `pythonAdapterSha256`.

After focused and full deterministic gates, SDK 26.5 warnings-as-errors
compilation, generated-artifact and evidence-safety checks, diff and ancestry
checks, and formal high-reasoning exact-diff review, commit one clean
successor and run exactly one native usage dry row. Only a pass authorizes its
single complete execution; every non-pass is terminal without retry,
substitution, or relabeling.

## File structure

- Create `fixtures/runtime-v1-benchmark/README.md` — exact profile, denominators, privacy, blocker, and release rules.
- Create `fixtures/runtime-v1-benchmark/runtime_v1_benchmark.py` — closed Codex-only arm/pair/release validation and derivation.
- Create `tests/test_runtime_v1_benchmark.py` — schema, normalization, arithmetic, correctness, and safety tests.
- Modify `plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py` — optional production-safe normalized Task 3 observation sink; absent by default.
- Modify `tests/test_runtime_v1_production.py` — observation containment, schema, fallback, and single-attempt regression coverage.
- Create `tests/e2e/codex_runtime_v1_benchmark.py` — authorized outer 24-pair runner and normalized evidence writer.
- Create `tests/test_codex_runtime_v1_benchmark.py` — deterministic outer-runner and observation-consumer tests.
- Create `docs/research/evidence/runtime-v1-benchmark.json` — normalized 24-pair/48-arm evidence.
- Create `docs/research/runtime-v1-benchmark.md` — bounded verdict and limitations.
- Modify `docs/runtime-v1-installation.md` — packaging-readiness result only after the live matrix finishes.

The existing `fixtures/dev-142/runtime_contract.py`, corpus, evidence, and two-host validator remain byte-for-byte unchanged.

### Task 1: Refresh the merged production and usage boundaries

**Files:**
- Read: `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
- Read: `plugins/apple-foundation-models-handoff/hooks/codex/hooks.json`
- Read: `plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py`
- Read: `plugins/apple-foundation-models-handoff/runtime/DiagnosticCondenser.swift`
- Read: `tests/e2e/codex_runtime_v1_production.py`
- Read: `fixtures/dev-142/runtime_contract.py`
- Read: `fixtures/dev-142/benchmark-corpus.json`
- Modify only if a verified interface changed: `docs/superpowers/plans/2026-07-26-dev-255-runtime-v1-token-benchmark-and-packaging.md`

- [ ] **Step 1: Verify predecessor ancestry and state**

Run:

```bash
git status --short --branch
git merge-base --is-ancestor origin/main HEAD
python3 scripts/sync_generated_artifacts.py --check
```

Expected: clean DEV-255 branch from the merged DEV-254 baseline.

- [ ] **Step 2: Freeze the production and corpus identities**

Run:

```bash
shasum -a 256 \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json \
  plugins/apple-foundation-models-handoff/hooks/codex/hooks.json \
  plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py \
  plugins/apple-foundation-models-handoff/runtime/DiagnosticCondenser.swift \
  fixtures/dev-142/benchmark-corpus.json
```

Expected: five lowercase SHA-256 identities recorded in the transient run configuration and normalized evidence.

- [ ] **Step 3: Freeze the reviewed usage boundary**

Confirm the reviewed dry-row facts and official `rust-v0.145.0` semantics
match the frozen five-key contract and four-key DEV-142 mapping above. Do not
run Apple or a benchmark arm during this plan-refresh task. Task 4 repeats the
dry row through the tested benchmark parser before any matrix arm.

Expected: no optional usage field, inferred provider total, or double-counted
subset remains in the plan.

### Task 2: Add the independent Codex-only benchmark contract

**Files:**
- Create: `fixtures/runtime-v1-benchmark/README.md`
- Create: `fixtures/runtime-v1-benchmark/runtime_v1_benchmark.py`
- Create: `tests/test_runtime_v1_benchmark.py`

- [ ] **Step 1: Write the failing contract tests**

Define exact constants:

```python
PROFILE = "codex-runtime-v1-cost-v1"
REQUIRED_PAIRS = 24
REQUIRED_ARMS = 48
MINIMUM_MEDIAN_REDUCTION_PPM = 100_000
```

Test closed objects; duplicate/extra/missing identities; mismatched pair
coordinates; every missing and extra Codex usage key; `bool`, float, string,
negative, and unsigned-64 overflow values; cached-input, cache-write, and
reasoning subset violations; DEV-142 mapping and total mismatch; proof that
cache-write is recorded but not added; missing/multiple terminal events;
missing usage; zero plugin-off denominator; exactly 10%; below 10%;
even-count median; correctness regression; anything other than two parent
requests and one completed turn; Apple attempts; command rerun; blocked pair;
unsafe evidence; cleanup failure; and the 24-pair success case.

Add explicit RED cases proving that 24 arbitrary unique fixture IDs cannot
pass; a real fixture with the wrong rendered SHA-256, command class, or command
form blocks; a missing, extra, duplicate, or substituted DEV-142 corpus
identity blocks; and caller-forged `RuntimeV1PairScore` summaries cannot bypass
arm validation, pair scoring, or release derivation.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark -v
```

Expected: FAIL because the contract module does not exist.

- [ ] **Step 3: Implement the closed data model**

Import only DEV-142's `normalize_usage`, `BlockedEvidence`, and
`load_closed_json`; do not copy its normalization or change that module. Load
`fixtures/dev-142/benchmark-corpus.json`, require its frozen corpus SHA-256 and
exact 24 IDs, and derive one immutable map:

```text
fixture_id -> { rendered_sha256, command_class, command_form }
```

`validate_arm` requires every fixture ID to exist in that map and requires its
`fixture_sha256`, `command_class`, and `command_form` to equal the mapped
values. Use frozen dataclasses:

```python
@dataclass(frozen=True)
class RuntimeV1Usage:
    input_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_parent_tokens: int

@dataclass(frozen=True)
class RuntimeV1Arm:
    fixture_id: str
    fixture_sha256: str
    arm: str
    codex_version: str
    parent_model: str
    reasoning_effort: str
    provider: str
    provider_normalization: str
    policy_version: str
    command_class: str
    command_form: str
    task_prompt_sha256: str
    usage: RuntimeV1Usage
    parent_requests: int
    completed_parent_turns: int
    apple_attempts: int
    validated_applied: bool
    command_executions: int
    correctness_passed: bool
    cleanup_complete: bool

@dataclass(frozen=True)
class RuntimeV1ArmPair:
    plugin_off: RuntimeV1Arm
    plugin_on: RuntimeV1Arm

@dataclass(frozen=True)
class RuntimeV1PairScore:
    fixture_id: str
    reduction_ppm: int | None
    status: str
    reason_codes: tuple[str, ...]
    correctness_regressions: int
    additional_parent_requests: int
    additional_parent_turns: int
    apple_attempts: int
    validated_applied_rows: int
    command_reruns: int
    cleanup_failures: int
```

Expose exactly these interfaces:

```text
normalize_codex_usage(value: object) -> RuntimeV1Usage
validate_arm(value: object) -> RuntimeV1Arm
validate_arm_pair(value: object) -> RuntimeV1ArmPair
score_pair(off: object, on: object) -> RuntimeV1PairScore
release_gate(
    arm_pairs: list[object],
    *,
    unsafe_committed_evidence_findings: int,
) -> dict[str, object]
validate_evidence(value: object) -> None
```

The raw arm-pair input is a closed object with exactly
`plugin_off` and `plugin_on`; `validate_arm_pair` validates both nested raw arm
objects, exact roles, identical coordinates, and the wrapper's one immutable
DEV-142 corpus identity. `RuntimeV1PairScore` is derived output only and is
never accepted as release authority.

`normalize_codex_usage` first validates the exact five-key Codex object, then
calls DEV-142's `normalize_usage` with the exact four-key mapping above and
checks the returned fields and total. Do not call or modify DEV-142's 48-pair
`release_gate`; the successor release arithmetic is owned here.

- [ ] **Step 4: Implement the release gate**

`release_gate` first requires exactly one validated arm pair for every exact
DEV-142 corpus ID and no other identity. It calls `score_pair` itself for all
24 pairs and aggregates only those freshly derived scores; it rejects
`RuntimeV1PairScore` inputs and never trusts a caller-provided reduction,
counter, status, or reason. The release gate returns `pass` only when:

```python
len(derived_pairs) == 24
set(pair.fixture_id for pair in derived_pairs) == set(EXACT_DEV142_FIXTURE_IDS)
all(pair.status == "pass" for pair in derived_pairs)
median_reduction_ppm >= 100_000
correctness_regressions == 0
additional_parent_requests == 0
additional_parent_turns == 0
real_apple_attempts >= 1
validated_applied_rows >= 1
original_command_reruns == 0
cleanup_failures == 0
unsafe_committed_evidence_findings == 0
```

Each valid arm has `parent_requests == 2`,
`completed_parent_turns == 1`, and `command_executions == 1`. Sort the 24
integer reductions and define the median as the integer floor-average of
zero-based positions 11 and 12. Any missing required pair, blocked required
pair, zero denominator, unavailable normalization, schema/semantic drift, or
incomplete cleanup returns `blocked`; invariant and correctness violations
return `fail`.

`validate_evidence` validates the closed evidence shape, groups its 48 raw
arms into the same 24 closed arm-pair inputs, calls `release_gate`, and requires
the stored pair summaries, release object, counts, status, and reason codes to
equal the freshly derived values exactly. Evidence validation cannot accept a
stored pair or release summary as proof of its own derivation.

- [ ] **Step 5: Run GREEN and commit**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark \
  tests.test_dev_142_contract -v
git diff --check
git add fixtures/runtime-v1-benchmark tests/test_runtime_v1_benchmark.py
git commit -m "test(DEV-255): define Runtime V1 benchmark contract"
```

Expected: focused tests PASS and DEV-142 remains unchanged.

### Task 3: Build the authorized outer paired runner

**Files:**
- Modify: `plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py`
- Modify: `tests/test_runtime_v1_production.py`
- Create: `tests/e2e/codex_runtime_v1_benchmark.py`
- Create: `tests/test_codex_runtime_v1_benchmark.py`

- [ ] **Step 1: Write failing runner tests**

Test exact executable capture/recheck; clean candidate-commit capture/recheck;
production-commit ancestry; immutable pair coordinates; deterministic fixture
order; plugin-off isolation; plugin-on install/trust; one command; zero added
turns; actual usage extraction; Apple-attempt counting; correctness scoring;
monotonic latency; transient raw-data cleanup; atomic normalized writes;
resume rejection; and fail-closed cancellation. Test the pinned stderr
classifier with empty bytes and the exact 39-byte `OptionalAppend` notice as
the only accepted inputs. Reject a missing newline, CRLF, extra whitespace,
ANSI escapes, duplicated lines, any prefix or suffix, and the same notice
under a different Codex version or source commit. Prove the raw accepted bytes
are discarded immediately and every rejected case returns
`blocked:codex_stderr_unclassified`.

- [ ] **Step 2: Run runner tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_benchmark.RuntimeV1RunnerTests -v
```

Expected: FAIL because the runner does not exist.

- [ ] **Step 3: Add the optional normalized production observation boundary**

Keep the installed production default byte-for-byte equivalent in behavior:
when `RUNTIME_V1_BENCHMARK_OBSERVATION_PATH` is absent, select the existing
no-op observer, create no file, expose no new capability, and preserve every
current fallback. Only the authorized outer Task 3 runner may set the variable,
and only for `pluginOn`.

Use a regular file, not a FIFO: a FIFO can block the hook and weaken
original-result fallback. Before evaluation, require the value to be one
absolute path with the fixed basename `runtime-v1-observation.json` in an
already-created `.runtime-v1-observation` directory directly beneath the
captured `RUNTIME_V1_REPO_ROOT`. Capture that directory as a non-symlink
directory, require the leaf not to exist, and recheck the repository and
directory identities before open and after close. Open once with
`O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC` and mode `0o600`; require
a regular single-link file, write exactly one complete canonical UTF-8 JSON
line through the captured descriptor, `fsync`, close, and recheck. Reject
relative, outside-root, pre-existing, symlinked, multiply linked, changed-parent,
duplicate-write, partial-write, or identity-drift cases.

The one line is a closed tagged union with exactly these fields:

```text
schemaVersion = 1
event = "runtime_v1_observation"
status = "replacement_emitted" | "fallback" | "blocked"
reasonCode = null | "apple_attempt_count_uncertain" |
             "observation_invariant_failed"
appleAttempts = 0 | 1 | null
appleValidResults = 0 | 1
replacementEmitted = true | false
replacementSha256 = <64-lowercase-hex> | null
replacementBytes = <nonnegative int> | null
preReceiptHookLatencyNanoseconds = <nonnegative int>
appleLatencyNanoseconds = <nonnegative int> | null
appleLatencySamples = 0 | 1
```

Wrap the existing one-shot bridge call with `time.monotonic_ns()` and reduce
only the adapter-owned closed events into this record.
`replacement_emitted` requires `replacementEmitted = true`, one known Apple
attempt, one valid result, one Apple latency sample, and the exact replacement
hash/byte count successfully written and flushed to stdout before the receipt.
It does not claim provider receipt. A known untouched-original path is
`fallback` with `replacementEmitted = false` and
no replacement fields. A blocked record also has
`replacementEmitted = false`. If bridge completion or the attempt count is
uncertain, emit only the normalized `blocked` variant with null attempt and
Apple-latency values. Do not include or retain the observation path, prompt,
response, original output, replacement body, diagnostics, source facts,
provider data, Apple output, credentials, or reasoning.

Any configured observation capture, reduction, open, write, close, or recheck
failure before stdout must suppress the replacement and preserve the exact
original result. It must not call the bridge again, retry Apple generation, or
convert a fallback into an emitted result. For an applied benchmark response,
complete all identity rechecks first, serialize once, require a full stdout
write and successful flush, and then write the terminal receipt as the final
fallible operation. If that post-stdout receipt fails, emit no substitute
observation and let the outer runner block the arm; do not label the already
emitted response as fallback.
The outer runner treats a missing, malformed, blocked, inconsistent, or
duplicate observation as a blocked arm and deletes the observation file and
directory during mandatory cleanup.

`preReceiptHookLatencyNanoseconds` is the monotonic interval from immediately
before evaluation through the successful stdout flush and immediately before
the terminal receipt write. It deliberately excludes the receipt's own durable
write and process-exit time and must never be labelled total hook latency.

Add production RED/GREEN tests for: default-variable absence; exact
replacement-emitted, fallback, and blocked records; all tagged-union
invariants; monotonic
denominators; relative/outside/pre-existing/symlink/hard-link/parent-drift
rejection; `O_EXCL`/`O_NOFOLLOW`/mode `0o600`; short-write and recheck failure;
no sensitive or path-bearing content; exact original preservation on every
pre-stdout observation failure; stdout short-write/flush failure suppressing
the receipt; post-stdout receipt failure blocking measurement without a false
fallback; and proof that the bridge remains one-shot. Tests must also prove the
runner never accepts an observation-owned `validatedApplied` field and never
derives the arm's `validated_applied` from the observation alone.

- [ ] **Step 4: Implement fixed pair coordinates**

For each DEV-142 corpus case, bind:

```python
{
    "benchmarkProfile": "codex-runtime-v1-cost-v1",
    "fixtureID": case["id"],
    "fixtureSha256": case["renderedSha256"],
    "parentModel": exact_parent_model,
    "reasoningEffort": exact_reasoning_effort,
    "provider": "openai-responses-usage-v1",
    "codexVersion": "0.145.0",
    "policyVersion": "diagnostic-condensation-v1",
    "commandClass": case["commandClass"],
    "commandForm": case["commandForm"],
    "taskPromptSha256": task_prompt_sha256,
}
```

Also bind the candidate commit, production plugin tree SHA-256, generated
Codex manifest SHA-256, hooks manifest SHA-256, Python adapter SHA-256, Swift
source SHA-256, corpus SHA-256, and exact captured executable identity to the
run. Pair coordinates are the fields in the object above and must be identical
between arms; arm role and plugin installation state are the only intentional
differences. Reject drift before scoring.

The hash-bound task prompt contains the approved direct command and the fixed
parent-outcome schema only. It must not contain the fixture ID, fixture hash,
expected facts, expected diagnostics, expected answer, oracle values, or
rendered-case hash. It instructs the parent to execute the command exactly once,
make no other tool call, and serialize only facts derived from the observed
tool result into this exact closed object:

```text
commandOutcome, summary, summaryFacts, diagnostics, warningCount,
omittedWarningCount, nextAction, completionFacts
```

Those are exactly DEV-142's condensation fields. The prompt must not ask the
parent to repeat a known answer or copy a fixture identifier.

- [ ] **Step 5: Implement one arm runner**

Each arm must:

1. Create a fresh isolated root.
2. Capture and recheck the exact Codex executable.
3. Give both roles identical CLI/model/reasoning/config/task coordinates.
   Leave `pluginOff` in a fresh plugin-empty `CODEX_HOME`; install and trust the
   exact production plugin only for `pluginOn`.
4. Invoke the captured executable once with an argument list equivalent to:

   ```text
   <host-path> exec --ephemeral --json --strict-config
     --skip-git-repo-check --enable hooks
     --disable code_mode --disable code_mode_only
     -c web_search="disabled" -c approval_policy="never"
     -c model_reasoning_effort="medium"
     -m gpt-5.6-sol -s danger-full-access
     --output-last-message <transient-output>
     -C <isolated-workspace> <approved-hash-bound-task>
   ```

   Construct this as a subprocess argument list, never a shell string. The
   task instructs Codex to run the case's approved direct Bash command exactly
   once and to make no other tool call.
5. Before parsing or using stdout, OTel, or any other arm artifact, apply the
   closed stderr classifier: accept only empty bytes or, for exact Codex
   `0.145.0` bound to source commit `25af12f7` on the non-terminal-stdin
   `OptionalAppend` path, the exact 39-byte
   `b"Reading additional input from stdin...\n"` notice. Immediately discard
   the accepted raw buffer and retain at most `stderrBytes = 0 | 39`; block
   every other byte sequence as `blocked:codex_stderr_unclassified`.
6. Count exactly two `/responses` provider requests through the authorized
   outer request counter used by the dry protocol, without retaining request
   bodies. Every `codex.api_request` record must contain exactly one closed
   `event.name` and one closed `endpoint`; count only
   `endpoint = "/responses"` and reject malformed, duplicated, or missing
   discriminator attributes. Other well-formed endpoints such as `/models`
   are not parent turns. Parse transient JSONL as one closed stream:
   `thread.started`, one
   `turn.started`, bounded item events, and exactly one terminal
   `turn.completed`; reject `turn.failed`, top-level error, trailing records,
   open items, or a second terminal. If the supported request counter is
   unavailable, block rather than infer the count. Require exactly one command
   execution, exactly two normal `/responses` parent requests, and one
   completed parent turn.
7. Validate the exact five-key terminal usage and map it through DEV-142.
8. For `pluginOff`, require zero Apple attempts and no loaded/trusted plugin.
   For `pluginOn`, require at most one Apple attempt, no retry, and exactly one
   replacement-emitted or untouched-original fallback observation. Apple-only
   generation is the only extra generation relative to `pluginOff`. Set the
   optional observation path only for `pluginOn`; validate its exact one-line
   closed union, cross-check it against the arm role, and then delete it. Never
   read `validated_applied` from this record.
9. Parse `--output-last-message` with duplicate-key rejection as exactly the
   eight-field parent-outcome object above. Require it to equal the text of the
   final completion-only `agent_message`, reject a wrapper, prose, Markdown,
   extra or missing keys, invalid DEV-142 field shape, non-JSON trailing
   content, or an output larger than DEV-142's bound. Accept semantically valid
   JSON regardless of member order or insignificant JSON whitespace; after the
   duplicate-safe parse, canonicalize the closed object application-side for
   hashing and scoring. While the exact input and canonical bytes remain
   transient, bind the canonical SHA-256 to the candidate commit, pair coordinate,
   `taskPromptSha256`, case `renderedSha256`, and immutable DEV-142 oracle;
   construct the fixed applied DEV-142 scoring envelope, call
   `validate_result` and `score_condensation`, and derive
   `correctness_passed` only from `QualityScore.passed` with no reason codes.
   No caller-provided correctness flag is accepted. Score both arms
   independently against the same case, then delete the final-message bytes.
10. Record monotonic Apple, pre-receipt hook, and parent-turn latency with
   explicit numerators and denominators. Never report the pre-receipt interval
   as full hook latency.
11. Recheck executable, plugin/tree identities, manifest/hook trust, and
    toolchain identity.
12. Delete provider bodies, JSONL, diagnostics, Apple output, transcripts,
    compiled binaries, isolated configuration, and credentials.
13. Return only the closed normalized arm after proving the isolated root no
    longer exists.

No arm retries. Interruption or uncertain completion blocks its required pair.

The JSONL parser must implement the exact supported Codex `0.145.0` lifecycle
from official commit `25af12f7`. Accept only exact closed top-level shapes:
`thread.started` first, then one `turn.started`, bounded item records, and one
final `turn.completed`. Within this benchmark, accept only
`command_execution`, nonempty `reasoning`, and `agent_message` items. Every
item ID must match `item_[0-9]+` and be unique on first introduction.

`command_execution` is the only matched lifecycle: require exactly one
`item.started` with the exact closed command item shape and
`status = "in_progress"`, followed by exactly one `item.completed` with the
same ID, type, and command, exact completed command fields, terminal status,
aggregated output, and exit code. Reject completion before start, a changed
ID/type/command, duplicate start or completion, reuse, or an open command.
Both records contain exactly
`id, type, command, aggregated_output, exit_code, status`; the start has empty
aggregated output and null exit code, and the completion has status
`completed | failed | declined` with an integer or null exit code consistent
with the emitted terminal shape.

`agent_message` and nonempty `reasoning` are completion-only. Accept each only
as an exact closed `item.completed` whose item contains exactly
`id, type, text`, with its own new synthetic ID and nonempty text; reject any
`item.started` for either type, empty reasoning, duplicate or reused IDs, or
extra item fields. Require at least one completed
`agent_message`; the final item before `turn.completed` must be the completed
agent message whose text exactly equals `--output-last-message`. Reject
`item.updated`, unsupported item types or events, extra keys at any depth,
out-of-order records, records after terminal, and multiple terminals. Add
positive tests for official completion-only agent/reasoning records and
negative tests for every rejected case above. A merely parseable or
count-equivalent stream is not closed proof.

- [ ] **Step 6: Implement atomic evidence output**

Write exactly one closed top-level object:

```text
schemaVersion, benchmarkProfile, status, reasonCodes,
candidateCommit, productionIdentities, host,
usageContract, requiredPairs, requiredArms,
observedPairs, observedArms, arms, pairs, release
```

`usageContract` contains exact Codex version/model/reasoning, event name, the
five raw key names, the four-key DEV-142 mapping, subset semantics, and
`totalFormula = input_tokens + output_tokens`. Each arm contains only the
closed `RuntimeV1Arm` fields above plus normalized latency counts. `release`
contains exact denominators, median reduction PPM, correctness regressions,
additional parent requests, additional parent turns, real Apple attempts,
validated applied rows, command reruns, unsafe findings, cleanup failures,
status, and reason codes.

Reject private absolute paths, credential forms, prompt/result/transcript
keys, original fixture text, raw JSONL/events, provider or Apple bodies,
reasoning, and malformed hashes before calling the existing atomic JSON
writer. A cleanup failure may write only a minimal normalized
`blocked:cleanup_incomplete` terminal record.

For `--through complete`, accept only the exact normalized output path
`docs/research/evidence/runtime-v1-benchmark.json`, require its existing
repository-contained parent identity, reject symlinks and pre-existing output,
and never create arbitrary parents. Candidate rechecks must allow exactly that
new path only after the final pre-write identity check; every other worktree
change remains `fail:candidate_identity_drift`. Dry-run and validation modes
allow no worktree change.

- [ ] **Step 7: Refresh identities, run deterministic GREEN, and commit**

After the production adapter and both Task 3 files are final, compute and bind
the exact current plugin-tree and adapter SHA-256 values under the standing
approval above. Recompute them from disk in tests, require every unchanged
manifest/Swift/corpus identity to equal its prior approved value, and prove the
installed plugin tree and trusted hook hash match the same captured bytes.
Placeholders, stale hashes, or self-attested command-line hashes block.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_production \
  tests.test_runtime_v1_benchmark \
  tests.test_codex_runtime_v1_benchmark -v
python3 scripts/sync_generated_artifacts.py --check
git diff --check
git add \
  plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py \
  tests/test_runtime_v1_production.py \
  tests/e2e/codex_runtime_v1_benchmark.py \
  tests/test_codex_runtime_v1_benchmark.py
git commit -m "test(DEV-255): add paired Runtime V1 benchmark runner"
```

Expected: deterministic production and runner tests PASS; all refreshed hashes
match current reviewed bytes; the runner no longer contains an unconditional
`apple_attempt_counter_unobservable` terminal; no live pair runs inside the
implementation session.

### Task 4: Execute 24 pairs and publish normalized evidence

**Files:**
- Create: `docs/research/evidence/runtime-v1-benchmark.json`
- Create: `docs/research/runtime-v1-benchmark.md`
- Modify: `docs/runtime-v1-installation.md`

- [ ] **Step 1: Preflight the complete run**

From an authorized outer Codex session, capture the exact Codex, Python,
`xcrun`, and Swift compiler executables; require Codex `0.145.0`,
`gpt-5.6-sol`, medium reasoning, authentication, plugin trust, SDK 26.5, Apple
availability, locale, the dry-row usage mapping, corpus and production
identities, and free temporary storage. Any missing prerequisite writes a
normalized blocker and stops before an Apple attempt or benchmark arm.

After Task 3 is committed, require a clean worktree and capture its exact
40-character lowercase `HEAD` as `approved_candidate_commit`. Prove
`6d336044b0c21dfeca485b6676a18d50bf085487` is an ancestor of that candidate,
pass both identities separately, and recheck `HEAD` equality before and after
every dry or live row. The dry row must finish clean. The complete run may
create only its authorized normalized output path; any other worktree change
is drift. The production commit identifies merged Runtime V1; the candidate
commit identifies the exact harness and contract under test. Missing ancestry
is `blocked:production_commit_not_contained`; candidate or unexpected worktree
drift is `fail:candidate_identity_drift`.

Before any provider-backed dry or live row, run the deterministic
current-candidate forwarding preflight described in the Sol/High amendment.
It must exercise the captured Codex `0.145.0` executable, exact installed
plugin/hook/adapter bytes, the stdout-precedes-receipt path, and a local
provider with synthetic content. Before using its stdout or recorded request
bodies, apply the same source-bound stderr byte classifier, discard accepted
raw stderr immediately, and block every unclassified byte as
`blocked:codex_stderr_unclassified`. While request bodies remain transient, prove
that the emitted replacement SHA-256 equals the only `function_call_output` in
request two, no function output exists in request one, the original tool-result
bytes are absent from the whole serialized second request, the `/responses`
request count is exactly two, the command count is exactly one, and the turn is
closed. Delete the bodies and isolated root, then retain only a normalized
result bound to the
candidate commit, executable version, Codex source commit `25af12f7`, plugin
tree, hook, and adapter hashes. A missing, stale, mismatched, or failed result
is `blocked:replacement_forwarding_unproven` and stops before an Apple attempt.
That blocked terminal must include the closed `failureStage` required by the
diagnosability amendment; it remains the only forwarding-preflight diagnostic.

Run the tested harness once through the plugin-off usage preflight:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_benchmark.py \
  --codex-executable <host-path> \
  --python-executable <host-path> \
  --approved-production-commit 6d336044b0c21dfeca485b6676a18d50bf085487 \
  --approved-candidate-commit <current-clean-task3-head> \
  --approved-plugin-sha256 <64-lowercase-hex> \
  --approved-hook-hash sha256:<64-lowercase-hex> \
  --through usage-dry-run
```

Require exactly one `turn.completed` event with the exact five-key usage
object, exactly two normal `/responses` parent requests, one completed parent
turn, no Apple attempt, no retry, accepted source-bound stderr with
`stderrBytes = 0 | 39`, and completed cleanup. The harness may print
only a normalized terminal record and must delete raw JSONL and the isolated
root.
Any mismatch stops before the matrix with
`blocked:provider_usage_schema_or_semantic_drift`.

For every live `pluginOn` row, derive `validated_applied` only after rechecking
the bound forwarding-preflight result and combining it with that row's
post-stdout `replacement_emitted` application receipt, exact two-`/responses`
OTel count, closed one-turn JSONL stream, one command execution, and correct
closed parent outcome. This per-row cross-check is the accepted production
effect proof. Neither OTel nor the observation is described as provider-body
evidence, and no provider body is retained.

- [ ] **Step 2: Run all required arms**

After the dry row passes, run the harness once with the exact captured
executables and approved hashes:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_benchmark.py \
  --codex-executable <host-path> \
  --python-executable <host-path> \
  --approved-production-commit 6d336044b0c21dfeca485b6676a18d50bf085487 \
  --approved-candidate-commit <current-clean-task3-head> \
  --approved-plugin-sha256 <64-lowercase-hex> \
  --approved-hook-hash sha256:<64-lowercase-hex> \
  --through complete \
  --output docs/research/evidence/runtime-v1-benchmark.json
```

The runner must reject placeholders; they identify values captured and
approved immediately before execution. Expected normalized denominators:

```text
requiredPairs = 24
requiredArms = 48
observedPairs = 24
observedArms = 48
```

Do not drop, repeat, replace, impute, or zero a row.

- [ ] **Step 3: Validate the release arithmetic**

Run:

```bash
python3 -m json.tool \
  docs/research/evidence/runtime-v1-benchmark.json >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark -v
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_benchmark.py \
  --validate-evidence docs/research/evidence/runtime-v1-benchmark.json
```

Expected: the evidence validates as exactly one `pass`, `blocked`, or `fail` verdict. Report the verdict truthfully.

- [ ] **Step 4: Write bounded interpretation and packaging result**

Record the evidence SHA-256, exact five-key usage contract and DEV-142
mapping, cache-write non-double-count rule, exact denominators, median
reduction, correctness regressions, added requests/turns, Apple attempts,
applied rows, reruns, safety findings, latency denominators, cleanup,
packaging/install result, proven claims, unproven claims, and stop/release
decision. Quote no provider, tool, or Apple content.

- [ ] **Step 5: Commit evidence**

Run:

```bash
git add \
  docs/research/evidence/runtime-v1-benchmark.json \
  docs/research/runtime-v1-benchmark.md \
  docs/runtime-v1-installation.md
git commit -m "test(DEV-255): record Runtime V1 benchmark verdict"
```

### Task 5: Run final regression and release review

**Files:**
- Verify all DEV-255 paths above.

- [ ] **Step 1: Run repository gates**

Run:

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: generator synchronized, full suite PASS except declared pre-existing skips, no diff errors, and only DEV-255 paths changed.

- [ ] **Step 2: Run Sol/High release review**

Review all 24 identities and 48 arms; exact five-key usage validation;
four-key DEV-142 mapping; independent cache-read, cache-write, and reasoning
subset checks; no subset double counting; total and median arithmetic;
correctness; exactly two requests and one completed turn per arm; Apple
attempts and no retry; reruns; latency denominators; evidence safety; cleanup;
production identity and packaging/install proof; DEV-142 byte immutability;
CI; and merge readiness. Resolve every actionable finding and rerun Step 1.

- [ ] **Step 3: Finish the issue**

Open one DEV-255 PR, wait for green CI, merge, verify remote containment and a clean synchronized worktree, then mark DEV-255 complete only when the normalized verdict satisfies the approved release gate. A `blocked` or `fail` verdict closes the run truthfully without a release claim.
