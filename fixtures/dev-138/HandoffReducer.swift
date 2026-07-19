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
    var requestedAt: Int
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
            requestedAt: 100,
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

struct HandoffProposal: Equatable {
    var sourceProfile: String
    var sourceProvider: String
    var destinationProfile: String
    var destinationProvider: String

    static func fixture(from state: HandoffState) -> HandoffProposal {
        HandoffProposal(
            sourceProfile: state.activeProfile,
            sourceProvider: state.activeProvider,
            destinationProfile: "destination",
            destinationProvider: "provider-b"
        )
    }
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
    var pendingProposal: HandoffProposal?
    var lastCheckpoint: String?
    var lastStableCheckpoint: String
    var repairFacts: RepairFacts
    var authorizedBoundary: TrustBoundary
    var fallback: Fallback
    var transcript: [TranscriptEntry]
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
            pendingProposal: nil,
            lastCheckpoint: nil,
            lastStableCheckpoint: "source-stable",
            repairFacts: .none,
            authorizedBoundary: TrustBoundary(
                providerRank: 2,
                maximumDataClass: .c2Sensitive,
                retentionRank: 1,
                toolRank: 1,
                effectBudget: 1
            ),
            fallback: .none,
            transcript: [.text("synthetic-summary")],
            auditEvents: []
        )
    }
}

enum ModelAvailability: Equatable {
    case degraded(candidate: TrustBoundary)
    case unavailable
}

enum ReconciliationTruth: String, Equatable {
    case confirmedApplied
    case confirmedNotApplied
}

enum TrustedEvent: Equatable {
    case proposeBaton(proposal: HandoffProposal)
    case commitBaton
    case completeConsultation
    case execute(request: ExecutionRequest)
    case acceptToolResult(result: ToolResult, authorization: ToolAuthorization)
    case modelAvailability(ModelAvailability)
    case commandUncertain(effectID: String)
    case reconciliationUnavailable
    case suppressReplay
    case reconcileSucceeded(truth: ReconciliationTruth)
    case retryReconciled(effectID: String)
    case failPrecommit
    case cancelPrecommit
    case cancelUncertain
    case repairTranscript(entries: [TranscriptEntry])
    case reuseTranscript(entries: [TranscriptEntry])
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
    var content: String
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

enum SHA256 {
    private static let roundConstants: [UInt32] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
        0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
        0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
        0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    ]

    static func hexDigest(_ input: String) -> String {
        var message = Array(input.utf8)
        let bitLength = UInt64(message.count) * 8
        message.append(0x80)
        while message.count % 64 != 56 {
            message.append(0)
        }
        for shift in stride(from: 56, through: 0, by: -8) {
            message.append(UInt8((bitLength >> UInt64(shift)) & 0xff))
        }

        var hash: [UInt32] = [
            0x6a09e667,
            0xbb67ae85,
            0x3c6ef372,
            0xa54ff53a,
            0x510e527f,
            0x9b05688c,
            0x1f83d9ab,
            0x5be0cd19,
        ]

        for offset in stride(from: 0, to: message.count, by: 64) {
            var words = [UInt32](repeating: 0, count: 64)
            for index in 0..<16 {
                let start = offset + index * 4
                words[index] = UInt32(message[start]) << 24
                    | UInt32(message[start + 1]) << 16
                    | UInt32(message[start + 2]) << 8
                    | UInt32(message[start + 3])
            }
            for index in 16..<64 {
                let first = rotateRight(words[index - 15], by: 7)
                    ^ rotateRight(words[index - 15], by: 18)
                    ^ (words[index - 15] >> 3)
                let second = rotateRight(words[index - 2], by: 17)
                    ^ rotateRight(words[index - 2], by: 19)
                    ^ (words[index - 2] >> 10)
                words[index] = words[index - 16]
                    &+ first
                    &+ words[index - 7]
                    &+ second
            }

            var a = hash[0]
            var b = hash[1]
            var c = hash[2]
            var d = hash[3]
            var e = hash[4]
            var f = hash[5]
            var g = hash[6]
            var h = hash[7]

            for index in 0..<64 {
                let sigmaOne = rotateRight(e, by: 6)
                    ^ rotateRight(e, by: 11)
                    ^ rotateRight(e, by: 25)
                let choice = (e & f) ^ ((~e) & g)
                let temporaryOne = h
                    &+ sigmaOne
                    &+ choice
                    &+ roundConstants[index]
                    &+ words[index]
                let sigmaZero = rotateRight(a, by: 2)
                    ^ rotateRight(a, by: 13)
                    ^ rotateRight(a, by: 22)
                let majority = (a & b) ^ (a & c) ^ (b & c)
                let temporaryTwo = sigmaZero &+ majority

                h = g
                g = f
                f = e
                e = d &+ temporaryOne
                d = c
                c = b
                b = a
                a = temporaryOne &+ temporaryTwo
            }

            hash[0] &+= a
            hash[1] &+= b
            hash[2] &+= c
            hash[3] &+= d
            hash[4] &+= e
            hash[5] &+= f
            hash[6] &+= g
            hash[7] &+= h
        }

        return hash.map { String(format: "%08x", $0) }.joined()
    }

    private static func rotateRight(_ value: UInt32, by amount: UInt32) -> UInt32 {
        (value >> amount) | (value << (32 - amount))
    }
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
        case let .proposeBaton(proposal):
            guard proposal.sourceProfile == state.activeProfile,
                  proposal.sourceProvider == state.activeProvider
            else {
                return refused(state, disposition: .refusedPolicy, audit: "transition:refused-source")
            }
            guard proposal.destinationProfile != proposal.sourceProfile,
                  !state.visitedProfiles.contains(proposal.destinationProfile)
            else {
                return refused(state, disposition: .refusedPolicy, audit: "transition:refused-revisit")
            }
            guard state.transitionCount < state.transitionBudget else {
                return refused(state, disposition: .refusedBudget, audit: "transition:refused-budget")
            }
            guard let edge = transitionEdge(for: proposal),
                  state.allowedEdges.contains(edge)
            else {
                return refused(state, disposition: .refusedPolicy, audit: "transition:refused-edge")
            }
            next.phase = .transitioning
            next.pendingTransition = "baton-pass"
            next.pendingProposal = proposal
            next.auditEvents.append("proposal:baton-pass")
            return applied(next, audit: ["proposal:baton-pass"])

        case .commitBaton:
            guard state.pendingTransition == "baton-pass",
                  let proposal = state.pendingProposal,
                  proposal.sourceProfile == state.activeProfile,
                  proposal.sourceProvider == state.activeProvider,
                  let edge = transitionEdge(for: proposal),
                  state.allowedEdges.contains(edge),
                  !state.visitedProfiles.contains(proposal.destinationProfile)
            else {
                return refused(state, disposition: .refusedPolicy, audit: "commit:refused-no-proposal")
            }
            guard state.transitionCount < state.transitionBudget else {
                return refused(state, disposition: .refusedBudget, audit: "commit:refused-budget")
            }
            next.activeProfile = proposal.destinationProfile
            next.activeProvider = proposal.destinationProvider
            next.finalResponseOwner = proposal.destinationProfile
            next.phase = .stable
            next.stateVersion += 1
            next.transitionCount += 1
            next.transitionHistory.append(edge)
            next.visitedProfiles.append(proposal.destinationProfile)
            next.pendingTransition = nil
            next.pendingProposal = nil
            next.lastStableCheckpoint = "baton-committed"
            next.auditEvents.append("commit:destination")
            return applied(next, audit: ["commit:destination"])

        case .completeConsultation:
            let effectID = "consultation-001"
            let callID = "consultation-call-001"
            guard !state.ledger.contains(where: { $0.effectID == effectID }),
                  !state.commandHistory.contains(where: { $0.callID == callID })
            else {
                return refused(state, disposition: .refusedReplay, audit: "consultation:refused-replay")
            }
            guard state.executorCommandCount < state.toolBudget,
                  state.ledger.count < state.effectBudget
            else {
                return refused(state, disposition: .refusedBudget, audit: "consultation:refused-budget")
            }
            let command = ExecutorCommand(
                effectID: effectID,
                callID: callID,
                binding: executorBinding,
                stateVersion: state.stateVersion,
                kind: .consultation
            )
            next.executorCommandCount += 1
            next.commandHistory.append(command)
            next.ledger.append(
                EffectRecord(
                    effectID: effectID,
                    stateVersion: state.stateVersion,
                    command: executorBinding.name,
                    checkpoint: "committed",
                    truth: "commandIssued",
                    reconciled: false
                )
            )
            next.auditEvents.append(contentsOf: ["consultation:isolated", "owner:source"])
            return applied(next, command: command, audit: ["consultation:isolated", "owner:source"])

        case let .execute(request):
            guard executionRequestIsAuthorized(request, for: state) else {
                return refused(state, disposition: .refusedPolicy, audit: "execution:refused-policy")
            }
            guard !state.ledger.contains(where: { $0.effectID == request.effectID }),
                  !state.commandHistory.contains(where: {
                      $0.callID == request.authorization.callID
                  })
            else {
                return refused(state, disposition: .refusedReplay, audit: "effect:refused-replay")
            }
            guard state.executorCommandCount < state.toolBudget,
                  state.ledger.count < state.effectBudget
            else {
                return refused(state, disposition: .refusedBudget, audit: "effect:refused-budget")
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
                  authorization.policyVersion == state.policyVersion
            else {
                return refused(state, disposition: .refusedPolicy, audit: "tool-result:refused-provenance")
            }
            let matchingCalls = state.commandHistory.filter {
                $0.callID == authorization.callID
            }
            guard matchingCalls.count == 1,
                  let command = matchingCalls.first,
                  command.binding == authorization.binding,
                  command.stateVersion == authorization.stateVersion
            else {
                return refused(state, disposition: .refusedPolicy, audit: "tool-result:refused-provenance")
            }
            let matchingRecordIndices = state.ledger.indices.filter { recordIndex in
                let record = state.ledger[recordIndex]
                return record.effectID == command.effectID
                    && record.stateVersion == command.stateVersion
                    && record.command == command.binding.name
            }
            guard matchingRecordIndices.count == 1,
                  let recordIndex = matchingRecordIndices.first
            else {
                return refused(state, disposition: .refusedPolicy, audit: "tool-result:refused-provenance")
            }
            guard effectRecordIsUnresolved(state.ledger[recordIndex])
            else {
                return refused(state, disposition: .refusedReplay, audit: "tool-result:refused-replay")
            }
            next.ledger[recordIndex].truth = "resultAccepted"
            next.auditEvents.append("tool-result:accepted")
            return applied(next, audit: ["tool-result:accepted"])

        case let .modelAvailability(availability):
            switch availability {
            case let .degraded(candidate):
                guard !boundaryExpands(candidate, comparedTo: state.authorizedBoundary) else {
                    return refused(
                        state,
                        disposition: .refusedPolicy,
                        audit: "fallback:refused-expanded-trust"
                    )
                }
                next.fallback = .safeAlternative
                next.auditEvents.append("fallback:safe-alternative")
                return applied(next, audit: ["fallback:safe-alternative"])
            case .unavailable:
                next.fallback = .unavailable
                next.auditEvents.append("fallback:explicit-unavailable")
                return applied(next, audit: ["fallback:explicit-unavailable"])
            }

        case let .commandUncertain(effectID):
            let unresolvedRecords = state.ledger.filter {
                $0.effectID == effectID && effectRecordIsUnresolved($0)
            }
            guard unresolvedRecords.count == 1,
                  let unresolvedRecord = unresolvedRecords.first,
                  hasOneCommandAwaitingResult(for: unresolvedRecord, in: state)
            else {
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

        case let .reconcileSucceeded(truth):
            let unresolvedRecords = state.ledger.filter {
                $0.effectID == state.repairFacts.effectID
                    && effectRecordIsUnresolved($0)
            }
            guard state.pendingEffectID == state.repairFacts.effectID,
                  state.repairFacts.disposition == .awaitingReconciliation,
                  state.repairFacts.retryAuthority == .denied,
                  unresolvedRecords.count == 1,
                  let unresolvedRecord = unresolvedRecords.first,
                  hasOneCommandAwaitingResult(for: unresolvedRecord, in: state)
            else {
                return refused(state, disposition: .refusedPolicy, audit: "reconciliation:refused-binding")
            }
            next.phase = .stable
            next.pendingEffectID = nil
            next.pendingTransition = nil
            next.lastCheckpoint = "reconciled"
            next.repairFacts.disposition = .reconciled
            next.repairFacts.lastKnownTruth = truth.rawValue
            next.repairFacts.reconciliationAttempts += 1
            next.repairFacts.retryAuthority = truth == .confirmedNotApplied ? .authorized : .denied
            next.ledger = next.ledger.map { record in
                guard record.effectID == state.repairFacts.effectID else { return record }
                var reconciled = record
                reconciled.truth = truth.rawValue
                reconciled.reconciled = true
                return reconciled
            }
            let audit = "reconciliation:\(truth.rawValue)"
            next.auditEvents.append(audit)
            return applied(next, audit: [audit])

        case let .retryReconciled(effectID):
            guard state.repairFacts.effectID == effectID,
                  state.repairFacts.disposition == .reconciled,
                  state.repairFacts.lastKnownTruth == ReconciliationTruth.confirmedNotApplied.rawValue,
                  state.repairFacts.retryAuthority == .authorized,
                  state.executorCommandCount < state.toolBudget,
                  !state.commandHistory.contains(where: {
                      $0.effectID == effectID && $0.kind == .retry
                  })
            else {
                let replayed = state.commandHistory.contains(where: {
                    $0.effectID == effectID && $0.kind == .retry
                })
                return refused(
                    state,
                    disposition: replayed ? .refusedReplay : .refusedPolicy,
                    audit: replayed ? "retry:refused-replay" : "retry:refused-before-reconcile"
                )
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
            next.ledger = next.ledger.map { record in
                guard record.effectID == effectID else { return record }
                var retried = record
                retried.truth = "retryIssued"
                return retried
            }
            next.repairFacts.retryAuthority = .denied
            next.auditEvents.append("retry:\(effectID)")
            return applied(next, command: command, audit: ["retry:\(effectID)"])

        case .failPrecommit:
            next.phase = .stable
            next.pendingTransition = nil
            next.pendingProposal = nil
            next.auditEvents.append(contentsOf: ["failure:precommit", "rollback:source"])
            return applied(next, audit: ["failure:precommit", "rollback:source"])

        case .cancelPrecommit:
            next.phase = .stable
            next.pendingTransition = nil
            next.pendingProposal = nil
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

        case let .repairTranscript(entries):
            guard let repaired = repairedTranscript(from: entries) else {
                return refused(state, disposition: .refusedPolicy, audit: "transcript:refused-repair")
            }
            next.transcript = repaired
            next.auditEvents.append(contentsOf: ["transcript:repaired", "transcript:reused"])
            return applied(next, audit: ["transcript:repaired", "transcript:reused"])

        case let .reuseTranscript(entries):
            guard transcriptIsBalanced(entries) else {
                return refused(state, disposition: .refusedPolicy, audit: "transcript:refused-reuse")
            }
            next.transcript = entries
            next.auditEvents.append("transcript:reused")
            return applied(next, audit: ["transcript:reused"])

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
            || transitionAttemptWasRefused(observation)
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
        if includedNames.count != included.count
            || included.contains(where: { !contextFieldIsAllowed($0, for: observation) })
        {
            violations.insert("D-CONTEXT-002")
        }

        let transferred = included.filter {
            $0.dataClass == .c1TaskPrivate || $0.dataClass == .c2Sensitive
        }
        if !transferred.isEmpty && !grantIsValid(observation.grant, for: observation, fields: transferred) {
            violations.insert("D-GRANT-001")
        }

        if !phaseFactsAreValid(observation) || !transcriptFactsAreValid(observation) {
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

        if fallbackAttemptExpandedTrust(observation) {
            violations.insert("D-FALLBACK-001")
        }

        if observation.evidence.contains(where: { !evidenceRecordIsSafe($0) }) {
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
            fallback: observation.state.fallback.rawValue,
            contextIncluded: observation.context.filter(\.included).map(\.outputLabel).sorted(),
            contextExcluded: observation.context.filter { !$0.included }.map(\.outputLabel).sorted(),
            auditEvents: observation.auditFacts.sorted()
        )
    }

    static func serializeContextForProvider(_ observation: ScenarioObservation) -> [String: String] {
        let included = observation.context.filter(\.included)
        let includedNames = Set(included.map(\.name))
        let transferred = included.filter {
            $0.dataClass == .c1TaskPrivate || $0.dataClass == .c2Sensitive
        }
        guard includedNames.count == included.count,
              observation.requiredContextNames.isSubset(of: includedNames),
              !included.contains(where: { !contextFieldIsAllowed($0, for: observation) }),
              transferred.isEmpty || grantIsValid(observation.grant, for: observation, fields: transferred)
        else {
            return [:]
        }
        return Dictionary(uniqueKeysWithValues: included.map { ($0.name, $0.value) })
    }

    private static func requiredPhase(for event: TrustedEvent) -> Phase {
        switch event {
        case .proposeBaton, .completeConsultation, .execute, .acceptToolResult, .modelAvailability,
             .commandUncertain, .retryReconciled, .repairTranscript, .reuseTranscript,
             .ignoreUntrustedInput:
            return .stable
        case .commitBaton, .failPrecommit, .cancelPrecommit:
            return .transitioning
        case .reconciliationUnavailable, .suppressReplay, .reconcileSucceeded,
             .cancelUncertain:
            return .recoveryRequired
        }
    }

    private static func transitionEdge(for proposal: HandoffProposal) -> TransitionEdge? {
        switch (
            proposal.sourceProfile,
            proposal.sourceProvider,
            proposal.destinationProfile,
            proposal.destinationProvider
        ) {
        case ("source", "provider-a", "destination", "provider-b"):
            return .sourceToDestination
        case ("source", "provider-a", "child", "provider-b"):
            return .sourceToChild
        case ("child", "provider-b", "source", "provider-a"):
            return .childToSource
        default:
            return nil
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
              names.count == included.count,
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
              grant.expiresAt >= request.requestedAt,
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
              observation.state.executorCommandCount == observation.state.commandHistory.count,
              Set(observation.state.commandHistory.map(\.callID)).count
                  == observation.state.commandHistory.count
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
            if state.pendingTransition != nil
                || state.pendingProposal != nil
                || state.pendingEffectID != nil
            {
                return false
            }
        case .transitioning:
            if state.pendingTransition == nil
                || state.pendingProposal == nil
                || state.pendingEffectID != nil
            {
                return false
            }
        case .recoveryRequired:
            if state.pendingEffectID == nil
                || state.pendingTransition != "effect-reconciliation"
                || state.lastCheckpoint != "uncertain"
                || state.repairFacts.disposition != .awaitingReconciliation
            {
                return false
            }
        case .terminated:
            if state.pendingTransition != nil
                || state.pendingProposal != nil
                || state.pendingEffectID != nil
            {
                return false
            }
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
                  state.repairFacts.effectID == effectID,
                  state.repairFacts.disposition == .reconciled,
                  state.repairFacts.lastKnownTruth
                      == ReconciliationTruth.confirmedNotApplied.rawValue
            else {
                return true
            }
        }
        return false
    }

    private static func effectRecordIsUnresolved(_ record: EffectRecord) -> Bool {
        record.truth == "commandIssued" || record.truth == "retryIssued"
    }

    private static func hasOneCommandAwaitingResult(
        for record: EffectRecord,
        in state: HandoffState
    ) -> Bool {
        state.commandHistory.filter { command in
            command.effectID == record.effectID
                && command.stateVersion == record.stateVersion
                && command.binding.name == record.command
                && (record.truth == "retryIssued"
                    ? command.kind == .retry
                    : command.kind != .retry)
        }.count == 1
    }

    private static func transitionAttemptWasRefused(_ observation: ScenarioObservation) -> Bool {
        observation.eventRecords.contains { record in
            guard case .proposeBaton = record.event else { return false }
            return record.decision.disposition == .refusedBudget
                || record.decision.auditEvents.contains("transition:refused-edge")
                || record.decision.auditEvents.contains("transition:refused-revisit")
        }
    }

    private static func transcriptFactsAreValid(_ observation: ScenarioObservation) -> Bool {
        guard transcriptIsBalanced(observation.state.transcript) else { return false }
        return !observation.eventRecords.contains { record in
            guard case let .reuseTranscript(entries) = record.event else { return false }
            return !transcriptIsBalanced(entries)
        }
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

    private static func repairedTranscript(
        from entries: [TranscriptEntry]
    ) -> [TranscriptEntry]? {
        var pendingCalls: [String] = []
        var seenCalls = Set<String>()
        var repaired = entries
        for entry in entries {
            switch entry {
            case .text:
                continue
            case let .call(callID):
                guard seenCalls.insert(callID).inserted else { return nil }
                pendingCalls.append(callID)
            case let .result(callID):
                guard let index = pendingCalls.firstIndex(of: callID) else { return nil }
                pendingCalls.remove(at: index)
            }
        }
        guard !pendingCalls.isEmpty else { return nil }
        repaired.append(contentsOf: pendingCalls.map(TranscriptEntry.result))
        return transcriptIsBalanced(repaired) ? repaired : nil
    }

    private static func fallbackAttemptExpandedTrust(
        _ observation: ScenarioObservation
    ) -> Bool {
        observation.eventRecords.contains { record in
            guard case let .modelAvailability(.degraded(candidate)) = record.event else {
                return false
            }
            return boundaryExpands(candidate, comparedTo: record.before.authorizedBoundary)
        }
    }

    private static func boundaryExpands(
        _ candidate: TrustBoundary,
        comparedTo authorized: TrustBoundary
    ) -> Bool {
        candidate.providerRank > authorized.providerRank
            || candidate.maximumDataClass.rawValue > authorized.maximumDataClass.rawValue
            || candidate.retentionRank > authorized.retentionRank
            || candidate.toolRank > authorized.toolRank
            || candidate.effectBudget > authorized.effectBudget
    }

    static func evidenceRecordIsSafe(_ record: EvidenceRecord) -> Bool {
        let prohibitedContent = [
            "blocked-c3-sentinel",
            "synthetic-credential-sentinel",
            "/Users/",
            "/home/",
            "session.trace",
            ".xcresult",
            "raw-evidence-payload",
        ]
        let hexadecimal = CharacterSet(charactersIn: "0123456789abcdef")
        let digest = String(record.fingerprint.dropFirst("sha256:".count))
        let digestIsWellFormed = record.fingerprint.hasPrefix("sha256:")
            && digest.count == 64
            && digest.unicodeScalars.allSatisfy(hexadecimal.contains)

        return record.classification == .metadataOnly
            && record.pathKind == .normalizedRelative
            && record.artifactExtension != ".trace"
            && record.artifactExtension != ".xcresult"
            && record.redaction == .redacted
            && !prohibitedContent.contains(where: record.content.contains)
            && digestIsWellFormed
            && record.fingerprint == "sha256:" + SHA256.hexDigest(record.content)
    }
}
