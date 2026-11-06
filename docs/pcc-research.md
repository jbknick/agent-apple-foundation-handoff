# Can apple-offload reach Private Cloud Compute?

Research for [#30](https://github.com/jbknick/agent-apple-foundation-handoff/issues/30), feeding
[#31](https://github.com/jbknick/agent-apple-foundation-handoff/issues/31). Researched 2026-11-06.

Every claim carries one evidence label:

- **Verified on hardware** — a command I ran on a Mac (macOS 27.0.1, build 26A434, Apple
  Intelligence on). Output is quoted below the table.
- **Documented by Apple** — an Apple page says so. Linked.
- **Unknown** — no source I could read settles it. Not guessed.

Community notes (WWDCNotes) are cited only as pointers and never upgrade a claim past
Unknown.

## Short answer

`/usr/bin/fm`, the only model route apple-offload uses, cannot reach PCC. It exposes one
model, `system`, the on-device model. PCC is reachable only from Swift through the
Foundation Models framework's `PrivateCloudComputeLanguageModel`, behind a managed
entitlement tied to the App Store Small Business Program. A PCC route would mean shipping a
small signed Swift helper, not changing a CLI flag.

## The five questions

### 1. Can we choose PCC?

| Claim | Evidence |
| --- | --- |
| `fm respond`, `fm available` and `fm serve` accept only `--model system`. | Verified on hardware (C1, C2) |
| `--model pcc` and `--model cloud` are rejected with "Please provide one of 'system'". | Verified on hardware (C2) |
| The `fm` binary contains no `PrivateCloudCompute` strings, and no `fm` help text mentions private, PCC or cloud. | Verified on hardware (C3) |
| In Swift, an app picks PCC by passing `PrivateCloudComputeLanguageModel()` to `LanguageModelSession`; the default session uses the on-device model. | Documented by Apple ([class reference](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel)) |
| `fm` gains PCC support in a later macOS release. | Unknown |

### 2. Can we tell which route ran?

| Claim | Evidence |
| --- | --- |
| The route is chosen by the caller (which model object the session was created with), so a Swift helper can record it itself. | Documented by Apple ([class reference](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel)) |
| A response carries a field saying which model or route served it. | Unknown — not in any page I could read |
| The framework falls back from PCC to on-device on its own. | Unknown — no mechanism documented; treat fallback as ours to implement |
| `fm respond -v` prints only "Creating session with default instructions"; it does not name a route. | Verified on hardware (C4) |

### 3. What does it require?

| Claim | Evidence |
| --- | --- |
| A managed PCC entitlement on the developer account, requested from Apple. | Documented by Apple ([Private Cloud Compute for developers](https://developer.apple.com/private-cloud-compute/)) |
| Enrollment in the App Store Small Business Program and fewer than 2 million first-time downloads across the developer's apps; over the cap, migrate within 6 months. | Documented by Apple ([same page](https://developer.apple.com/private-cloud-compute/)) |
| macOS 27.0 or later (also iOS, iPadOS, visionOS, watchOS 27). | Documented by Apple ([class reference](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel)) |
| A device and region that support Apple Intelligence. | Documented by Apple ([class reference](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel)) |
| Daily usage limits that vary by feature, request complexity and system demand. | Documented by Apple ([Foundation Models framework](https://developer.apple.com/foundation-models-framework/)) |
| An open-source CLI distributed outside the App Store qualifies for the entitlement. | Unknown — eligibility is written for App Store apps |
| An explicit iCloud sign-in requirement. | Unknown |

### 4. What privacy guarantees apply?

| Claim | Evidence |
| --- | --- |
| Request data is used only to answer the request and deleted afterwards; it is not retained, including in logs. | Documented by Apple ([PCC security overview](https://security.apple.com/blog/private-cloud-compute/)) |
| No remote shell or interactive debugging on PCC nodes; staff with admin access cannot see user data. | Documented by Apple ([same](https://security.apple.com/blog/private-cloud-compute/)) |
| Requests cannot be routed to specific nodes by user or content; an OHTTP relay hides the source IP. | Documented by Apple ([same](https://security.apple.com/blog/private-cloud-compute/)) |
| Software images of production builds are published for researchers and checked against a transparency log. | Documented by Apple ([same](https://security.apple.com/blog/private-cloud-compute/)) |
| Data still leaves the Mac. On-device is the only route where artifact text never crosses the network. | Documented by Apple (offline support differs: on-device works offline, PCC does not) |

The current product boundary in `CLAUDE.md` promises local-only processing. Any PCC route
changes that promise, so #29 has to land first and say so in user-facing text.

### 5. How does it fail?

| Claim | Evidence |
| --- | --- |
| The framework reports availability (`isAvailable`, `availability`) and quota (`quotaUsage`, `isLimitReached`) before a request. | Documented by Apple ([class reference](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel)) |
| Errors surface as `PrivateCloudComputeLanguageModel.Error`. | Documented by Apple ([Error](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel/error)) |
| The individual error cases (offline, quota, missing entitlement). | Unknown — the case list did not render for me |
| Unsupported model names fail fast in `fm` with exit status non-zero and no model call. | Verified on hardware (C2) |
| The on-device route is available on this Mac. | Verified on hardware (C5) |

## Recommendation for #31

Do not build #31 as written yet. Build it in two steps:

1. **Now:** make the route explicit in the runtime. Add a `route` field to runs (`on_device`
   today) and a provider interface that can hold more than one route, with fallback order from
   #29 and tests using `MockProvider` for success, fallback and both-failed. Report PCC as
   `unavailable: fm_has_no_pcc_model` from a real probe of `fm --help`, not a hard-coded
   value. This is useful whatever Apple does next.
2. **Later, only if both hold:** Apple confirms the entitlement covers a non-App-Store CLI, and
   the maintainer accepts shipping a signed Swift helper. Then the helper owns PCC calls,
   records which model object served each request, and apple-offload treats it as a second
   provider.

Smallest experiment to settle the open questions: ask Apple through the entitlement request
form whether a notarized CLI distributed via npm qualifies, and watch the next macOS seed's
`fm --help` for a new model.

## Command output

C1 — supported models:

```console
$ fm available --help
  OPTIONS
    -m, --model <model>  Model to check (system); checks all if omitted
$ fm respond --help | sed -n '/MODELS/,$p'
  MODELS
    system                  On-device Apple Foundation Model (default)
```

C2 — other model names are rejected:

```console
$ fm available --model pcc
Error: The value 'pcc' is invalid for '--model <model>'. Please provide one of 'system'.
$ fm respond --model cloud 'hi'
Error: The value 'cloud' is invalid for '--model <model>'. Please provide one of 'system'.
```

C3 — no PCC in the binary or help:

```console
$ strings /usr/bin/fm | grep -ci privatecloud
0
$ fm respond --help | grep -ci 'private\|pcc\|cloud'
0
$ fm serve --help | grep -ci 'private\|pcc\|cloud'
0
```

C4 — verbose output does not name a route:

```console
$ fm respond -v --no-stream -g 'Reply with the single word ok.'
Creating session with default instructions

Ok.
```

C5 — on-device availability:

```console
$ fm available
System model available
$ sw_vers
ProductVersion:		27.0.1
BuildVersion:		26A434
```

Not run: an offline repeat, and any PCC request (no entitlement, and `fm` has no PCC model).
