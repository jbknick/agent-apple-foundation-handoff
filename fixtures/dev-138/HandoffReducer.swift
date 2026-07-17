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

struct ContextField: Equatable {
    var name: String
    var outputLabel: String
    var dataClass: DataClass
    var included: Bool
    var redacted: Bool
    var sourceMetadata: String
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
    var allowedTool: String
    var retention: String
    var expiresAt: Int
    var stateVersion: Int
    var policyVersion: Int
    var exceptionalC2Authorized: Bool
}

struct EffectRecord: Equatable {
    var effectID: String
    var stateVersion: Int
    var command: String
    var checkpoint: String
    var truth: String
    var reconciled: Bool
}

struct HandoffState: Equatable {
    var activeProfile: String
    var finalResponseOwner: String
    var phase: Phase
    var stateVersion: Int
    var policyVersion: Int
    var transitionCount: Int
    var transitionBudget: Int
    var executorCommandCount: Int
    var ledger: [EffectRecord]
    var pendingEffectID: String?
    var pendingTransition: String?
    var lastCheckpoint: String?
    var lastStableCheckpoint: String
    var auditEvents: [String]

    static var initial: HandoffState {
        HandoffState(
            activeProfile: "source",
            finalResponseOwner: "source",
            phase: .stable,
            stateVersion: 1,
            policyVersion: 7,
            transitionCount: 0,
            transitionBudget: 2,
            executorCommandCount: 0,
            ledger: [],
            pendingEffectID: nil,
            pendingTransition: nil,
            lastCheckpoint: nil,
            lastStableCheckpoint: "source-stable",
            auditEvents: []
        )
    }
}

enum TrustedEvent: Equatable {
    case commitBaton
    case completeConsultation
    case execute(effectID: String)
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
    var tool: String
    var retention: String
    var routeAllowed: Bool
    var transitionEdgeAllowed: Bool
    var loopDetected: Bool
    var handoffCommitted: Bool
    var commandRequested: Bool
    var commandAuthorized: Bool
    var commandOriginTrusted: Bool
    var untrustedResultAccepted: Bool
    var requiredContextNames: Set<String>
    var context: [ContextField]
    var grant: BoundaryGrant
    var now: Int
    var phaseRuleValid: Bool
    var duplicateLedgerDetected: Bool
    var replayCommandIssued: Bool
    var retryBeforeReconciliation: Bool
    var cancellationErasedRecovery: Bool
    var fallback: Fallback
    var fallbackExpandedTrust: Bool
    var transcriptBalanced: Bool
    var transcriptRepaired: Bool
    var rawEvidence: [String]
    var evidenceSanitized: Bool
    var rubricComplete: Bool
    var state: HandoffState
}

struct ExecutorCommand: Equatable {
    let effectID: String
    let tool: String
}

struct ReducerDecision: Equatable {
    let state: HandoffState
    let command: ExecutorCommand?
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
    static func reduce(_ state: HandoffState, event: TrustedEvent) -> ReducerDecision {
        var next = state
        var command: ExecutorCommand?

        switch event {
        case .commitBaton:
            guard state.phase == .stable else {
                return ReducerDecision(state: state, command: nil)
            }
            guard state.transitionCount < state.transitionBudget else {
                return ReducerDecision(state: state, command: nil)
            }
            next.activeProfile = "destination"
            next.finalResponseOwner = "destination"
            next.stateVersion += 1
            next.transitionCount += 1
            next.lastStableCheckpoint = "baton-committed"
            next.auditEvents.append("commit:destination")

        case .completeConsultation:
            next.activeProfile = "source"
            next.finalResponseOwner = "source"
            next.executorCommandCount += 1
            next.auditEvents.append(contentsOf: ["consultation:isolated", "owner:source"])
            command = ExecutorCommand(effectID: "consultation-001", tool: "executor.run")

        case let .execute(effectID):
            guard state.phase == .stable, !state.ledger.contains(where: { $0.effectID == effectID }) else {
                return ReducerDecision(state: state, command: nil)
            }
            next.executorCommandCount += 1
            next.ledger.append(
                EffectRecord(
                    effectID: effectID,
                    stateVersion: state.stateVersion,
                    command: "executor.run",
                    checkpoint: "committed",
                    truth: "commandIssued",
                    reconciled: false
                )
            )
            next.auditEvents.append("effect:\(effectID)")
            command = ExecutorCommand(effectID: effectID, tool: "executor.run")

        case let .commandUncertain(effectID):
            guard state.ledger.contains(where: { $0.effectID == effectID }) else {
                return ReducerDecision(state: state, command: nil)
            }
            next.phase = .recoveryRequired
            next.pendingEffectID = effectID
            next.pendingTransition = "effect-reconciliation"
            next.lastCheckpoint = "uncertain"
            next.auditEvents = [
                "checkpoint=uncertain",
                "pendingEffect=\(effectID)",
                "recovery:persistent",
            ]

        case .reconciliationUnavailable:
            guard state.phase == .recoveryRequired else {
                return ReducerDecision(state: state, command: nil)
            }
            next.auditEvents = [
                "authority=\(state.activeProfile)",
                "pendingEffect=\(state.pendingEffectID ?? "none")",
                "checkpoint=\(state.lastCheckpoint ?? "none")",
                "transitionCount=\(state.transitionCount)",
                "executorCommandCount=\(state.executorCommandCount)",
                "ledgerCount=\(state.ledger.count)",
                "repair=unavailable",
                "snapshot=unchanged",
            ]

        case .suppressReplay:
            guard state.phase == .recoveryRequired else {
                return ReducerDecision(state: state, command: nil)
            }
            next.auditEvents = [
                "pendingEffect=\(state.pendingEffectID ?? "none")",
                "replay:suppressed",
            ]

        case .reconcileSucceeded:
            guard state.phase == .recoveryRequired else {
                return ReducerDecision(state: state, command: nil)
            }
            next.phase = .stable
            next.pendingEffectID = nil
            next.pendingTransition = nil
            next.lastCheckpoint = "reconciled"
            next.ledger = next.ledger.map { record in
                guard record.effectID == state.pendingEffectID else { return record }
                var reconciled = record
                reconciled.truth = "reconciled"
                reconciled.reconciled = true
                return reconciled
            }
            next.auditEvents = ["reconciliation:succeeded"]

        case let .retryReconciled(effectID):
            guard state.phase == .stable, state.lastCheckpoint == "reconciled" else {
                return ReducerDecision(state: state, command: nil)
            }
            next.executorCommandCount += 1
            next.auditEvents.append("retry:\(effectID)")
            command = ExecutorCommand(effectID: effectID, tool: "executor.run")

        case .failPrecommit:
            next = .initial
            next.auditEvents = ["failure:precommit", "rollback:source"]

        case .cancelPrecommit:
            next = .initial
            next.auditEvents = ["cancellation:precommit", "rollback:source"]

        case .cancelUncertain:
            guard state.phase == .recoveryRequired else {
                return ReducerDecision(state: state, command: nil)
            }
            next.auditEvents = ["cancellation:recorded", "checkpoint=uncertain", "recovery:preserved"]

        case .repairTranscript:
            next.auditEvents = ["transcript:repaired", "transcript:reused"]

        case .ignoreUntrustedInput:
            next.auditEvents = ["untrusted_input:ignored"]
        }

        return ReducerDecision(state: next, command: command)
    }

    static func validate(_ observation: ScenarioObservation) -> [String] {
        var violations = Set<String>()

        if observation.schemaVersion != 1 {
            violations.insert("D-SCHEMA-001")
        }

        if !observation.routeAllowed {
            violations.insert("D-ROUTE-001")
        }

        let ownerIsValid: Bool
        if observation.handoffCommitted {
            switch observation.pattern {
            case .batonPass:
                ownerIsValid = observation.state.activeProfile == observation.destinationProfile
                    && observation.state.finalResponseOwner == observation.destinationProfile
            case .isolatedConsultation:
                ownerIsValid = observation.state.activeProfile == observation.sourceProfile
                    && observation.state.finalResponseOwner == observation.sourceProfile
            }
        } else {
            ownerIsValid = observation.state.activeProfile == observation.sourceProfile
                && observation.state.finalResponseOwner == observation.sourceProfile
        }
        if !ownerIsValid {
            violations.insert("D-OWNER-001")
        }

        if !observation.transitionEdgeAllowed
            || observation.loopDetected
            || observation.state.transitionCount > observation.state.transitionBudget
        {
            violations.insert("D-TRANSITION-001")
        }

        if observation.commandRequested
            && (!observation.commandAuthorized
                || !observation.commandOriginTrusted
                || observation.untrustedResultAccepted)
        {
            violations.insert("D-TOOL-001")
        }

        let included = observation.context.filter(\.included)
        let includedNames = Set(included.map(\.name))
        if !observation.requiredContextNames.isSubset(of: includedNames) {
            violations.insert("D-CONTEXT-001")
        }
        if included.contains(where: {
            $0.dataClass == .c3NeverTransfer || ($0.dataClass == .c2Sensitive && !$0.redacted)
        }) {
            violations.insert("D-CONTEXT-002")
        }

        let transferred = included.filter {
            $0.dataClass == .c1TaskPrivate || $0.dataClass == .c2Sensitive
        }
        if !transferred.isEmpty && !grantIsValid(observation.grant, for: observation, fields: transferred) {
            violations.insert("D-GRANT-001")
        }

        if !observation.phaseRuleValid
            || (!observation.transcriptBalanced && !observation.transcriptRepaired)
            || (observation.state.phase == .terminated && observation.state.pendingEffectID != nil)
            || observation.cancellationErasedRecovery
        {
            violations.insert("D-PHASE-001")
        }

        let identities = observation.state.ledger.map(\.effectID)
        if observation.duplicateLedgerDetected
            || Set(identities).count != identities.count
            || observation.cancellationErasedRecovery
        {
            violations.insert("D-EFFECT-001")
        }

        if observation.replayCommandIssued || observation.retryBeforeReconciliation {
            violations.insert("D-EFFECT-002")
        }

        if observation.fallbackExpandedTrust || observation.fallback == .unsafeExpandedTrust {
            violations.insert("D-FALLBACK-001")
        }

        if !observation.rawEvidence.isEmpty && !observation.evidenceSanitized {
            violations.insert("D-EVIDENCE-001")
        }

        if !observation.rubricComplete {
            violations.insert("D-RUBRIC-001")
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
            fallback: observation.fallback.rawValue,
            contextIncluded: observation.context.filter(\.included).map(\.outputLabel).sorted(),
            contextExcluded: observation.context.filter { !$0.included }.map(\.outputLabel).sorted(),
            auditEvents: observation.state.auditEvents.sorted()
        )
    }

    static func serializeContextForProvider(_ observation: ScenarioObservation) -> [String: String] {
        let included = observation.context.filter(\.included)
        let includedNames = Set(included.map(\.name))
        guard observation.requiredContextNames.isSubset(of: includedNames),
              !included.contains(where: {
                  $0.dataClass == .c3NeverTransfer
                      || ($0.dataClass == .c2Sensitive && !$0.redacted)
                      || $0.sourceMetadata.isEmpty
              })
        else {
            return [:]
        }

        let transferred = included.filter {
            $0.dataClass == .c1TaskPrivate || $0.dataClass == .c2Sensitive
        }
        guard transferred.isEmpty
                || grantIsValid(observation.grant, for: observation, fields: transferred)
        else {
            return [:]
        }

        return Dictionary(uniqueKeysWithValues: included.map { ($0.name, $0.value) })
    }

    private static func grantIsValid(
        _ grant: BoundaryGrant,
        for observation: ScenarioObservation,
        fields: [ContextField]
    ) -> Bool {
        guard grant.personID == observation.personID,
              grant.sessionID == observation.sessionID,
              grant.sourceProfile == observation.sourceProfile,
              grant.sourceProvider == observation.sourceProvider,
              grant.destinationProfile == observation.destinationProfile,
              grant.destinationProvider == observation.destinationProvider,
              grant.purpose == observation.purpose,
              grant.allowedTool == observation.tool,
              grant.retention == observation.retention,
              grant.expiresAt >= observation.now,
              grant.stateVersion == observation.state.stateVersion,
              grant.policyVersion == observation.state.policyVersion
        else {
            return false
        }

        for field in fields {
            guard grant.allowedDataClasses.contains(field.dataClass),
                  grant.allowedFields.contains(field.name),
                  !field.sourceMetadata.isEmpty
            else {
                return false
            }
            if field.dataClass == .c2Sensitive && !grant.exceptionalC2Authorized {
                return false
            }
        }
        return true
    }
}
