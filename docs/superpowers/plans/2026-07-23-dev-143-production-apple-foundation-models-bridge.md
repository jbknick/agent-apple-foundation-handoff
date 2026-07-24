# DEV-143 Production Apple Foundation Models Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the single local Swift Apple Foundation Models bridge that implements the frozen DEV-142 diagnostic-condensation process contract for the later Codex adapter.

**Architecture:** Add one macOS 26 Swift package with a focused `BridgeCore` library and a thin executable. The library performs strict JSON/schema validation, deterministic policy gates, one injected session call, generated-result validation, and one terminal response; the executable owns bounded stdin/stdout only.

**Tech Stack:** Swift 6.3.3, Swift Package Manager, Foundation, CryptoKit, FoundationModels SDK 26.5, XCTest, Python 3 repository verification.

## Global Constraints

- Spec sources: `docs/superpowers/specs/2026-07-23-codex-foundation-models-runtime-completion-design.md` and `docs/superpowers/specs/2026-07-21-dev-143-local-bridge-design.md`.
- Prerequisites: DEV-142 is Done at merged baseline `b6b2289`, and DEV-246 has recorded a passing exact Codex `0.145.0` model-visible result-replacement contract. Do not implement if DEV-246 is blocked or failed. Refresh this plan with Sol if the DEV-142 schema, reason codes, merged baseline, or DEV-246 capability boundary changes.
- Exact identities are `schemaVersion = 1`, `policyVersion = diagnostic-condensation-v1`, `action = condense_diagnostic_output`, and `resultType = diagnostic_condensation`.
- Input is 8,192–65,536 canonical UTF-8 bytes; applied output is at most 4,096 bytes and saves at least 4,096 bytes.
- Apple response budget is at most 1,024 tokens and total occupancy is at most 75 percent of `contextSize`.
- Only C0/C1 `trustedLocal` fields with `apple_on_device` destination and `ephemeral` retention are eligible.
- The bridge makes at most one Apple attempt and never executes or reruns the source command.
- No mobile app, Claude adapter, external model, PCC, credentials, paid service, network inference, chunking, retry, or provider abstraction.
- Default tests perform no live generation and require no Apple availability.
- Missing live prerequisites are `blocked`, never pass; committed evidence is normalized and contains no raw prompt, diagnostic, model output, private path, credential, transcript, trace, or `.xcresult`.

---

## File Structure

- Create `runtime/apple-foundation-models-bridge/Package.swift` — package products, targets, and macOS floor.
- Create `runtime/apple-foundation-models-bridge/Sources/BridgeCore/BridgeContract.swift` — exact request/result Codable types and policy constants.
- Create `runtime/apple-foundation-models-bridge/Sources/BridgeCore/StrictJSON.swift` — one-value, duplicate-key, finite-number, and closed-key validation.
- Create `runtime/apple-foundation-models-bridge/Sources/BridgeCore/BridgeSession.swift` — injected session and clock contracts.
- Create `runtime/apple-foundation-models-bridge/Sources/BridgeCore/BridgeEngine.swift` — deterministic validation, one attempt, and result validation.
- Create `runtime/apple-foundation-models-bridge/Sources/BridgeCore/FoundationModelsBridgeSession.swift` — SDK 26.5 availability, locale, token, and structured-generation boundary.
- Create `runtime/apple-foundation-models-bridge/Sources/apple-foundation-models-bridge/main.swift` — bounded process entry point.
- Create `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/BridgeContractTests.swift` — strict schema and binding tests.
- Create `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/BridgeEngineTests.swift` — deterministic fake-session routing tests.
- Create `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/BridgeProcessTests.swift` — child-process cardinality and privacy tests.
- Create `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/FoundationModelsInterfaceTests.swift` — compile/interface-only SDK assertions.
- Create `runtime/apple-foundation-models-bridge/Sources/apple-foundation-models-bridge-live-proof/main.swift` — opt-in normalized live proof.
- Create `docs/research/evidence/dev-143-bridge.json` — normalized deterministic and live status summary.
- Modify `tests/test_dev_142_contract.py` — assert the Swift mirror retains DEV-142 identities and bounds.

### Task 1: Scaffold the package and freeze the process types

**Files:**
- Create: `runtime/apple-foundation-models-bridge/Package.swift`
- Create: `runtime/apple-foundation-models-bridge/Sources/BridgeCore/BridgeContract.swift`
- Test: `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/BridgeContractTests.swift`

**Interfaces:**
- Consumes: DEV-142 request/result field names and reason-code vocabulary.
- Produces: `BridgeRequest`, `BridgeResult`, `DiagnosticCondensation`, `BridgePolicy`, and `BridgeReason`.

- [ ] **Step 1: Write the failing policy-identity test**

```swift
import XCTest
@testable import BridgeCore

final class BridgeContractTests: XCTestCase {
    func testPolicyIdentityIsFrozen() {
        XCTAssertEqual(BridgePolicy.schemaVersion, 1)
        XCTAssertEqual(BridgePolicy.policyVersion, "diagnostic-condensation-v1")
        XCTAssertEqual(BridgePolicy.action, "condense_diagnostic_output")
        XCTAssertEqual(BridgePolicy.resultType, "diagnostic_condensation")
        XCTAssertEqual(BridgePolicy.inputBytes, 8_192...65_536)
        XCTAssertEqual(BridgePolicy.maximumOutputBytes, 4_096)
        XCTAssertEqual(BridgePolicy.minimumSavingsBytes, 4_096)
    }
}
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
cd runtime/apple-foundation-models-bridge
swift test --filter BridgeContractTests.testPolicyIdentityIsFrozen
```

Expected: FAIL because the package and `BridgePolicy` do not exist.

- [ ] **Step 3: Add the package and exact public contract**

```swift
// Package.swift
// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "apple-foundation-models-bridge",
    platforms: [.macOS(.v26)],
    products: [
        .library(name: "BridgeCore", targets: ["BridgeCore"]),
        .executable(name: "apple-foundation-models-bridge", targets: ["apple-foundation-models-bridge"]),
        .executable(name: "apple-foundation-models-bridge-live-proof", targets: ["apple-foundation-models-bridge-live-proof"]),
    ],
    targets: [
        .target(name: "BridgeCore"),
        .executableTarget(name: "apple-foundation-models-bridge", dependencies: ["BridgeCore"]),
        .executableTarget(name: "apple-foundation-models-bridge-live-proof", dependencies: ["BridgeCore"]),
        .testTarget(name: "BridgeCoreTests", dependencies: ["BridgeCore"]),
    ]
)
```

```swift
// Sources/BridgeCore/BridgeContract.swift
import Foundation

public enum BridgePolicy {
    public static let schemaVersion = 1
    public static let policyVersion = "diagnostic-condensation-v1"
    public static let action = "condense_diagnostic_output"
    public static let resultType = "diagnostic_condensation"
    public static let inputBytes = 8_192...65_536
    public static let maximumOutputBytes = 4_096
    public static let minimumSavingsBytes = 4_096
    public static let maximumResponseTokens = 1_024
}

public enum BridgeReason: String, Codable, CaseIterable {
    case toolNotAllowed = "tool_not_allowed"
    case commandNotAllowed = "command_not_allowed"
    case compoundCommand = "compound_command"
    case dataPolicyDenied = "data_policy_denied"
    case inputBelowMinimum = "input_below_minimum"
    case inputAboveMaximum = "input_above_maximum"
    case appleUnavailable = "apple_unavailable"
    case localeUnsupported = "locale_unsupported"
    case contextBudgetExceeded = "context_budget_exceeded"
    case generationDeclined = "generation_declined"
    case cancelled
    case deadlineExceeded = "deadline_exceeded"
    case invalidResponse = "invalid_response"
    case insufficientRealizedSavings = "insufficient_realized_savings"
    case hostReplacementUnavailable = "host_replacement_unavailable"
    case hostReplacementFailed = "host_replacement_failed"
    case contractInvariantFailed = "contract_invariant_failed"
}
```

Define closed Codable records matching the DEV-142 field list exactly. Use explicit `CodingKeys`, nonoptional required fields, and distinct `AppliedResult` and `FallbackResult` payloads so `BridgeResult` can encode only one terminal shape.

- [ ] **Step 4: Run the contract tests**

Run: `swift test --filter BridgeContractTests`

Expected: PASS with zero failures.

- [ ] **Step 5: Commit the frozen types**

```bash
git add runtime/apple-foundation-models-bridge
git commit -m "feat(dev-143): scaffold the bridge contract"
```

### Task 2: Reject malformed or open JSON before decoding

**Files:**
- Create: `runtime/apple-foundation-models-bridge/Sources/BridgeCore/StrictJSON.swift`
- Modify: `runtime/apple-foundation-models-bridge/Sources/BridgeCore/BridgeContract.swift`
- Test: `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/BridgeContractTests.swift`

**Interfaces:**
- Consumes: raw stdin `Data` and a closed key tree for DEV-142 request/result shapes.
- Produces: `StrictJSON.decodeRequest(_:) throws -> BridgeRequest` and `StrictJSON.encodeResult(_:) throws -> Data`.

- [ ] **Step 1: Add RED cases for duplicate, unknown, multiple, nonfinite, and invalid UTF-8 inputs**

```swift
func testStrictRequestRejectsMalformedJSON() throws {
    let invalid = [
        #"{"schemaVersion":1,"schemaVersion":1}"#,
        #"{"schemaVersion":1,"unknown":true}"#,
        #"{}{}"#,
        #"{"inputBytes":NaN}"#,
    ]
    for payload in invalid {
        XCTAssertThrowsError(try StrictJSON.decodeRequest(Data(payload.utf8)))
    }
    XCTAssertThrowsError(try StrictJSON.decodeRequest(Data([0xff])))
}
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `swift test --filter BridgeContractTests.testStrictRequestRejectsMalformedJSON`

Expected: FAIL because `StrictJSON` does not exist.

- [ ] **Step 3: Implement strict validation in two passes**

Implement a UTF-8 lexer that walks exactly one JSON value, tracks object keys per nesting level, rejects duplicate keys, nonfinite constants, trailing content, excessive nesting, and control characters. After the lexical pass, use `JSONSerialization` to validate the exact allowed key sets recursively, then `JSONDecoder` to construct `BridgeRequest`.

```swift
public enum StrictJSON {
    public static let maximumInputBytes = 1_048_576

    public static func decodeRequest(_ data: Data) throws -> BridgeRequest {
        guard !data.isEmpty, data.count <= maximumInputBytes else {
            throw BridgeContractError.invalidJSON
        }
        try JSONLexicalValidator(data: data).validateSingleValue()
        let object = try JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed])
        try ClosedSchema.request.validate(object)
        return try JSONDecoder().decode(BridgeRequest.self, from: data)
    }

    public static func encodeResult(_ result: BridgeResult) throws -> Data {
        let data = try JSONEncoder.canonical.encode(result)
        guard data.count <= BridgePolicy.maximumOutputBytes else {
            throw BridgeContractError.outputTooLarge
        }
        return data
    }
}
```

The canonical encoder must use `.sortedKeys`, `.withoutEscapingSlashes`, and no pretty printing or trailing newline.

- [ ] **Step 4: Run all contract tests**

Run: `swift test --filter BridgeContractTests`

Expected: PASS; every malformed row is rejected before a session exists.

- [ ] **Step 5: Commit strict JSON**

```bash
git add runtime/apple-foundation-models-bridge
git commit -m "feat(dev-143): enforce strict bridge JSON"
```

### Task 3: Implement deterministic policy and one-attempt orchestration

**Files:**
- Create: `runtime/apple-foundation-models-bridge/Sources/BridgeCore/BridgeSession.swift`
- Create: `runtime/apple-foundation-models-bridge/Sources/BridgeCore/BridgeEngine.swift`
- Test: `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/BridgeEngineTests.swift`

**Interfaces:**
- Consumes: `BridgeRequest`, `BridgeEnvironment`, and injected `BridgeSession`.
- Produces: `BridgeEngine.run(request:) async -> BridgeResult`.

- [ ] **Step 1: Write RED tests for decline, one attempt, cancellation, deadline, binding drift, and realized savings**

```swift
actor FakeSession: BridgeSession {
    private(set) var calls = 0
    let result: DiagnosticCondensation

    init(result: DiagnosticCondensation) { self.result = result }

    func condense(_ request: BridgeRequest, deadline: ContinuousClock.Instant) async throws -> DiagnosticCondensation {
        calls += 1
        return result
    }
}

func testValidRequestAttemptsSessionOnce() async throws {
    let session = FakeSession(result: .validFixture)
    let engine = BridgeEngine(session: session, environment: .eligibleFixture)
    let result = await engine.run(request: .validFixture)
    XCTAssertEqual(result.outcome, .applied)
    XCTAssertEqual(await session.calls, 1)
}
```

Add table cases for every `BridgeReason`, including no session call for all preflight declines and exactly one call for generation/validation failures.

- [ ] **Step 2: Run the engine tests and confirm RED**

Run: `swift test --filter BridgeEngineTests`

Expected: FAIL because `BridgeSession`, `BridgeEnvironment`, and `BridgeEngine` do not exist.

- [ ] **Step 3: Implement the injected orchestration boundary**

```swift
public protocol BridgeSession: Sendable {
    func condense(
        _ request: BridgeRequest,
        deadline: ContinuousClock.Instant
    ) async throws -> DiagnosticCondensation
}

public struct BridgeEnvironment: Sendable {
    public let appleAvailable: Bool
    public let localeSupported: Bool
    public let occupiedTokens: Int
    public let contextSize: Int
    public let deadline: ContinuousClock.Instant
}

public struct BridgeEngine: Sendable {
    let session: any BridgeSession
    let environment: BridgeEnvironment

    public func run(request: BridgeRequest) async -> BridgeResult {
        do {
            try request.validatePreflight(in: environment)
            let condensation = try await session.condense(request, deadline: environment.deadline)
            return try request.validatedAppliedResult(condensation)
        } catch let decline as BridgeDecline {
            return .fallback(request.bindings, outcome: .declined, reason: decline.reason)
        } catch is CancellationError {
            return .fallback(request.bindings, outcome: .fail, reason: .cancelled)
        } catch {
            return .fallback(request.bindings, outcome: .fail, reason: .contractInvariantFailed)
        }
    }
}
```

`validatePreflight` must recompute canonical bytes and estimated savings, enforce exact bindings/data grants, verify 75-percent occupancy using checked integer arithmetic, and reject before calling the session. `validatedAppliedResult` must verify semantic facts, digest/bindings, output size, and realized savings.

- [ ] **Step 4: Run the engine tests**

Run: `swift test --filter BridgeEngineTests`

Expected: PASS with fake-session calls equal to zero or one exactly as specified.

- [ ] **Step 5: Commit the deterministic engine**

```bash
git add runtime/apple-foundation-models-bridge
git commit -m "feat(dev-143): add deterministic bridge engine"
```

### Task 4: Add the SDK 26.5 Foundation Models session

**Files:**
- Create: `runtime/apple-foundation-models-bridge/Sources/BridgeCore/FoundationModelsBridgeSession.swift`
- Test: `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/FoundationModelsInterfaceTests.swift`

**Interfaces:**
- Consumes: validated allowlisted fields and a fixed instruction.
- Produces: one `DiagnosticCondensation` from `LanguageModelSession.respond`.

- [ ] **Step 1: Add a compile-only RED test target reference**

```swift
@available(macOS 26.0, *)
func typecheckProductionSession() {
    let session: any BridgeSession = FoundationModelsBridgeSession()
    _ = session
}
```

- [ ] **Step 2: Run the focused compile and confirm RED**

Run: `swift test --filter FoundationModelsInterfaceTests`

Expected: FAIL because `FoundationModelsBridgeSession` does not exist.

- [ ] **Step 3: Implement the production session with static structured output**

```swift
import FoundationModels

@available(macOS 26.0, *)
@Generable
struct GeneratedCondensation {
    let commandOutcome: String
    let summary: String
    let summaryFacts: [String]
    let diagnostics: [GeneratedDiagnostic]
    let warningCount: Int
    let omittedWarningCount: Int
    let nextAction: String
    let completionFacts: [String]
}

@available(macOS 26.0, *)
public struct FoundationModelsBridgeSession: BridgeSession {
    public init() {}

    public func condense(
        _ request: BridgeRequest,
        deadline: ContinuousClock.Instant
    ) async throws -> DiagnosticCondensation {
        let model = SystemLanguageModel.default
        guard model.availability == .available else { throw BridgeDecline(.appleUnavailable) }
        let options = GenerationOptions(maximumResponseTokens: BridgePolicy.maximumResponseTokens)
        let session = LanguageModelSession(model: model, instructions: FixedInstruction.text)
        let response = try await session.respond(
            to: request.allowedPrompt,
            generating: GeneratedCondensation.self,
            options: options
        )
        return try DiagnosticCondensation(validating: response.content)
    }
}
```

Use SDK 26.5 `tokenCount(for:)` overloads to compute prompt, instruction, schema, and reserved-response occupancy before `respond`. Wrap the call in an application-owned `ContinuousClock` deadline task group; map deadline expiry to `.deadlineExceeded` and preserve `CancellationError` separately. Map stable `LanguageModelSession.GenerationError` cases to the approved reason set without using OS 27 names.

- [ ] **Step 4: Run compile/interface and deterministic tests**

Run:

```bash
swift test --filter FoundationModelsInterfaceTests
swift test
swift build
```

Expected: PASS; no test invokes live generation.

- [ ] **Step 5: Commit the production session**

```bash
git add runtime/apple-foundation-models-bridge
git commit -m "feat(dev-143): add the local Foundation Models session"
```

### Task 5: Add the single-record executable and process tests

**Files:**
- Create: `runtime/apple-foundation-models-bridge/Sources/apple-foundation-models-bridge/main.swift`
- Test: `runtime/apple-foundation-models-bridge/Tests/BridgeCoreTests/BridgeProcessTests.swift`

**Interfaces:**
- Consumes: at most `StrictJSON.maximumInputBytes` from stdin.
- Produces: one canonical JSON record on stdout and one stable exit code.

- [ ] **Step 1: Write RED child-process assertions**

Assert valid, malformed, empty, oversized, duplicate, cancellation, and failure inputs produce exactly one newline-terminated JSON object, no raw payload on stderr, and exit after the first value.

- [ ] **Step 2: Run and confirm RED**

Run: `swift test --filter BridgeProcessTests`

Expected: FAIL because the executable has no entry point.

- [ ] **Step 3: Implement bounded process I/O**

```swift
import BridgeCore
import Foundation

@main
enum BridgeMain {
    static func main() async {
        let input = FileHandle.standardInput.readDataToEndOfFile()
        let result = await BridgeProcess.run(input)
        FileHandle.standardOutput.write(result.data)
        FileHandle.standardOutput.write(Data([0x0a]))
        Foundation.exit(result.exitCode)
    }
}
```

`BridgeProcess.run` must always produce a schema-valid normalized fallback when parsing cannot recover request bindings, use stable exit codes `0` for `applied`/`declined` and `1` for `fail`, write no payload-bearing diagnostics, and never read a second input.

- [ ] **Step 4: Run process and package verification**

Run:

```bash
swift test --filter BridgeProcessTests
swift test
swift build
```

Expected: PASS with exactly one terminal record per row.

- [ ] **Step 5: Commit the executable**

```bash
git add runtime/apple-foundation-models-bridge
git commit -m "feat(dev-143): add the bridge process protocol"
```

### Task 6: Add normalized live proof and repository integration evidence

**Files:**
- Create: `runtime/apple-foundation-models-bridge/Sources/apple-foundation-models-bridge-live-proof/main.swift`
- Create: `docs/research/evidence/dev-143-bridge.json`
- Modify: `tests/test_dev_142_contract.py`

**Interfaces:**
- Consumes: a supported local Apple runtime and one synthetic hash-bound request.
- Produces: metadata-only `compiled_sdk_26_5`, `interface_verified_sdk_26_5`, and live `pass`/`blocked` rows.

- [ ] **Step 1: Add RED repository assertions**

Add Python tests that load `BridgeContract.swift`, compare the four identities and numeric bounds to `fixtures/dev-142/runtime_contract.py`, and reject Claude/mobile/external-provider strings in the runtime package.

- [ ] **Step 2: Run and confirm RED**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract -v`

Expected: FAIL until the repository integration assertions and evidence file exist.

- [ ] **Step 3: Implement the live proof**

The executable must generate only from an approved synthetic request, print a single normalized record containing status, reason, SDK label, request/result hashes, byte counts, attempt count, and response-schema verdict, and omit all raw content. When availability or another prerequisite is missing, print `status=blocked` with a stable reason.

- [ ] **Step 4: Run the complete DEV-143 gate**

Run:

```bash
cd runtime/apple-foundation-models-bridge
swift test
swift build
cd ../..
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
bats tests/plugin_skeleton.bats
git diff --check
git status --short
```

Expected: all deterministic gates PASS; the live row is PASS only after actual generation, otherwise normalized BLOCKED; status shows only DEV-143 paths.

- [ ] **Step 5: Run required Sol review and commit evidence**

Sol must review API labels, schema parity, privacy, one-attempt behavior, and live-proof classification before the final issue commit.

```bash
git add runtime/apple-foundation-models-bridge docs/research/evidence/dev-143-bridge.json tests/test_dev_142_contract.py
git commit -m "test(dev-143): prove the local Apple bridge"
```

After review, open one DEV-143 PR, wait for green CI, merge, synchronize `main`, verify clean state, and only then unblock DEV-144.
