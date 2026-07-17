import Foundation

struct EffectSnapshot: Codable, Equatable {
    let effectID: String
    let stateVersion: Int
    let command: String
    let checkpoint: String
    let truth: String
    let reconciled: Bool
}

struct RecoverySnapshot: Codable, Equatable {
    let authority: String
    let finalResponseOwner: String
    let phase: String
    let stateVersion: Int
    let policyVersion: Int
    let transitionCount: Int
    let transitionBudget: Int
    let executorCommandCount: Int
    let effectCount: Int
    let pendingEffect: String
    let pendingTransition: String
    let checkpoint: String
    let stableCheckpoint: String
    let effectLedger: [EffectSnapshot]

    init(_ state: HandoffState) {
        authority = state.activeProfile
        finalResponseOwner = state.finalResponseOwner
        phase = state.phase.rawValue
        stateVersion = state.stateVersion
        policyVersion = state.policyVersion
        transitionCount = state.transitionCount
        transitionBudget = state.transitionBudget
        executorCommandCount = state.executorCommandCount
        effectCount = state.ledger.count
        pendingEffect = state.pendingEffectID ?? "none"
        pendingTransition = state.pendingTransition ?? "none"
        checkpoint = state.lastCheckpoint ?? "none"
        stableCheckpoint = state.lastStableCheckpoint
        effectLedger = state.ledger.map {
            EffectSnapshot(
                effectID: $0.effectID,
                stateVersion: $0.stateVersion,
                command: $0.command,
                checkpoint: $0.checkpoint,
                truth: $0.truth,
                reconciled: $0.reconciled
            )
        }
    }
}

struct RecoveryProbe: Codable {
    let before: RecoverySnapshot
    let after: RecoverySnapshot
    let outcome: String
    let commandEmitted: Bool
}

struct ContextProbe: Codable {
    let blockedPayload: [String: String]
    let rejectedLeakPayload: [String: String]
}

enum DeterministicScenarios {
    private static let effectID = "effect-001"

    private static func defaultContext() -> [ContextField] {
        [
            ContextField(
                name: "task_summary",
                outputLabel: "task_summary",
                dataClass: .c1TaskPrivate,
                included: true,
                redacted: false,
                sourceMetadata: "source:task"
            ),
            ContextField(
                name: "account_token",
                outputLabel: "account_token",
                dataClass: .c2Sensitive,
                included: false,
                redacted: false,
                sourceMetadata: "source:account"
            ),
            ContextField(
                name: "raw_secret",
                outputLabel: "raw_secret",
                dataClass: .c3NeverTransfer,
                included: false,
                redacted: false,
                sourceMetadata: "source:secret"
            ),
        ]
    }

    private static func grant(stateVersion: Int = 2, policyVersion: Int = 7) -> BoundaryGrant {
        BoundaryGrant(
            personID: "person-001",
            sessionID: "session-001",
            sourceProfile: "source",
            sourceProvider: "provider-a",
            destinationProfile: "destination",
            destinationProvider: "provider-b",
            purpose: "task-execution",
            allowedDataClasses: [.c1TaskPrivate, .c2Sensitive],
            allowedFields: ["task_summary", "customer_record"],
            allowedTool: "executor.run",
            retention: "ephemeral",
            expiresAt: 200,
            stateVersion: stateVersion,
            policyVersion: policyVersion,
            exceptionalC2Authorized: true
        )
    }

    private static func committedState() -> HandoffState {
        var state = HandoffState.initial
        state = HandoffReducer.reduce(state, event: .commitBaton).state
        state = HandoffReducer.reduce(state, event: .execute(effectID: effectID)).state
        return state
    }

    private static func consultationState() -> HandoffState {
        HandoffReducer.reduce(.initial, event: .completeConsultation).state
    }

    private static func recoveryState() -> HandoffState {
        HandoffReducer.reduce(
            committedState(),
            event: .commandUncertain(effectID: effectID)
        ).state
    }

    private static func base(_ caseID: String) -> ScenarioObservation {
        ScenarioObservation(
            schemaVersion: 1,
            caseID: caseID,
            pattern: .batonPass,
            sourceProfile: "source",
            sourceProvider: "provider-a",
            destinationProfile: "destination",
            destinationProvider: "provider-b",
            personID: "person-001",
            sessionID: "session-001",
            purpose: "task-execution",
            tool: "executor.run",
            retention: "ephemeral",
            routeAllowed: true,
            transitionEdgeAllowed: true,
            loopDetected: false,
            handoffCommitted: true,
            commandRequested: true,
            commandAuthorized: true,
            commandOriginTrusted: true,
            untrustedResultAccepted: false,
            requiredContextNames: ["task_summary"],
            context: defaultContext(),
            grant: grant(),
            now: 100,
            phaseRuleValid: true,
            duplicateLedgerDetected: false,
            replayCommandIssued: false,
            retryBeforeReconciliation: false,
            cancellationErasedRecovery: false,
            fallback: .none,
            fallbackExpandedTrust: false,
            transcriptBalanced: true,
            transcriptRepaired: false,
            rawEvidence: [],
            evidenceSanitized: true,
            rubricComplete: true,
            state: committedState()
        )
    }

    private static func consultation(_ caseID: String) -> ScenarioObservation {
        var observation = base(caseID)
        observation.pattern = .isolatedConsultation
        observation.state = consultationState()
        observation.grant = grant(stateVersion: 1)
        return observation
    }

    private static func setPrecommitState(
        _ observation: inout ScenarioObservation,
        event: TrustedEvent
    ) {
        observation.state = HandoffReducer.reduce(.initial, event: event).state
        observation.grant = grant(stateVersion: 1)
        observation.handoffCommitted = false
        observation.commandRequested = false
    }

    static func all() -> [ScenarioObservation] {
        var scenarios: [ScenarioObservation] = []

        scenarios.append(base("DEV138-BATON-VALID"))

        var budget = base("DEV138-BUDGET-EXCEEDED")
        budget.state.transitionCount = 3
        budget.state.auditEvents = ["transition:budget-exceeded"]
        scenarios.append(budget)

        var c2Redacted = base("DEV138-C2-REDACTED")
        c2Redacted.context = [
            ContextField(name: "customer_record", outputLabel: "customer_record:redacted", dataClass: .c2Sensitive, included: true, redacted: true, sourceMetadata: "source:customer"),
            ContextField(name: "customer_record", outputLabel: "customer_record:raw", dataClass: .c2Sensitive, included: false, redacted: false, sourceMetadata: "source:customer"),
            ContextField(name: "raw_secret", outputLabel: "raw_secret", dataClass: .c3NeverTransfer, included: false, redacted: false, sourceMetadata: "source:secret"),
            ContextField(name: "task_summary", outputLabel: "task_summary", dataClass: .c1TaskPrivate, included: true, redacted: false, sourceMetadata: "source:task"),
        ]
        c2Redacted.requiredContextNames = ["customer_record", "task_summary"]
        c2Redacted.state.auditEvents = ["context:C2:redacted", "handoff:committed"]
        scenarios.append(c2Redacted)

        var c2Unredacted = c2Redacted
        c2Unredacted.caseID = "DEV138-C2-UNREDACTED"
        c2Unredacted.context[0].outputLabel = "customer_record:raw"
        c2Unredacted.context[0].redacted = false
        c2Unredacted.context.remove(at: 1)
        c2Unredacted.state.auditEvents = ["context:C2:unredacted"]
        scenarios.append(c2Unredacted)

        var c3Blocked = base("DEV138-C3-BLOCKED")
        c3Blocked.context = [
            ContextField(name: "raw_secret", outputLabel: "raw_secret", dataClass: .c3NeverTransfer, included: false, redacted: false, sourceMetadata: "source:secret", value: "blocked-" + "c3-sentinel"),
            ContextField(name: "task_summary", outputLabel: "task_summary", dataClass: .c1TaskPrivate, included: true, redacted: false, sourceMetadata: "source:task"),
        ]
        c3Blocked.commandRequested = false
        c3Blocked.state.executorCommandCount = 0
        c3Blocked.state.ledger = []
        c3Blocked.state.auditEvents = ["context:C3:blocked", "handoff:committed"]
        scenarios.append(c3Blocked)

        var c3Leak = c3Blocked
        c3Leak.caseID = "DEV138-C3-LEAK"
        c3Leak.context[0].included = true
        c3Leak.commandRequested = true
        c3Leak.state.executorCommandCount = 1
        c3Leak.state.ledger = committedState().ledger
        c3Leak.state.auditEvents = ["context:C3:included"]
        scenarios.append(c3Leak)

        var cancellationErased = base("DEV138-CANCEL-ERASES-RECOVERY")
        cancellationErased.state.ledger = []
        cancellationErased.state.auditEvents = ["cancellation:erased-recovery", "ledger:erased"]
        cancellationErased.cancellationErasedRecovery = true
        scenarios.append(cancellationErased)

        var cancellationPrecommit = base("DEV138-CANCEL-PRECOMMIT")
        setPrecommitState(&cancellationPrecommit, event: .cancelPrecommit)
        scenarios.append(cancellationPrecommit)

        var cancellationUncertain = base("DEV138-CANCEL-UNCERTAIN")
        cancellationUncertain.state = HandoffReducer.reduce(
            recoveryState(),
            event: .cancelUncertain
        ).state
        scenarios.append(cancellationUncertain)

        scenarios.append(consultation("DEV138-CONSULTATION-VALID"))

        var requiredMissing = base("DEV138-CONTEXT-REQUIRED-MISSING")
        requiredMissing.context.removeAll(where: { $0.name == "task_summary" })
        requiredMissing.state.auditEvents = ["context:required-missing"]
        scenarios.append(requiredMissing)

        var edgeInvalid = base("DEV138-EDGE-INVALID")
        edgeInvalid.transitionEdgeAllowed = false
        edgeInvalid.state.auditEvents = ["transition:edge-invalid"]
        scenarios.append(edgeInvalid)

        var duplicateLedger = base("DEV138-EFFECT-DUPLICATE-LEDGER")
        duplicateLedger.state.ledger.append(duplicateLedger.state.ledger[0])
        duplicateLedger.duplicateLedgerDetected = true
        duplicateLedger.state.auditEvents = ["ledger:duplicate-effect-001"]
        scenarios.append(duplicateLedger)

        var replayCommand = base("DEV138-EFFECT-REPLAY-COMMAND")
        replayCommand.state = recoveryState()
        replayCommand.state.executorCommandCount = 2
        replayCommand.state.auditEvents = ["effect:replay-command", "pendingEffect=effect-001"]
        replayCommand.replayCommandIssued = true
        scenarios.append(replayCommand)

        var retryBeforeReconciliation = base("DEV138-EFFECT-RETRY-BEFORE-RECONCILE")
        retryBeforeReconciliation.state = recoveryState()
        retryBeforeReconciliation.state.executorCommandCount = 2
        retryBeforeReconciliation.state.auditEvents = ["effect:retry-before-reconcile", "pendingEffect=effect-001"]
        retryBeforeReconciliation.retryBeforeReconciliation = true
        scenarios.append(retryBeforeReconciliation)

        var evidenceLeak = base("DEV138-EVIDENCE-LEAKAGE")
        evidenceLeak.rawEvidence = [
            "classification=C2",
            "synthetic-" + "credential-sentinel",
            "/" + "Users/fixture/private",
            "session" + ".tr" + "ace",
            "raw-evidence-" + "payload",
        ]
        evidenceLeak.evidenceSanitized = false
        evidenceLeak.state.auditEvents = ["evidence:prohibited-content-detected", "evidence:redaction-failed"]
        scenarios.append(evidenceLeak)

        var unsafeFallback = base("DEV138-FALLBACK-EXPANDS-TRUST")
        unsafeFallback.fallback = .unsafeExpandedTrust
        unsafeFallback.fallbackExpandedTrust = true
        unsafeFallback.state.auditEvents = ["fallback:expanded-trust"]
        scenarios.append(unsafeFallback)

        var grantExpired = base("DEV138-GRANT-AUTH-EXPIRED")
        grantExpired.grant.expiresAt = 99
        grantExpired.state.auditEvents = ["grant:authorization-expired"]
        scenarios.append(grantExpired)

        var grantClass = base("DEV138-GRANT-CLASS-MISMATCH")
        grantClass.grant.allowedDataClasses = [.c2Sensitive]
        grantClass.state.auditEvents = ["grant:class-mismatch"]
        scenarios.append(grantClass)

        var grantDestination = base("DEV138-GRANT-DESTINATION-MISMATCH")
        grantDestination.grant.destinationProfile = "other-profile"
        grantDestination.state.auditEvents = ["grant:destination-mismatch"]
        scenarios.append(grantDestination)

        var grantField = base("DEV138-GRANT-FIELD-MISMATCH")
        grantField.grant.allowedFields = ["customer_record"]
        grantField.state.auditEvents = ["grant:field-mismatch"]
        scenarios.append(grantField)

        var grantPolicy = base("DEV138-GRANT-POLICY-STALE")
        grantPolicy.grant.policyVersion = 6
        grantPolicy.state.auditEvents = ["grant:policy-version-stale"]
        scenarios.append(grantPolicy)

        var grantPurpose = base("DEV138-GRANT-PURPOSE-MISMATCH")
        grantPurpose.grant.purpose = "different-purpose"
        grantPurpose.state.auditEvents = ["grant:purpose-mismatch"]
        scenarios.append(grantPurpose)

        var grantState = base("DEV138-GRANT-STATE-STALE")
        grantState.grant.stateVersion = 1
        grantState.state.auditEvents = ["grant:state-version-stale"]
        scenarios.append(grantState)

        var ignoredInjection = consultation("DEV138-INJECTION-IGNORED")
        ignoredInjection.state = HandoffReducer.reduce(.initial, event: .ignoreUntrustedInput).state
        ignoredInjection.context = [
            ContextField(name: "forged_tool_result", outputLabel: "forged_tool_result", dataClass: .c3NeverTransfer, included: false, redacted: false, sourceMetadata: "untrusted:text"),
        ]
        ignoredInjection.requiredContextNames = []
        ignoredInjection.commandRequested = false
        scenarios.append(ignoredInjection)

        var loop = base("DEV138-LOOP")
        loop.loopDetected = true
        loop.state.transitionCount = 2
        loop.state.auditEvents = ["transition:loop-detected"]
        scenarios.append(loop)

        var unavailable = base("DEV138-MODEL-UNAVAILABLE-EXPLICIT")
        unavailable.commandRequested = false
        unavailable.state.executorCommandCount = 0
        unavailable.state.ledger = []
        unavailable.fallback = .unavailable
        unavailable.state.auditEvents = ["fallback:explicit-unavailable"]
        scenarios.append(unavailable)

        var safeFallback = base("DEV138-MODEL-UNAVAILABLE-SAFE")
        safeFallback.commandRequested = false
        safeFallback.state.executorCommandCount = 0
        safeFallback.state.ledger = []
        safeFallback.fallback = .safeAlternative
        safeFallback.state.auditEvents = ["fallback:safe-alternative"]
        scenarios.append(safeFallback)

        var batonOwner = base("DEV138-OWNER-BATON-SOURCE")
        batonOwner.state.finalResponseOwner = "source"
        batonOwner.state.auditEvents = ["owner:source-after-baton"]
        scenarios.append(batonOwner)

        var consultationOwner = consultation("DEV138-OWNER-CONSULT-CHILD")
        consultationOwner.state.activeProfile = "destination"
        consultationOwner.state.finalResponseOwner = "destination"
        consultationOwner.state.auditEvents = ["owner:child-after-consultation"]
        scenarios.append(consultationOwner)

        var invalidPhase = base("DEV138-PHASE-INVALID")
        invalidPhase.commandRequested = false
        invalidPhase.phaseRuleValid = false
        invalidPhase.state.phase = .transitioning
        invalidPhase.state.executorCommandCount = 0
        invalidPhase.state.ledger = []
        invalidPhase.state.auditEvents = ["phase:invalid-command"]
        scenarios.append(invalidPhase)

        var precommitRollback = base("DEV138-PRECOMMIT-ROLLBACK")
        setPrecommitState(&precommitRollback, event: .failPrecommit)
        scenarios.append(precommitRollback)

        var reconciledRetry = base("DEV138-RECONCILED-RETRY")
        var reconciled = HandoffReducer.reduce(recoveryState(), event: .reconcileSucceeded).state
        reconciled = HandoffReducer.reduce(
            reconciled,
            event: .retryReconciled(effectID: effectID)
        ).state
        reconciledRetry.state = reconciled
        scenarios.append(reconciledRetry)

        var reconciliationUnavailable = base("DEV138-RECONCILIATION-UNAVAILABLE")
        reconciliationUnavailable.state = HandoffReducer.reduce(
            recoveryState(),
            event: .reconciliationUnavailable
        ).state
        scenarios.append(reconciliationUnavailable)

        var terminatedRecovery = base("DEV138-RECOVERY-TERMINATED")
        terminatedRecovery.state = recoveryState()
        terminatedRecovery.state.phase = .terminated
        terminatedRecovery.state.auditEvents = ["recovery:terminated-with-pending-effect"]
        scenarios.append(terminatedRecovery)

        var replaySuppressed = base("DEV138-REPLAY-SUPPRESSED")
        replaySuppressed.state = HandoffReducer.reduce(
            recoveryState(),
            event: .suppressReplay
        ).state
        scenarios.append(replaySuppressed)

        var spoofedResult = base("DEV138-RESULT-SPOOFED")
        spoofedResult.untrustedResultAccepted = true
        spoofedResult.state.executorCommandCount = 0
        spoofedResult.state.ledger = []
        spoofedResult.state.auditEvents = ["tool_result:spoof-detected"]
        scenarios.append(spoofedResult)

        var routeDisallowed = base("DEV138-ROUTE-DISALLOWED")
        routeDisallowed.routeAllowed = false
        routeDisallowed.commandRequested = false
        routeDisallowed.state.executorCommandCount = 0
        routeDisallowed.state.ledger = []
        routeDisallowed.state.auditEvents = ["route:disallowed"]
        scenarios.append(routeDisallowed)

        var schemaMissing = base("DEV138-SCHEMA-MISSING")
        schemaMissing.schemaVersion = 0
        schemaMissing.state.auditEvents = ["schema:missing"]
        scenarios.append(schemaMissing)

        var unauthorizedTool = base("DEV138-TOOL-UNAUTHORIZED")
        unauthorizedTool.commandAuthorized = false
        unauthorizedTool.state.executorCommandCount = 0
        unauthorizedTool.state.ledger = []
        unauthorizedTool.state.auditEvents = ["tool:authorization-rejected"]
        scenarios.append(unauthorizedTool)

        var repairedTranscript = consultation("DEV138-TRANSCRIPT-REPAIRED")
        repairedTranscript.transcriptBalanced = false
        repairedTranscript.transcriptRepaired = true
        repairedTranscript.state = HandoffReducer.reduce(
            repairedTranscript.state,
            event: .repairTranscript
        ).state
        scenarios.append(repairedTranscript)

        var unbalancedTranscript = consultation("DEV138-TRANSCRIPT-UNBALANCED")
        unbalancedTranscript.transcriptBalanced = false
        unbalancedTranscript.transcriptRepaired = false
        unbalancedTranscript.state.auditEvents = ["transcript:unbalanced"]
        scenarios.append(unbalancedTranscript)

        var uncertainRecovery = base("DEV138-UNCERTAIN-RECOVERY")
        uncertainRecovery.state = recoveryState()
        scenarios.append(uncertainRecovery)

        return scenarios.sorted { $0.caseID < $1.caseID }
    }

    static func mutation(named name: String) -> ScenarioObservation? {
        var observation = base("MUTATION-" + name.uppercased())

        switch name {
        case "tool_unauthorized":
            observation.commandAuthorized = false
        case "context_required_missing":
            observation.context.removeAll(where: { $0.name == "task_summary" })
        case "context_c3_leak":
            observation.context.append(
                ContextField(name: "never_transfer", outputLabel: "never_transfer", dataClass: .c3NeverTransfer, included: true, redacted: false, sourceMetadata: "source:secret")
            )
        case "phase_invalid":
            observation.phaseRuleValid = false
        case "effect_duplicate":
            observation.state.ledger.append(observation.state.ledger[0])
        case "effect_replay":
            observation.replayCommandIssued = true
        case "fallback_expands_trust":
            observation.fallbackExpandedTrust = true
        case "evidence_leak":
            observation.rawEvidence = ["private-evidence"]
            observation.evidenceSanitized = false
        case "rubric_incomplete":
            observation.rubricComplete = false
        case "grant_person_mismatch":
            observation.grant.personID = "other-person"
        case "grant_session_mismatch":
            observation.grant.sessionID = "other-session"
        case "grant_source_profile_mismatch":
            observation.grant.sourceProfile = "other-source"
        case "grant_source_provider_mismatch":
            observation.grant.sourceProvider = "other-provider"
        case "grant_destination_profile_mismatch":
            observation.grant.destinationProfile = "other-destination"
        case "grant_destination_provider_mismatch":
            observation.grant.destinationProvider = "other-provider"
        case "grant_purpose_mismatch":
            observation.grant.purpose = "other-purpose"
        case "grant_class_mismatch":
            observation.grant.allowedDataClasses = [.c2Sensitive]
        case "grant_field_mismatch":
            observation.grant.allowedFields = ["customer_record"]
        case "grant_tool_mismatch":
            observation.grant.allowedTool = "other.tool"
        case "grant_retention_mismatch":
            observation.grant.retention = "persistent"
        case "grant_expired":
            observation.grant.expiresAt = 99
        case "grant_exceptional_c2_missing":
            observation.context.append(
                ContextField(name: "customer_record", outputLabel: "customer_record:redacted", dataClass: .c2Sensitive, included: true, redacted: true, sourceMetadata: "source:customer")
            )
            observation.grant.exceptionalC2Authorized = false
        case "grant_state_version_stale":
            observation.grant.stateVersion = 1
        case "grant_policy_version_stale":
            observation.grant.policyVersion = 6
        default:
            return nil
        }

        return observation
    }

    static func recoveryProbe(named name: String) -> RecoveryProbe? {
        let before = recoveryState()
        let decision: ReducerDecision
        let outcome: String

        switch name {
        case "reconciliation-unavailable":
            decision = HandoffReducer.reduce(before, event: .reconciliationUnavailable)
            outcome = "repair-blocked/unavailable"
        case "replay-suppressed":
            decision = HandoffReducer.reduce(before, event: .suppressReplay)
            outcome = "replay-suppressed"
        default:
            return nil
        }

        return RecoveryProbe(
            before: RecoverySnapshot(before),
            after: RecoverySnapshot(decision.state),
            outcome: outcome,
            commandEmitted: decision.command != nil
        )
    }

    static func contextProbe() -> ContextProbe {
        let byID = Dictionary(uniqueKeysWithValues: all().map { ($0.caseID, $0) })
        return ContextProbe(
            blockedPayload: HandoffReducer.serializeContextForProvider(
                byID["DEV138-C3-BLOCKED"]!
            ),
            rejectedLeakPayload: HandoffReducer.serializeContextForProvider(
                byID["DEV138-C3-LEAK"]!
            )
        )
    }
}

@main
struct DeterministicScenarioRunner {
    static func main() throws {
        let arguments = Array(CommandLine.arguments.dropFirst())
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]

        if arguments.count == 2, arguments[0] == "--probe-recovery" {
            guard let probe = DeterministicScenarios.recoveryProbe(named: arguments[1]) else {
                FileHandle.standardError.write(Data("unknown recovery probe\n".utf8))
                Foundation.exit(2)
            }
            try write(probe, with: encoder)
            return
        }

        if arguments.count == 1, arguments[0] == "--probe-context" {
            try write(DeterministicScenarios.contextProbe(), with: encoder)
            return
        }

        let observations: [ScenarioObservation]

        if arguments.count == 2, arguments[0] == "--mutation" {
            guard let mutation = DeterministicScenarios.mutation(named: arguments[1]) else {
                FileHandle.standardError.write(Data("unknown mutation\n".utf8))
                Foundation.exit(2)
            }
            observations = [mutation]
        } else if arguments.isEmpty {
            observations = DeterministicScenarios.all()
        } else {
            FileHandle.standardError.write(Data("usage: dev-138-fixtures [--mutation NAME | --probe-recovery NAME | --probe-context]\n".utf8))
            Foundation.exit(2)
        }

        for observation in observations {
            let result = HandoffReducer.makeResult(observation)
            try write(result, with: encoder)
        }
    }

    private static func write<T: Encodable>(_ value: T, with encoder: JSONEncoder) throws {
        FileHandle.standardOutput.write(try encoder.encode(value))
        FileHandle.standardOutput.write(Data([0x0A]))
    }
}
