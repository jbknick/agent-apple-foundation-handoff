import Foundation

enum Pattern: String, Codable, Equatable {
    case batonPass
    case isolatedConsultation
}

enum Phase: String, Codable, Equatable {
    case stable
    case transitioning
    case recoveryRequired
    case terminated
}

enum DataClass: Int, Codable, Hashable {
    case c0Public
    case c1TaskPrivate
    case c2Sensitive
    case c3NeverTransfer
}

enum Fallback: String, Codable, Equatable {
    case none
    case safeAlternative
    case unavailable
    case unsafeExpandedTrust
}

enum TransitionEdge: String, Codable, Hashable {
    case sourceToDestination
    case sourceToChild
    case childToSource
}

struct ToolBinding: Codable, Equatable, Hashable {
    var name: String
    var version: String
    var provider: String
    var resultType: String
}

struct ContextField: Equatable {
    var name: String
    var outputLabel: String
    var dataClass: DataClass
    var included: Bool
    var redacted: Bool
    var sourceMetadata: String
    var sourceProfile: String = "source"
    var sourceProvider: String = "provider-a"
    var subject: String = "person-001"
    var purpose: String = "task-execution"
    var destinationProfile: String = "destination"
    var destinationProvider: String = "provider-b"
    var retention: String = "ephemeral"
    var stateVersion: Int = 2
    var policyVersion: Int = 7
    var value: String = ""
}

struct BoundaryGrant: Equatable {
    var personID: String
    var sessionID: String
    var sourceProfile: String
    var sourceProvider: String
    var destinationProfile: String
    var destinationProvider: String
    var purpose: String
    var allowedDataClasses: Set<DataClass>
    var allowedFields: Set<String>
    var allowedTools: Set<ToolBinding>
    var callID: String
    var retention: String
    var expiresAt: Int
    var stateVersion: Int
    var policyVersion: Int
    var exceptionalC2Permission: String
}

struct ToolAuthorization: Equatable {
    var actorProfile: String
    var callID: String
    var binding: ToolBinding
    var stateVersion: Int
    var policyVersion: Int
}

struct ToolResult: Equatable {
    var callID: String
    var binding: ToolBinding
    var stateVersion: Int
}

struct ExecutionRequest: Equatable {
    var effectID: String
    var requiredContextNames: Set<String>
    var context: [ContextField]
    var grant: BoundaryGrant
    var authorization: ToolAuthorization

    static func fixture(state: HandoffState) -> ExecutionRequest {
        let binding = ToolBinding(
            name: "executor.run",
            version: "1.0",
            provider: "provider-b",
            resultType: "ExecutionReceipt"
        )
        let authorization = ToolAuthorization(
            actorProfile: state.activeProfile,
            callID: "call-001",
            binding: binding,
            stateVersion: state.stateVersion,
            policyVersion: state.policyVersion
        )
        let context = [
            ContextField(
                name: "task_summary",
                outputLabel: "task_summary",
                dataClass: .c1TaskPrivate,
                included: true,
                redacted: false,
                sourceMetadata: "source:task",
                stateVersion: state.stateVersion,
                policyVersion: state.policyVersion
            )
        ]
        let grant = BoundaryGrant(
            personID: "person-001",
            sessionID: "session-001",
            sourceProfile: "source",
            sourceProvider: "provider-a",
            destinationProfile: "destination",
            destinationProvider: "provider-b",
            purpose: "task-execution",
            allowedDataClasses: [.c1TaskPrivate],
            allowedFields: ["task_summary"],
            allowedTools: [binding],
            callID: authorization.callID,
            retention: "ephemeral",
            expiresAt: 200,
            stateVersion: state.stateVersion,
            policyVersion: state.policyVersion,
            exceptionalC2Permission: "not-required"
        )
        return ExecutionRequest(
            effectID: "effect-001",
            requiredContextNames: ["task_summary"],
            context: context,
            grant: grant,
            authorization: authorization
        )
    }
}

enum CommandKind: String, Codable, Equatable {
    case initial
    case consultation
    case retry
}

struct ExecutorCommand: Equatable {
    let effectID: String
    let callID: String
    let binding: ToolBinding
    let stateVersion: Int
    let kind: CommandKind
}

struct EffectRecord: Equatable {
    var effectID: String
    var stateVersion: Int
    var command: String
    var checkpoint: String
    var truth: String
    var reconciled: Bool
}

enum RepairDisposition: String, Codable, Equatable {
    case none
    case awaitingReconciliation
    case reconciled
}

enum RetryAuthority: String, Codable, Equatable {
    case denied
    case authorized
}

struct RepairFacts: Codable, Equatable {
    var effectID: String
    var lastKnownTruth: String
    var disposition: RepairDisposition
    var reconciliationAttempts: Int
    var retryAuthority: RetryAuthority

    static let none = RepairFacts(
        effectID: "none",
        lastKnownTruth: "none",
        disposition: .none,
        reconciliationAttempts: 0,
        retryAuthority: .denied
    )
}

struct HandoffState: Equatable {
    var activeProfile: String
    var activeProvider: String
    var finalResponseOwner: String
    var phase: Phase
    var stateVersion: Int
    var policyVersion: Int
    var allowedEdges: Set<TransitionEdge>
    var transitionHistory: [TransitionEdge]
    var visitedProfiles: [String]
    var transitionCount: Int
    var transitionBudget: Int
    var toolBudget: Int
    var effectBudget: Int
    var executorCommandCount: Int
    var commandHistory: [ExecutorCommand]
    var ledger: [EffectRecord]
    var pendingEffectID: String?
    var pendingTransition: String?
    var lastCheckpoint: String?
    var lastStableCheckpoint: String
    var repairFacts: RepairFacts
    var auditEvents: [String]

    static var initial: HandoffState {
        HandoffState(
            activeProfile: "source",
            activeProvider: "provider-a",
            finalResponseOwner: "source",
            phase: .stable,
            stateVersion: 1,
            policyVersion: 7,
            allowedEdges: [.sourceToDestination, .sourceToChild, .childToSource],
            transitionHistory: [],
            visitedProfiles: ["source"],
            transitionCount: 0,
            transitionBudget: 2,
            toolBudget: 2,
            effectBudget: 1,
            executorCommandCount: 0,
            commandHistory: [],
            ledger: [],
            pendingEffectID: nil,
            pendingTransition: nil,
            lastCheckpoint: nil,
            lastStableCheckpoint: "source-stable",
            repairFacts: .none,
            auditEvents: []
        )
    }
}

enum TrustedEvent: Equatable {
    case proposeBaton
    case commitBaton
    case completeConsultation
    case execute(request: ExecutionRequest)
    case acceptToolResult(result: ToolResult, authorization: ToolAuthorization)
    case commandUncertain(effectID: String)
    case reconciliationUnavailable
    case suppressReplay
    case reconcileSucceeded
    case retryReconciled(effectID: String)
    case failPrecommit
    case cancelPrecommit
    case cancelUncertain
    case repairTranscript
    case ignoreUntrustedInput
}

enum EventDisposition: String, Equatable {
    case applied
    case refusedPhase
    case refusedBudget
    case refusedPolicy
    case refusedReplay
}

enum ReducerOutcome: String, Equatable {
    case stateAdvanced
    case statePreserved
    case repairBlockedUnavailable
    case replaySuppressed
    case refused
}

struct ReducerDecision: Equatable {
    let state: HandoffState
    let command: ExecutorCommand?
    let disposition: EventDisposition
    let outcome: ReducerOutcome
    let auditEvents: [String]
}

struct EventRecord: Equatable {
    let event: TrustedEvent
    let before: HandoffState
    let decision: ReducerDecision
}

struct RouteContract: Equatable {
    var pattern: Pattern
    var destinationProfile: String
    var destinationProvider: String
    var allowedEdges: Set<TransitionEdge>
}

struct TrustBoundary: Equatable {
    var providerRank: Int
    var maximumDataClass: DataClass
    var retentionRank: Int
    var toolRank: Int
    var effectBudget: Int
}

enum FallbackSelection: Equatable {
    case primary
    case chosen(TrustBoundary)
    case unavailable
}

struct FallbackPlan: Equatable {
    var primary: TrustBoundary
    var selection: FallbackSelection
}

enum TranscriptEntry: Equatable {
    case text(String)
    case call(String)
    case result(String)
}

enum EvidenceClassification: Equatable {
    case metadataOnly
    case rawContent
}

enum EvidencePathKind: Equatable {
    case normalizedRelative
    case absolute
}

enum EvidenceRedaction: Equatable {
    case redacted
    case raw
}

struct EvidenceRecord: Equatable {
    var classification: EvidenceClassification
    var pathKind: EvidencePathKind
    var artifactExtension: String
    var redaction: EvidenceRedaction
    var fingerprint: String
}

struct ScenarioObservation {
    var schemaVersion: Int
    var caseID: String
    var pattern: Pattern
    var sourceProfile: String
    var sourceProvider: String
    var destinationProfile: String
    var destinationProvider: String
    var personID: String
    var sessionID: String
    var purpose: String
    var retention: String
    var route: RouteContract
    var requiredContextNames: Set<String>
    var context: [ContextField]
    var grant: BoundaryGrant
    var clock: Int
    var toolAuthorization: ToolAuthorization
    var toolResult: ToolResult?
    var fallbackPlan: FallbackPlan
    var transcript: [TranscriptEntry]
    var evidence: [EvidenceRecord]
    var state: HandoffState
    var eventRecords: [EventRecord]
    var recoveryBaseline: HandoffState?
    var auditFacts: [String]
}

struct CaseResult: Codable {
    let schemaVersion: Int
    let caseId: String
    let status: String
    let violations: [String]
    let pattern: String
    let activeProfile: String
    let finalResponseOwner: String
    let phase: String
    let stateVersion: Int
    let policyVersion: Int
    let transitionCount: Int
    let transitionBudget: Int
    let executorCommandCount: Int
    let effectCount: Int
    let fallback: String
    let contextIncluded: [String]
    let contextExcluded: [String]
    let auditEvents: [String]
}

enum HandoffReducer {
    private static let executorBinding = ToolBinding(
        name: "executor.run",
        version: "1.0",
        provider: "provider-b",
        resultType: "ExecutionReceipt"
    )

    static func reduce(_ state: HandoffState, event: TrustedEvent) -> ReducerDecision {
        guard state.phase == requiredPhase(for: event) else {
            return refused(state, disposition: .refusedPhase, audit: "event:refused-phase")
        }

        var next = state

        switch event {
        case .proposeBaton:
            guard state.transitionCount < state.transitionBudget else {
                return refused(state, disposition: .refusedBudget, audit: "transition:refused-budget")
            }
            guard state.allowedEdges.contains(.sourceToDestination) else {
                return refused(state, disposition: .refusedPolicy, audit: "transition:refused-edge")
            }
            next.phase = .transitioning
            next.pendingTransition = "baton-pass"
            next.auditEvents.append("proposal:baton-pass")
            return applied(next, audit: ["proposal:baton-pass"])

        case .commitBaton:
            guard state.pendingTransition == "baton-pass" else {
                return refused(state, disposition: .refusedPolicy, audit: "commit:refused-no-proposal")
            }
            guard state.transitionCount < state.transitionBudget else {
                return refused(state, disposition: .refusedBudget, audit: "commit:refused-budget")
            }
            next.activeProfile = "destination"
            next.activeProvider = "provider-b"
            next.finalResponseOwner = "destination"
            next.phase = .stable
            next.stateVersion += 1
            next.transitionCount += 1
            next.transitionHistory.append(.sourceToDestination)
            next.visitedProfiles.append("destination")
            next.pendingTransition = nil
            next.lastStableCheckpoint = "baton-committed"
            next.auditEvents.append("commit:destination")
            return applied(next, audit: ["commit:destination"])

        case .completeConsultation:
            guard state.executorCommandCount < state.toolBudget else {
                return refused(state, disposition: .refusedBudget, audit: "consultation:refused-budget")
            }
            let command = ExecutorCommand(
                effectID: "consultation-001",
                callID: "consultation-call-001",
                binding: executorBinding,
                stateVersion: state.stateVersion,
                kind: .consultation
            )
            next.executorCommandCount += 1
            next.commandHistory.append(command)
            next.auditEvents.append(contentsOf: ["consultation:isolated", "owner:source"])
            return applied(next, command: command, audit: ["consultation:isolated", "owner:source"])

        case let .execute(request):
            guard executionRequestIsAuthorized(request, for: state) else {
                return refused(state, disposition: .refusedPolicy, audit: "execution:refused-policy")
            }
            guard state.executorCommandCount < state.toolBudget,
                  state.ledger.count < state.effectBudget
            else {
                return refused(state, disposition: .refusedBudget, audit: "effect:refused-budget")
            }
            guard !state.ledger.contains(where: { $0.effectID == request.effectID }) else {
                return refused(state, disposition: .refusedReplay, audit: "effect:refused-replay")
            }
            let command = ExecutorCommand(
                effectID: request.effectID,
                callID: request.authorization.callID,
                binding: request.authorization.binding,
                stateVersion: state.stateVersion,
                kind: .initial
            )
            next.executorCommandCount += 1
            next.commandHistory.append(command)
            next.ledger.append(
                EffectRecord(
                    effectID: request.effectID,
                    stateVersion: state.stateVersion,
                    command: request.authorization.binding.name,
                    checkpoint: "committed",
                    truth: "commandIssued",
                    reconciled: false
                )
            )
            next.auditEvents.append("effect:\(request.effectID)")
            return applied(next, command: command, audit: ["effect:\(request.effectID)"])

        case let .acceptToolResult(result, authorization):
            guard result.callID == authorization.callID,
                  result.binding == authorization.binding,
                  result.stateVersion == state.stateVersion,
                  authorization.actorProfile == state.activeProfile,
                  authorization.stateVersion == state.stateVersion,
                  authorization.policyVersion == state.policyVersion,
                  state.commandHistory.contains(where: {
                      $0.callID == authorization.callID
                          && $0.binding == authorization.binding
                  })
            else {
                return refused(state, disposition: .refusedPolicy, audit: "tool-result:refused-provenance")
            }
            return ReducerDecision(
                state: state,
                command: nil,
                disposition: .applied,
                outcome: .statePreserved,
                auditEvents: ["tool-result:accepted"]
            )

        case let .commandUncertain(effectID):
            guard state.ledger.contains(where: { $0.effectID == effectID }) else {
                return refused(state, disposition: .refusedPolicy, audit: "recovery:refused-no-effect")
            }
            next.phase = .recoveryRequired
            next.pendingEffectID = effectID
            next.pendingTransition = "effect-reconciliation"
            next.lastCheckpoint = "uncertain"
            next.repairFacts = RepairFacts(
                effectID: effectID,
                lastKnownTruth: "possibleCommit",
                disposition: .awaitingReconciliation,
                reconciliationAttempts: 0,
                retryAuthority: .denied
            )
            next.auditEvents.append(contentsOf: [
                "checkpoint=uncertain",
                "pendingEffect=\(effectID)",
                "recovery:persistent",
            ])
            return applied(next, audit: ["recovery:persistent"])

        case .reconciliationUnavailable:
            return ReducerDecision(
                state: state,
                command: nil,
                disposition: .applied,
                outcome: .repairBlockedUnavailable,
                auditEvents: ["repair=unavailable", "snapshot=unchanged"]
            )

        case .suppressReplay:
            return ReducerDecision(
                state: state,
                command: nil,
                disposition: .applied,
                outcome: .replaySuppressed,
                auditEvents: ["replay:suppressed", "snapshot=unchanged"]
            )

        case .reconcileSucceeded:
            guard state.pendingEffectID == state.repairFacts.effectID else {
                return refused(state, disposition: .refusedPolicy, audit: "reconciliation:refused-binding")
            }
            next.phase = .stable
            next.pendingEffectID = nil
            next.pendingTransition = nil
            next.lastCheckpoint = "reconciled"
            next.repairFacts.disposition = .reconciled
            next.repairFacts.lastKnownTruth = "externallyConfirmed"
            next.repairFacts.reconciliationAttempts += 1
            next.repairFacts.retryAuthority = .authorized
            next.ledger = next.ledger.map { record in
                guard record.effectID == state.repairFacts.effectID else { return record }
                var reconciled = record
                reconciled.truth = "reconciled"
                reconciled.reconciled = true
                return reconciled
            }
            next.auditEvents.append("reconciliation:succeeded")
            return applied(next, audit: ["reconciliation:succeeded"])

        case let .retryReconciled(effectID):
            guard state.repairFacts.effectID == effectID,
                  state.repairFacts.disposition == .reconciled,
                  state.repairFacts.retryAuthority == .authorized,
                  state.executorCommandCount < state.toolBudget
            else {
                return refused(state, disposition: .refusedPolicy, audit: "retry:refused-before-reconcile")
            }
            let command = ExecutorCommand(
                effectID: effectID,
                callID: "call-001-retry",
                binding: executorBinding,
                stateVersion: state.stateVersion,
                kind: .retry
            )
            next.executorCommandCount += 1
            next.commandHistory.append(command)
            next.repairFacts.retryAuthority = .denied
            next.auditEvents.append("retry:\(effectID)")
            return applied(next, command: command, audit: ["retry:\(effectID)"])

        case .failPrecommit:
            next.phase = .stable
            next.pendingTransition = nil
            next.auditEvents.append(contentsOf: ["failure:precommit", "rollback:source"])
            return applied(next, audit: ["failure:precommit", "rollback:source"])

        case .cancelPrecommit:
            next.phase = .stable
            next.pendingTransition = nil
            next.auditEvents.append(contentsOf: ["cancellation:precommit", "rollback:source"])
            return applied(next, audit: ["cancellation:precommit", "rollback:source"])

        case .cancelUncertain:
            return ReducerDecision(
                state: state,
                command: nil,
                disposition: .applied,
                outcome: .statePreserved,
                auditEvents: ["cancellation:recorded", "recovery:preserved"]
            )

        case .repairTranscript:
            next.auditEvents.append(contentsOf: ["transcript:repaired", "transcript:reused"])
            return applied(next, audit: ["transcript:repaired", "transcript:reused"])

        case .ignoreUntrustedInput:
            return ReducerDecision(
                state: state,
                command: nil,
                disposition: .applied,
                outcome: .statePreserved,
                auditEvents: ["untrusted_input:ignored"]
            )
        }
    }

    static func validate(_ observation: ScenarioObservation) -> [String] {
        var violations = Set<String>()

        if observation.schemaVersion != 1 {
            violations.insert("D-SCHEMA-001")
        }

        if observation.route.pattern != observation.pattern
            || observation.route.destinationProfile != observation.destinationProfile
            || observation.route.destinationProvider != observation.destinationProvider
        {
            violations.insert("D-ROUTE-001")
        }

        let committedBaton = observation.state.transitionHistory.contains(.sourceToDestination)
        let ownerIsValid: Bool
        switch observation.pattern {
        case .batonPass where committedBaton:
            ownerIsValid = observation.state.activeProfile == observation.destinationProfile
                && observation.state.activeProvider == observation.destinationProvider
                && observation.state.finalResponseOwner == observation.destinationProfile
        default:
            ownerIsValid = observation.state.activeProfile == observation.sourceProfile
                && observation.state.activeProvider == observation.sourceProvider
                && observation.state.finalResponseOwner == observation.sourceProfile
        }
        if !ownerIsValid {
            violations.insert("D-OWNER-001")
        }

        let visited = observation.state.visitedProfiles
        if observation.state.transitionHistory.contains(where: {
            !observation.route.allowedEdges.contains($0)
        })
            || observation.state.transitionCount != observation.state.transitionHistory.count
            || observation.state.transitionCount > observation.state.transitionBudget
            || Set(visited).count != visited.count
        {
            violations.insert("D-TRANSITION-001")
        }

        if !toolFactsAreValid(observation) {
            violations.insert("D-TOOL-001")
        }

        let included = observation.context.filter(\.included)
        let includedNames = Set(included.map(\.name))
        if !observation.requiredContextNames.isSubset(of: includedNames) {
            violations.insert("D-CONTEXT-001")
        }
        if included.contains(where: { !contextFieldIsAllowed($0, for: observation) }) {
            violations.insert("D-CONTEXT-002")
        }

        let transferred = included.filter {
            $0.dataClass == .c1TaskPrivate || $0.dataClass == .c2Sensitive
        }
        if !transferred.isEmpty && !grantIsValid(observation.grant, for: observation, fields: transferred) {
            violations.insert("D-GRANT-001")
        }

        if !phaseFactsAreValid(observation) || !transcriptIsBalanced(observation.transcript) {
            violations.insert("D-PHASE-001")
        }

        let effectIdentities = observation.state.ledger.map(\.effectID)
        if Set(effectIdentities).count != effectIdentities.count
            || recoveryCancellationErasedLedger(observation)
        {
            violations.insert("D-EFFECT-001")
        }

        if commandHistoryViolatesReplayPolicy(observation.state) {
            violations.insert("D-EFFECT-002")
        }

        if fallbackExpandsBoundary(observation.fallbackPlan) {
            violations.insert("D-FALLBACK-001")
        }

        if observation.evidence.contains(where: evidenceRecordIsUnsafe) {
            violations.insert("D-EVIDENCE-001")
        }

        return violations.sorted()
    }

    static func makeResult(_ observation: ScenarioObservation) -> CaseResult {
        let violations = validate(observation)
        return CaseResult(
            schemaVersion: observation.schemaVersion,
            caseId: observation.caseID,
            status: violations.isEmpty ? "pass" : "fail",
            violations: violations,
            pattern: observation.pattern.rawValue,
            activeProfile: observation.state.activeProfile,
            finalResponseOwner: observation.state.finalResponseOwner,
            phase: observation.state.phase.rawValue,
            stateVersion: observation.state.stateVersion,
            policyVersion: observation.state.policyVersion,
            transitionCount: observation.state.transitionCount,
            transitionBudget: observation.state.transitionBudget,
            executorCommandCount: observation.state.executorCommandCount,
            effectCount: observation.state.ledger.count,
            fallback: normalizedFallback(observation.fallbackPlan).rawValue,
            contextIncluded: observation.context.filter(\.included).map(\.outputLabel).sorted(),
            contextExcluded: observation.context.filter { !$0.included }.map(\.outputLabel).sorted(),
            auditEvents: observation.auditFacts.sorted()
        )
    }

    static func serializeContextForProvider(_ observation: ScenarioObservation) -> [String: String] {
        let included = observation.context.filter(\.included)
        let transferred = included.filter {
            $0.dataClass == .c1TaskPrivate || $0.dataClass == .c2Sensitive
        }
        guard observation.requiredContextNames.isSubset(of: Set(included.map(\.name))),
              !included.contains(where: { !contextFieldIsAllowed($0, for: observation) }),
              transferred.isEmpty || grantIsValid(observation.grant, for: observation, fields: transferred)
        else {
            return [:]
        }
        return Dictionary(uniqueKeysWithValues: included.map { ($0.name, $0.value) })
    }

    private static func requiredPhase(for event: TrustedEvent) -> Phase {
        switch event {
        case .proposeBaton, .completeConsultation, .execute, .acceptToolResult, .commandUncertain,
             .retryReconciled, .repairTranscript, .ignoreUntrustedInput:
            return .stable
        case .commitBaton, .failPrecommit, .cancelPrecommit:
            return .transitioning
        case .reconciliationUnavailable, .suppressReplay, .reconcileSucceeded,
             .cancelUncertain:
            return .recoveryRequired
        }
    }

    private static func executionRequestIsAuthorized(
        _ request: ExecutionRequest,
        for state: HandoffState
    ) -> Bool {
        let included = request.context.filter(\.included)
        let names = Set(included.map(\.name))
        let classes = Set(included.map(\.dataClass))
        let fields = Set(included.map(\.name))
        let authorization = request.authorization
        let grant = request.grant

        guard request.requiredContextNames.isSubset(of: names),
              !included.contains(where: {
                  $0.dataClass == .c3NeverTransfer
                      || ($0.dataClass == .c2Sensitive && !$0.redacted)
                      || $0.sourceMetadata.isEmpty
                      || $0.sourceProfile != "source"
                      || $0.sourceProvider != "provider-a"
                      || $0.subject != "person-001"
                      || $0.purpose != "task-execution"
                      || $0.destinationProfile != "destination"
                      || $0.destinationProvider != "provider-b"
                      || $0.retention != "ephemeral"
                      || $0.stateVersion != state.stateVersion
                      || $0.policyVersion != state.policyVersion
              }),
              authorization.actorProfile == state.activeProfile,
              authorization.callID == "call-001",
              authorization.binding == executorBinding,
              authorization.stateVersion == state.stateVersion,
              authorization.policyVersion == state.policyVersion,
              grant.personID == "person-001",
              grant.sessionID == "session-001",
              grant.sourceProfile == "source",
              grant.sourceProvider == "provider-a",
              grant.destinationProfile == "destination",
              grant.destinationProvider == "provider-b",
              grant.purpose == "task-execution",
              grant.allowedDataClasses == classes,
              grant.allowedFields == fields,
              grant.allowedTools == [authorization.binding],
              grant.callID == authorization.callID,
              grant.retention == "ephemeral",
              grant.expiresAt >= 100,
              grant.stateVersion == state.stateVersion,
              grant.policyVersion == state.policyVersion,
              grant.exceptionalC2Permission == (classes.contains(.c2Sensitive) ? "approved" : "not-required")
        else {
            return false
        }
        return true
    }

    private static func refused(
        _ state: HandoffState,
        disposition: EventDisposition,
        audit: String
    ) -> ReducerDecision {
        ReducerDecision(
            state: state,
            command: nil,
            disposition: disposition,
            outcome: .refused,
            auditEvents: [audit]
        )
    }

    private static func applied(
        _ state: HandoffState,
        command: ExecutorCommand? = nil,
        audit: [String]
    ) -> ReducerDecision {
        ReducerDecision(
            state: state,
            command: command,
            disposition: .applied,
            outcome: .stateAdvanced,
            auditEvents: audit
        )
    }

    private static func contextFieldIsAllowed(
        _ field: ContextField,
        for observation: ScenarioObservation
    ) -> Bool {
        field.dataClass != .c3NeverTransfer
            && !(field.dataClass == .c2Sensitive && !field.redacted)
            && !field.sourceMetadata.isEmpty
            && field.sourceProfile == observation.sourceProfile
            && field.sourceProvider == observation.sourceProvider
            && field.subject == observation.personID
            && field.purpose == observation.purpose
            && field.destinationProfile == observation.destinationProfile
            && field.destinationProvider == observation.destinationProvider
            && field.retention == observation.retention
            && field.stateVersion == observation.state.stateVersion
            && field.policyVersion == observation.state.policyVersion
    }

    private static func grantIsValid(
        _ grant: BoundaryGrant,
        for observation: ScenarioObservation,
        fields: [ContextField]
    ) -> Bool {
        let exactClasses = Set(fields.map(\.dataClass))
        let exactFields = Set(fields.map(\.name))
        let exactTools: Set<ToolBinding> = [observation.toolAuthorization.binding]
        let requiresExceptionalC2 = exactClasses.contains(.c2Sensitive)

        return grant.personID == observation.personID
            && grant.sessionID == observation.sessionID
            && grant.sourceProfile == observation.sourceProfile
            && grant.sourceProvider == observation.sourceProvider
            && grant.destinationProfile == observation.destinationProfile
            && grant.destinationProvider == observation.destinationProvider
            && grant.purpose == observation.purpose
            && grant.allowedDataClasses == exactClasses
            && grant.allowedFields == exactFields
            && grant.allowedTools == exactTools
            && grant.callID == observation.toolAuthorization.callID
            && grant.retention == observation.retention
            && grant.expiresAt >= observation.clock
            && grant.stateVersion == observation.state.stateVersion
            && grant.policyVersion == observation.state.policyVersion
            && grant.exceptionalC2Permission == (requiresExceptionalC2 ? "approved" : "not-required")
    }

    private static func toolFactsAreValid(_ observation: ScenarioObservation) -> Bool {
        let authorization = observation.toolAuthorization
        guard authorization.actorProfile == observation.state.activeProfile,
              authorization.callID == "call-001",
              authorization.binding == executorBinding,
              authorization.stateVersion == observation.state.stateVersion,
              authorization.policyVersion == observation.state.policyVersion,
              observation.state.executorCommandCount <= observation.state.toolBudget,
              observation.state.executorCommandCount == observation.state.commandHistory.count
        else {
            return false
        }

        guard let result = observation.toolResult else { return true }
        return result.callID == authorization.callID
            && result.binding == authorization.binding
            && result.stateVersion == observation.state.stateVersion
    }

    private static func phaseFactsAreValid(_ observation: ScenarioObservation) -> Bool {
        let state = observation.state
        switch state.phase {
        case .stable:
            if state.pendingTransition != nil || state.pendingEffectID != nil { return false }
        case .transitioning:
            if state.pendingTransition == nil || state.pendingEffectID != nil { return false }
        case .recoveryRequired:
            if state.pendingEffectID == nil
                || state.pendingTransition != "effect-reconciliation"
                || state.lastCheckpoint != "uncertain"
                || state.repairFacts.disposition != .awaitingReconciliation
            {
                return false
            }
        case .terminated:
            if state.pendingTransition != nil || state.pendingEffectID != nil { return false }
        }

        for record in observation.eventRecords {
            if record.decision.disposition == .applied
                && record.before.phase != requiredPhase(for: record.event)
            {
                return false
            }
        }

        if let baseline = observation.recoveryBaseline,
           baseline.phase == .recoveryRequired,
           observation.eventRecords.last?.event == .cancelUncertain,
           observation.state != baseline
        {
            return false
        }
        return true
    }

    private static func recoveryCancellationErasedLedger(_ observation: ScenarioObservation) -> Bool {
        guard let baseline = observation.recoveryBaseline,
              baseline.phase == .recoveryRequired,
              observation.eventRecords.last?.event == .cancelUncertain
        else {
            return false
        }
        return observation.state.ledger != baseline.ledger
            || observation.state.repairFacts != baseline.repairFacts
    }

    private static func commandHistoryViolatesReplayPolicy(_ state: HandoffState) -> Bool {
        let grouped = Dictionary(grouping: state.commandHistory, by: \.effectID)
        for (effectID, commands) in grouped where commands.count > 1 {
            guard commands.count == 2,
                  commands.last?.kind == .retry,
                  state.ledger.first(where: { $0.effectID == effectID })?.reconciled == true
            else {
                return true
            }
        }
        return false
    }

    private static func transcriptIsBalanced(_ transcript: [TranscriptEntry]) -> Bool {
        var pendingCalls = Set<String>()
        for entry in transcript {
            switch entry {
            case .text:
                continue
            case let .call(callID):
                if !pendingCalls.insert(callID).inserted { return false }
            case let .result(callID):
                if pendingCalls.remove(callID) == nil { return false }
            }
        }
        return pendingCalls.isEmpty
    }

    private static func normalizedFallback(_ plan: FallbackPlan) -> Fallback {
        switch plan.selection {
        case .primary:
            return .none
        case .unavailable:
            return .unavailable
        case let .chosen(boundary):
            return fallbackExpandsBoundary(plan) || boundary == plan.primary
                ? (fallbackExpandsBoundary(plan) ? .unsafeExpandedTrust : .safeAlternative)
                : .safeAlternative
        }
    }

    private static func fallbackExpandsBoundary(_ plan: FallbackPlan) -> Bool {
        guard case let .chosen(candidate) = plan.selection else { return false }
        return candidate.providerRank > plan.primary.providerRank
            || candidate.maximumDataClass.rawValue > plan.primary.maximumDataClass.rawValue
            || candidate.retentionRank > plan.primary.retentionRank
            || candidate.toolRank > plan.primary.toolRank
            || candidate.effectBudget > plan.primary.effectBudget
    }

    private static func evidenceRecordIsUnsafe(_ record: EvidenceRecord) -> Bool {
        record.classification == .rawContent
            || record.pathKind == .absolute
            || record.artifactExtension == ".trace"
            || record.artifactExtension == ".xcresult"
            || record.redaction == .raw
    }
}
