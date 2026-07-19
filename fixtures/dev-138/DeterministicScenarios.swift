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
    let repairFacts: RepairFacts
    let auditEvents: [String]

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
        repairFacts = state.repairFacts
        auditEvents = state.auditEvents
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
    private static let executorBinding = ToolBinding(
        name: "executor.run",
        version: "1.0",
        provider: "provider-b",
        resultType: "ExecutionReceipt"
    )

    private static func defaultContext(stateVersion: Int = 2) -> [ContextField] {
        [
            ContextField(
                name: "task_summary",
                outputLabel: "task_summary",
                dataClass: .c1TaskPrivate,
                included: true,
                redacted: false,
                sourceMetadata: "source:task",
                stateVersion: stateVersion
            ),
            ContextField(
                name: "account_token",
                outputLabel: "account_token",
                dataClass: .c2Sensitive,
                included: false,
                redacted: false,
                sourceMetadata: "source:account",
                stateVersion: stateVersion
            ),
            ContextField(
                name: "raw_secret",
                outputLabel: "raw_secret",
                dataClass: .c3NeverTransfer,
                included: false,
                redacted: false,
                sourceMetadata: "source:secret",
                stateVersion: stateVersion
            ),
        ]
    }

    private static func authorization(for state: HandoffState) -> ToolAuthorization {
        ToolAuthorization(
            actorProfile: state.activeProfile,
            callID: "call-001",
            binding: executorBinding,
            stateVersion: state.stateVersion,
            policyVersion: state.policyVersion
        )
    }

    private static func result(for state: HandoffState) -> ToolResult {
        ToolResult(
            callID: "call-001",
            binding: executorBinding,
            stateVersion: state.stateVersion
        )
    }

    private static func grant(
        fields: [ContextField],
        state: HandoffState,
        authorization: ToolAuthorization
    ) -> BoundaryGrant {
        let transferred = fields.filter {
            $0.included && ($0.dataClass == .c1TaskPrivate || $0.dataClass == .c2Sensitive)
        }
        let classes = Set(transferred.map(\.dataClass))
        return BoundaryGrant(
            personID: "person-001",
            sessionID: "session-001",
            sourceProfile: "source",
            sourceProvider: "provider-a",
            destinationProfile: "destination",
            destinationProvider: "provider-b",
            purpose: "task-execution",
            allowedDataClasses: classes,
            allowedFields: Set(transferred.map(\.name)),
            allowedTools: [authorization.binding],
            callID: authorization.callID,
            retention: "ephemeral",
            expiresAt: 200,
            stateVersion: state.stateVersion,
            policyVersion: state.policyVersion,
            exceptionalC2Permission: classes.contains(.c2Sensitive) ? "approved" : "not-required"
        )
    }

    private static func event(
        _ state: HandoffState,
        _ event: TrustedEvent
    ) -> EventRecord {
        EventRecord(
            event: event,
            before: state,
            decision: HandoffReducer.reduce(state, event: event)
        )
    }

    private static func batonExecution() -> (HandoffState, [EventRecord]) {
        var state = HandoffState.initial
        var records: [EventRecord] = []
        let proposal = event(
            state,
            .proposeBaton(proposal: HandoffProposal.fixture(from: state))
        )
        records.append(proposal)
        state = proposal.decision.state
        let commit = event(state, .commitBaton)
        records.append(commit)
        state = commit.decision.state
        var request = ExecutionRequest.fixture(state: state)
        request.effectID = effectID
        let execution = event(state, .execute(request: request))
        records.append(execution)
        state = execution.decision.state
        return (state, records)
    }

    private static func committedExecution() -> (HandoffState, [EventRecord]) {
        var state = HandoffState.initial
        var records: [EventRecord] = []
        let proposal = event(
            state,
            .proposeBaton(proposal: HandoffProposal.fixture(from: state))
        )
        records.append(proposal)
        state = proposal.decision.state
        let commit = event(state, .commitBaton)
        records.append(commit)
        state = commit.decision.state
        return (state, records)
    }

    private static func consultationExecution() -> (HandoffState, [EventRecord]) {
        let record = event(.initial, .completeConsultation)
        return (record.decision.state, [record])
    }

    private static func recoveryExecution() -> (HandoffState, [EventRecord]) {
        var (state, records) = batonExecution()
        let record = event(state, .commandUncertain(effectID: effectID))
        records.append(record)
        state = record.decision.state
        return (state, records)
    }

    private static func base(_ caseID: String) -> ScenarioObservation {
        let (state, records) = batonExecution()
        let context = defaultContext()
        let toolAuthorization = authorization(for: state)
        return ScenarioObservation(
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
            retention: "ephemeral",
            route: RouteContract(
                pattern: .batonPass,
                destinationProfile: "destination",
                destinationProvider: "provider-b",
                allowedEdges: [.sourceToDestination]
            ),
            requiredContextNames: ["task_summary"],
            context: context,
            grant: grant(fields: context, state: state, authorization: toolAuthorization),
            clock: 100,
            toolAuthorization: toolAuthorization,
            toolResult: result(for: state),
            evidence: [
                EvidenceRecord(
                    classification: .metadataOnly,
                    pathKind: .normalizedRelative,
                    artifactExtension: ".jsonl",
                    redaction: .redacted,
                    content: "case=DEV138;kind=metadata-only",
                    fingerprint: "sha256:" + SHA256.hexDigest(
                        "case=DEV138;kind=metadata-only"
                    )
                )
            ],
            state: state,
            eventRecords: records,
            recoveryBaseline: nil,
            auditFacts: ["commit:destination", "effect:effect-001"]
        )
    }

    private static func rebind(_ observation: inout ScenarioObservation) {
        for index in observation.context.indices {
            observation.context[index].sourceProfile = observation.sourceProfile
            observation.context[index].sourceProvider = observation.sourceProvider
            observation.context[index].subject = observation.personID
            observation.context[index].purpose = observation.purpose
            observation.context[index].destinationProfile = observation.destinationProfile
            observation.context[index].destinationProvider = observation.destinationProvider
            observation.context[index].retention = observation.retention
            observation.context[index].stateVersion = observation.state.stateVersion
            observation.context[index].policyVersion = observation.state.policyVersion
        }
        observation.toolAuthorization = authorization(for: observation.state)
        observation.toolResult = result(for: observation.state)
        observation.grant = grant(
            fields: observation.context,
            state: observation.state,
            authorization: observation.toolAuthorization
        )
    }

    private static func consultation(_ caseID: String) -> ScenarioObservation {
        var observation = base(caseID)
        let (state, records) = consultationExecution()
        observation.pattern = .isolatedConsultation
        observation.route.pattern = .isolatedConsultation
        observation.state = state
        observation.eventRecords = records
        observation.auditFacts = ["consultation:isolated", "owner:source"]
        rebind(&observation)
        return observation
    }

    private static func clearCommands(_ observation: inout ScenarioObservation) {
        observation.state.executorCommandCount = 0
        observation.state.commandHistory = []
        observation.state.ledger = []
        observation.toolResult = nil
    }

    private static func request(from observation: ScenarioObservation) -> ExecutionRequest {
        ExecutionRequest(
            effectID: effectID,
            requestedAt: observation.clock,
            requiredContextNames: observation.requiredContextNames,
            context: observation.context,
            grant: observation.grant,
            authorization: observation.toolAuthorization
        )
    }

    private static func applyExecutionAttempt(
        _ request: ExecutionRequest,
        to observation: inout ScenarioObservation,
        exposeRequestFacts: Bool = true
    ) {
        let (committed, records) = committedExecution()
        let attempt = event(committed, .execute(request: request))
        observation.state = attempt.decision.state
        observation.eventRecords = records + [attempt]
        observation.toolResult = nil
        if exposeRequestFacts {
            observation.requiredContextNames = request.requiredContextNames
            observation.context = request.context
            observation.grant = request.grant
            observation.toolAuthorization = request.authorization
        } else {
            rebind(&observation)
            observation.toolResult = nil
        }
    }

    static func all() -> [ScenarioObservation] {
        var scenarios: [ScenarioObservation] = []

        scenarios.append(base("DEV138-BATON-VALID"))

        var budget = base("DEV138-BUDGET-EXCEEDED")
        var exhausted = HandoffState.initial
        exhausted.transitionBudget = 0
        let budgetRefusal = event(
            exhausted,
            .proposeBaton(proposal: HandoffProposal.fixture(from: exhausted))
        )
        budget.state = budgetRefusal.decision.state
        budget.eventRecords = [budgetRefusal]
        budget.auditFacts = ["transition:budget-exceeded"]
        rebind(&budget)
        scenarios.append(budget)

        var c2Redacted = base("DEV138-C2-REDACTED")
        c2Redacted.context = [
            ContextField(name: "customer_record", outputLabel: "customer_record:redacted", dataClass: .c2Sensitive, included: true, redacted: true, sourceMetadata: "source:customer"),
            ContextField(name: "customer_record", outputLabel: "customer_record:raw", dataClass: .c2Sensitive, included: false, redacted: false, sourceMetadata: "source:customer"),
            ContextField(name: "raw_secret", outputLabel: "raw_secret", dataClass: .c3NeverTransfer, included: false, redacted: false, sourceMetadata: "source:secret"),
            ContextField(name: "task_summary", outputLabel: "task_summary", dataClass: .c1TaskPrivate, included: true, redacted: false, sourceMetadata: "source:task"),
        ]
        c2Redacted.requiredContextNames = ["customer_record", "task_summary"]
        c2Redacted.auditFacts = ["context:C2:redacted", "handoff:committed"]
        rebind(&c2Redacted)
        scenarios.append(c2Redacted)

        var c2Unredacted = c2Redacted
        c2Unredacted.caseID = "DEV138-C2-UNREDACTED"
        c2Unredacted.context[0].outputLabel = "customer_record:raw"
        c2Unredacted.context[0].redacted = false
        c2Unredacted.context.remove(at: 1)
        c2Unredacted.auditFacts = ["context:C2:unredacted", "refusal:context-envelope"]
        rebind(&c2Unredacted)
        applyExecutionAttempt(request(from: c2Unredacted), to: &c2Unredacted)
        scenarios.append(c2Unredacted)

        var c3Blocked = base("DEV138-C3-BLOCKED")
        c3Blocked.context = [
            ContextField(name: "raw_secret", outputLabel: "raw_secret", dataClass: .c3NeverTransfer, included: false, redacted: false, sourceMetadata: "source:secret", value: "blocked-" + "c3-sentinel"),
            ContextField(name: "task_summary", outputLabel: "task_summary", dataClass: .c1TaskPrivate, included: true, redacted: false, sourceMetadata: "source:task"),
        ]
        rebind(&c3Blocked)
        var blockedC3Request = request(from: c3Blocked)
        blockedC3Request.context[0].included = true
        applyExecutionAttempt(
            blockedC3Request,
            to: &c3Blocked,
            exposeRequestFacts: false
        )
        c3Blocked.auditFacts = ["context:C3:blocked", "handoff:committed"]
        scenarios.append(c3Blocked)

        var c3Leak = c3Blocked
        c3Leak.caseID = "DEV138-C3-LEAK"
        c3Leak.context[0].included = true
        rebind(&c3Leak)
        applyExecutionAttempt(request(from: c3Leak), to: &c3Leak)
        c3Leak.auditFacts = ["context:C3:included", "refusal:context-envelope"]
        scenarios.append(c3Leak)

        var cancellationErased = base("DEV138-CANCEL-ERASES-RECOVERY")
        let (recoveryBeforeCancellation, recoveryRecords) = recoveryExecution()
        var corruptedAfterCancellation = recoveryBeforeCancellation
        corruptedAfterCancellation.phase = .stable
        corruptedAfterCancellation.pendingEffectID = nil
        corruptedAfterCancellation.pendingTransition = nil
        corruptedAfterCancellation.lastCheckpoint = nil
        corruptedAfterCancellation.ledger = []
        corruptedAfterCancellation.repairFacts = .none
        let corruptedDecision = ReducerDecision(
            state: corruptedAfterCancellation,
            command: nil,
            disposition: .applied,
            outcome: .stateAdvanced,
            auditEvents: ["cancellation:erased-recovery"]
        )
        cancellationErased.state = corruptedAfterCancellation
        cancellationErased.eventRecords = recoveryRecords + [
            EventRecord(event: .cancelUncertain, before: recoveryBeforeCancellation, decision: corruptedDecision)
        ]
        cancellationErased.recoveryBaseline = recoveryBeforeCancellation
        cancellationErased.auditFacts = ["cancellation:erased-recovery", "ledger:erased"]
        rebind(&cancellationErased)
        scenarios.append(cancellationErased)

        var cancellationPrecommit = base("DEV138-CANCEL-PRECOMMIT")
        let proposalForCancellation = event(
            .initial,
            .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
        let cancellation = event(proposalForCancellation.decision.state, .cancelPrecommit)
        cancellationPrecommit.state = cancellation.decision.state
        cancellationPrecommit.eventRecords = [proposalForCancellation, cancellation]
        clearCommands(&cancellationPrecommit)
        cancellationPrecommit.auditFacts = ["cancellation:precommit", "rollback:source"]
        rebind(&cancellationPrecommit)
        scenarios.append(cancellationPrecommit)

        var cancellationUncertain = base("DEV138-CANCEL-UNCERTAIN")
        let (uncertainState, uncertainRecords) = recoveryExecution()
        let lateCancellation = event(uncertainState, .cancelUncertain)
        cancellationUncertain.state = lateCancellation.decision.state
        cancellationUncertain.eventRecords = uncertainRecords + [lateCancellation]
        cancellationUncertain.recoveryBaseline = uncertainState
        cancellationUncertain.auditFacts = ["cancellation:recorded", "checkpoint=uncertain", "recovery:preserved"]
        rebind(&cancellationUncertain)
        scenarios.append(cancellationUncertain)

        scenarios.append(consultation("DEV138-CONSULTATION-VALID"))

        var requiredMissing = base("DEV138-CONTEXT-REQUIRED-MISSING")
        requiredMissing.context.removeAll(where: { $0.name == "task_summary" })
        requiredMissing.auditFacts = ["context:required-missing", "refusal:context-envelope"]
        rebind(&requiredMissing)
        applyExecutionAttempt(request(from: requiredMissing), to: &requiredMissing)
        scenarios.append(requiredMissing)

        var edgeInvalid = base("DEV138-EDGE-INVALID")
        var edgeState = HandoffState.initial
        edgeState.allowedEdges = []
        let edgeRefusal = event(
            edgeState,
            .proposeBaton(proposal: HandoffProposal.fixture(from: edgeState))
        )
        edgeInvalid.state = edgeRefusal.decision.state
        edgeInvalid.eventRecords = [edgeRefusal]
        edgeInvalid.route.allowedEdges = []
        edgeInvalid.auditFacts = ["transition:edge-invalid", "refusal:transition"]
        rebind(&edgeInvalid)
        scenarios.append(edgeInvalid)

        var duplicateLedger = base("DEV138-EFFECT-DUPLICATE-LEDGER")
        duplicateLedger.state.ledger.append(duplicateLedger.state.ledger[0])
        duplicateLedger.auditFacts = ["ledger:duplicate-effect-001"]
        scenarios.append(duplicateLedger)

        var replayCommand = base("DEV138-EFFECT-REPLAY-COMMAND")
        let (replayRecovery, replayRecords) = recoveryExecution()
        replayCommand.state = replayRecovery
        let originalReplayCommand = replayCommand.state.commandHistory[0]
        replayCommand.state.commandHistory.append(
            ExecutorCommand(
                effectID: originalReplayCommand.effectID,
                callID: "call-001-replay",
                binding: originalReplayCommand.binding,
                stateVersion: originalReplayCommand.stateVersion,
                kind: .initial
            )
        )
        replayCommand.state.executorCommandCount = 2
        replayCommand.eventRecords = replayRecords
        replayCommand.auditFacts = ["effect:replay-command", "pendingEffect=effect-001", "refusal:replay"]
        rebind(&replayCommand)
        scenarios.append(replayCommand)

        var prematureRetryScenario = base("DEV138-EFFECT-RETRY-BEFORE-RECONCILE")
        let (retryRecovery, retryRecords) = recoveryExecution()
        prematureRetryScenario.state = retryRecovery
        let prematureRetry = ExecutorCommand(
            effectID: effectID,
            callID: "call-001-retry",
            binding: executorBinding,
            stateVersion: retryRecovery.stateVersion,
            kind: .retry
        )
        prematureRetryScenario.state.commandHistory.append(prematureRetry)
        prematureRetryScenario.state.executorCommandCount = 2
        prematureRetryScenario.eventRecords = retryRecords
        prematureRetryScenario.auditFacts = ["effect:retry-before-reconcile", "pendingEffect=effect-001", "refusal:retry"]
        rebind(&prematureRetryScenario)
        scenarios.append(prematureRetryScenario)

        var evidenceLeak = base("DEV138-EVIDENCE-LEAKAGE")
        let prohibitedEvidence = "synthetic-" + "credential-sentinel"
        evidenceLeak.evidence = [
            EvidenceRecord(
                classification: .rawContent,
                pathKind: .absolute,
                artifactExtension: ".tr" + "ace",
                redaction: .raw,
                content: prohibitedEvidence,
                fingerprint: "sha256:" + SHA256.hexDigest(prohibitedEvidence)
            )
        ]
        evidenceLeak.auditFacts = ["evidence:prohibited-content-detected", "evidence:redaction-failed"]
        scenarios.append(evidenceLeak)

        var unsafeFallback = base("DEV138-FALLBACK-EXPANDS-TRUST")
        let unsafeFallbackEvent = event(
            unsafeFallback.state,
            .modelAvailability(
                .degraded(
                    candidate: TrustBoundary(
                        providerRank: 3,
                        maximumDataClass: .c3NeverTransfer,
                        retentionRank: 2,
                        toolRank: 2,
                        effectBudget: 2
                    )
                )
            )
        )
        unsafeFallback.state = unsafeFallbackEvent.decision.state
        unsafeFallback.eventRecords.append(unsafeFallbackEvent)
        unsafeFallback.auditFacts = ["fallback:expanded-trust", "refusal:fallback"]
        scenarios.append(unsafeFallback)

        var grantExpired = base("DEV138-GRANT-AUTH-EXPIRED")
        grantExpired.grant.expiresAt = 99
        applyExecutionAttempt(request(from: grantExpired), to: &grantExpired)
        grantExpired.auditFacts = ["grant:authorization-expired", "refusal:grant"]
        scenarios.append(grantExpired)

        var grantClass = base("DEV138-GRANT-CLASS-MISMATCH")
        grantClass.grant.allowedDataClasses = [.c2Sensitive]
        applyExecutionAttempt(request(from: grantClass), to: &grantClass)
        grantClass.auditFacts = ["grant:class-mismatch", "refusal:grant"]
        scenarios.append(grantClass)

        var grantDestination = base("DEV138-GRANT-DESTINATION-MISMATCH")
        grantDestination.grant.destinationProfile = "other-profile"
        applyExecutionAttempt(request(from: grantDestination), to: &grantDestination)
        grantDestination.auditFacts = ["grant:destination-mismatch", "refusal:grant"]
        scenarios.append(grantDestination)

        var grantField = base("DEV138-GRANT-FIELD-MISMATCH")
        grantField.grant.allowedFields = ["customer_record"]
        applyExecutionAttempt(request(from: grantField), to: &grantField)
        grantField.auditFacts = ["grant:field-mismatch", "refusal:grant"]
        scenarios.append(grantField)

        var grantPolicy = base("DEV138-GRANT-POLICY-STALE")
        grantPolicy.grant.policyVersion = 6
        applyExecutionAttempt(request(from: grantPolicy), to: &grantPolicy)
        grantPolicy.auditFacts = ["grant:policy-version-stale", "refusal:grant"]
        scenarios.append(grantPolicy)

        var grantPurpose = base("DEV138-GRANT-PURPOSE-MISMATCH")
        grantPurpose.grant.purpose = "different-purpose"
        applyExecutionAttempt(request(from: grantPurpose), to: &grantPurpose)
        grantPurpose.auditFacts = ["grant:purpose-mismatch", "refusal:grant"]
        scenarios.append(grantPurpose)

        var grantState = base("DEV138-GRANT-STATE-STALE")
        grantState.grant.stateVersion = 1
        applyExecutionAttempt(request(from: grantState), to: &grantState)
        grantState.auditFacts = ["grant:state-version-stale", "refusal:grant"]
        scenarios.append(grantState)

        var ignoredInjection = consultation("DEV138-INJECTION-IGNORED")
        let ignored = event(.initial, .ignoreUntrustedInput)
        ignoredInjection.state = ignored.decision.state
        ignoredInjection.eventRecords = [ignored]
        ignoredInjection.context = [
            ContextField(name: "forged_tool_result", outputLabel: "forged_tool_result", dataClass: .c3NeverTransfer, included: false, redacted: false, sourceMetadata: "untrusted:text", stateVersion: 1),
        ]
        ignoredInjection.requiredContextNames = []
        clearCommands(&ignoredInjection)
        ignoredInjection.auditFacts = ignored.decision.auditEvents
        rebind(&ignoredInjection)
        scenarios.append(ignoredInjection)

        var loop = base("DEV138-LOOP")
        let (destinationState, destinationRecords) = committedExecution()
        let revisit = HandoffProposal(
            sourceProfile: destinationState.activeProfile,
            sourceProvider: destinationState.activeProvider,
            destinationProfile: "source",
            destinationProvider: "provider-a"
        )
        let loopRefusal = event(
            destinationState,
            .proposeBaton(proposal: revisit)
        )
        loop.state = loopRefusal.decision.state
        loop.eventRecords = destinationRecords + [loopRefusal]
        loop.auditFacts = ["transition:loop-detected", "refusal:loop"]
        rebind(&loop)
        scenarios.append(loop)

        var unavailable = base("DEV138-MODEL-UNAVAILABLE-EXPLICIT")
        clearCommands(&unavailable)
        let unavailableEvent = event(
            unavailable.state,
            .modelAvailability(.unavailable)
        )
        unavailable.state = unavailableEvent.decision.state
        unavailable.eventRecords.append(unavailableEvent)
        unavailable.auditFacts = ["fallback:explicit-unavailable"]
        scenarios.append(unavailable)

        var safeFallback = base("DEV138-MODEL-UNAVAILABLE-SAFE")
        clearCommands(&safeFallback)
        let safeFallbackEvent = event(
            safeFallback.state,
            .modelAvailability(
                .degraded(
                    candidate: TrustBoundary(
                        providerRank: 1,
                        maximumDataClass: .c1TaskPrivate,
                        retentionRank: 0,
                        toolRank: 1,
                        effectBudget: 0
                    )
                )
            )
        )
        safeFallback.state = safeFallbackEvent.decision.state
        safeFallback.eventRecords.append(safeFallbackEvent)
        safeFallback.auditFacts = ["fallback:safe-alternative"]
        scenarios.append(safeFallback)

        var batonOwner = base("DEV138-OWNER-BATON-SOURCE")
        batonOwner.state.finalResponseOwner = "source"
        batonOwner.auditFacts = ["owner:source-after-baton"]
        scenarios.append(batonOwner)

        var consultationOwner = consultation("DEV138-OWNER-CONSULT-CHILD")
        consultationOwner.state.activeProfile = "destination"
        consultationOwner.state.activeProvider = "provider-b"
        consultationOwner.state.finalResponseOwner = "destination"
        consultationOwner.auditFacts = ["owner:child-after-consultation"]
        rebind(&consultationOwner)
        scenarios.append(consultationOwner)

        var invalidPhase = base("DEV138-PHASE-INVALID")
        invalidPhase.state.phase = .transitioning
        invalidPhase.state.pendingTransition = nil
        clearCommands(&invalidPhase)
        invalidPhase.auditFacts = ["phase:invalid-command", "refusal:phase"]
        rebind(&invalidPhase)
        scenarios.append(invalidPhase)

        var precommitRollback = base("DEV138-PRECOMMIT-ROLLBACK")
        let proposalForFailure = event(
            .initial,
            .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
        let failure = event(proposalForFailure.decision.state, .failPrecommit)
        precommitRollback.state = failure.decision.state
        precommitRollback.eventRecords = [proposalForFailure, failure]
        clearCommands(&precommitRollback)
        precommitRollback.auditFacts = ["failure:precommit", "rollback:source"]
        rebind(&precommitRollback)
        scenarios.append(precommitRollback)

        var reconciledRetry = base("DEV138-RECONCILED-RETRY")
        var (reconciledState, reconciledRecords) = recoveryExecution()
        let reconciliation = event(
            reconciledState,
            .reconcileSucceeded(truth: .confirmedNotApplied)
        )
        reconciledRecords.append(reconciliation)
        reconciledState = reconciliation.decision.state
        let retry = event(reconciledState, .retryReconciled(effectID: effectID))
        reconciledRecords.append(retry)
        reconciledState = retry.decision.state
        reconciledRetry.state = reconciledState
        reconciledRetry.eventRecords = reconciledRecords
        reconciledRetry.auditFacts = [
            "reconciliation:confirmedNotApplied",
            "retry:effect-001",
        ]
        rebind(&reconciledRetry)
        scenarios.append(reconciledRetry)

        var reconciliationUnavailable = base("DEV138-RECONCILIATION-UNAVAILABLE")
        let (repairBlockedState, repairRecords) = recoveryExecution()
        let blocked = event(repairBlockedState, .reconciliationUnavailable)
        reconciliationUnavailable.state = blocked.decision.state
        reconciliationUnavailable.eventRecords = repairRecords + [blocked]
        reconciliationUnavailable.recoveryBaseline = repairBlockedState
        reconciliationUnavailable.auditFacts = [
            "authority=destination",
            "checkpoint=uncertain",
            "executorCommandCount=1",
            "ledgerCount=1",
            "pendingEffect=effect-001",
            "repair=unavailable",
            "snapshot=unchanged",
            "transitionCount=1",
        ]
        rebind(&reconciliationUnavailable)
        scenarios.append(reconciliationUnavailable)

        var terminatedRecovery = base("DEV138-RECOVERY-TERMINATED")
        let (terminatedState, terminatedRecords) = recoveryExecution()
        terminatedRecovery.state = terminatedState
        terminatedRecovery.state.phase = .terminated
        terminatedRecovery.eventRecords = terminatedRecords
        terminatedRecovery.auditFacts = ["recovery:terminated-with-pending-effect"]
        rebind(&terminatedRecovery)
        scenarios.append(terminatedRecovery)

        var replaySuppressed = base("DEV138-REPLAY-SUPPRESSED")
        let (replayState, replayBaseRecords) = recoveryExecution()
        let replay = event(replayState, .suppressReplay)
        replaySuppressed.state = replay.decision.state
        replaySuppressed.eventRecords = replayBaseRecords + [replay]
        replaySuppressed.recoveryBaseline = replayState
        replaySuppressed.auditFacts = ["pendingEffect=effect-001", "replay:suppressed"]
        rebind(&replaySuppressed)
        scenarios.append(replaySuppressed)

        var spoofedResult = base("DEV138-RESULT-SPOOFED")
        spoofedResult.toolResult?.callID = "forged-call"
        spoofedResult.toolResult = ToolResult(callID: "forged-call", binding: executorBinding, stateVersion: spoofedResult.state.stateVersion)
        let resultRefusal = event(
            spoofedResult.state,
            .acceptToolResult(
                result: spoofedResult.toolResult!,
                authorization: spoofedResult.toolAuthorization
            )
        )
        spoofedResult.state = resultRefusal.decision.state
        spoofedResult.eventRecords.append(resultRefusal)
        spoofedResult.auditFacts = ["tool_result:spoof-detected", "refusal:tool-result"]
        scenarios.append(spoofedResult)

        var routeDisallowed = base("DEV138-ROUTE-DISALLOWED")
        routeDisallowed.route.destinationProfile = "other-profile"
        clearCommands(&routeDisallowed)
        routeDisallowed.auditFacts = ["route:disallowed", "refusal:route"]
        scenarios.append(routeDisallowed)

        var schemaMissing = base("DEV138-SCHEMA-MISSING")
        schemaMissing.schemaVersion = 0
        schemaMissing.auditFacts = ["schema:missing"]
        scenarios.append(schemaMissing)

        var unauthorizedTool = base("DEV138-TOOL-UNAUTHORIZED")
        unauthorizedTool.toolAuthorization.actorProfile = "source"
        applyExecutionAttempt(request(from: unauthorizedTool), to: &unauthorizedTool)
        unauthorizedTool.auditFacts = ["tool:authorization-rejected", "refusal:tool"]
        scenarios.append(unauthorizedTool)

        var repairedTranscript = consultation("DEV138-TRANSCRIPT-REPAIRED")
        let repair = event(
            repairedTranscript.state,
            .repairTranscript(entries: [.call("call-001")])
        )
        repairedTranscript.state = repair.decision.state
        repairedTranscript.eventRecords.append(repair)
        repairedTranscript.auditFacts = ["transcript:repaired", "transcript:reused"]
        rebind(&repairedTranscript)
        scenarios.append(repairedTranscript)

        var unbalancedTranscript = consultation("DEV138-TRANSCRIPT-UNBALANCED")
        let refusedReuse = event(
            unbalancedTranscript.state,
            .reuseTranscript(entries: [.call("call-001")])
        )
        unbalancedTranscript.state = refusedReuse.decision.state
        unbalancedTranscript.eventRecords.append(refusedReuse)
        unbalancedTranscript.auditFacts = ["transcript:unbalanced", "refusal:transcript-reuse"]
        scenarios.append(unbalancedTranscript)

        var uncertainRecovery = base("DEV138-UNCERTAIN-RECOVERY")
        let (uncertainRecoveryState, uncertainRecoveryRecords) = recoveryExecution()
        uncertainRecovery.state = uncertainRecoveryState
        uncertainRecovery.eventRecords = uncertainRecoveryRecords
        uncertainRecovery.auditFacts = ["checkpoint=uncertain", "pendingEffect=effect-001", "recovery:persistent"]
        rebind(&uncertainRecovery)
        scenarios.append(uncertainRecovery)

        return scenarios.sorted { $0.caseID < $1.caseID }
    }

    static func mutation(named name: String) -> ScenarioObservation? {
        var observation = base("MUTATION-" + name.uppercased())

        switch name {
        case "tool_unauthorized":
            observation.toolAuthorization.actorProfile = "source"
        case "context_required_missing":
            observation.context.removeAll(where: { $0.name == "task_summary" })
            rebind(&observation)
        case "context_c3_leak":
            observation.context.append(
                ContextField(name: "never_transfer", outputLabel: "never_transfer", dataClass: .c3NeverTransfer, included: true, redacted: false, sourceMetadata: "source:secret")
            )
            rebind(&observation)
        case "phase_invalid":
            observation.state.phase = .transitioning
            observation.state.pendingTransition = nil
        case "effect_duplicate":
            observation.state.ledger.append(observation.state.ledger[0])
        case "effect_replay":
            let original = observation.state.commandHistory[0]
            observation.state.commandHistory.append(
                ExecutorCommand(
                    effectID: original.effectID,
                    callID: "call-001-replay",
                    binding: original.binding,
                    stateVersion: original.stateVersion,
                    kind: .initial
                )
            )
            observation.state.executorCommandCount = 2
        case "fallback_expands_trust":
            let fallbackAttempt = event(
                observation.state,
                .modelAvailability(
                    .degraded(
                        candidate: TrustBoundary(
                            providerRank: 3,
                            maximumDataClass: .c3NeverTransfer,
                            retentionRank: 2,
                            toolRank: 2,
                            effectBudget: 2
                        )
                    )
                )
            )
            observation.state = fallbackAttempt.decision.state
            observation.eventRecords.append(fallbackAttempt)
        case "evidence_leak":
            let rawEvidence = "raw-" + "evidence-payload"
            observation.evidence = [
                EvidenceRecord(
                    classification: .rawContent,
                    pathKind: .absolute,
                    artifactExtension: ".trace",
                    redaction: .raw,
                    content: rawEvidence,
                    fingerprint: "sha256:" + SHA256.hexDigest(rawEvidence)
                )
            ]
        case "evidence_bad_fingerprint":
            observation.evidence[0].fingerprint = "sha256:not-a-digest"
        case "evidence_mismatched_fingerprint":
            observation.evidence[0].fingerprint = "sha256:" + String(repeating: "0", count: 64)
        case "evidence_metadata_disguised_prohibited":
            let disguised = "synthetic-" + "credential-sentinel"
            observation.evidence[0].content = disguised
            observation.evidence[0].fingerprint = "sha256:" + SHA256.hexDigest(disguised)
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
            observation.grant.allowedDataClasses = []
        case "grant_extra_class":
            observation.grant.allowedDataClasses.insert(.c2Sensitive)
        case "grant_extra_c3_class":
            observation.grant.allowedDataClasses.insert(.c3NeverTransfer)
        case "grant_field_mismatch":
            observation.grant.allowedFields = []
        case "grant_extra_field":
            observation.grant.allowedFields.insert("extra_field")
        case "grant_tool_mismatch":
            observation.grant.allowedTools = [
                ToolBinding(name: "other.tool", version: "1.0", provider: "provider-b", resultType: "ExecutionReceipt")
            ]
        case "grant_retention_mismatch":
            observation.grant.retention = "persistent"
        case "grant_expired":
            observation.grant.expiresAt = 99
        case "grant_exceptional_c2_missing":
            observation.context.append(
                ContextField(name: "customer_record", outputLabel: "customer_record:redacted", dataClass: .c2Sensitive, included: true, redacted: true, sourceMetadata: "source:customer")
            )
            rebind(&observation)
            observation.grant.exceptionalC2Permission = "denied"
        case "grant_state_version_stale":
            observation.grant.stateVersion = 1
        case "grant_policy_version_stale":
            observation.grant.policyVersion = 6
        case "result_call_id_mismatch":
            observation.toolResult?.callID = "other-call"
        case "result_tool_version_mismatch":
            observation.toolResult?.binding.version = "2.0"
        case "result_provider_mismatch":
            observation.toolResult?.binding.provider = "other-provider"
        case "result_type_mismatch":
            observation.toolResult?.binding.resultType = "OtherResult"
        case "result_state_version_stale":
            observation.toolResult?.stateVersion = 1
        default:
            return nil
        }

        return observation
    }

    static func recoveryProbe(named name: String) -> RecoveryProbe? {
        let (before, _) = recoveryExecution()
        let event: TrustedEvent
        switch name {
        case "reconciliation-unavailable":
            event = .reconciliationUnavailable
        case "replay-suppressed":
            event = .suppressReplay
        default:
            return nil
        }
        let decision = HandoffReducer.reduce(before, event: event)
        return RecoveryProbe(
            before: RecoverySnapshot(before),
            after: RecoverySnapshot(decision.state),
            outcome: decision.outcome.rawValue == "repairBlockedUnavailable"
                ? "repair-blocked/unavailable"
                : "replay-suppressed",
            commandEmitted: decision.command != nil
        )
    }

    static func contextProbe() -> ContextProbe {
        let byID = Dictionary(uniqueKeysWithValues: all().map { ($0.caseID, $0) })
        return ContextProbe(
            blockedPayload: HandoffReducer.serializeContextForProvider(byID["DEV138-C3-BLOCKED"]!),
            rejectedLeakPayload: HandoffReducer.serializeContextForProvider(byID["DEV138-C3-LEAK"]!)
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
            try write(HandoffReducer.makeResult(observation), with: encoder)
        }
    }

    private static func write<T: Encodable>(_ value: T, with encoder: JSONEncoder) throws {
        FileHandle.standardOutput.write(try encoder.encode(value))
        FileHandle.standardOutput.write(Data([0x0A]))
    }
}
