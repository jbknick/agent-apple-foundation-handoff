enum DataClass: Int, Hashable {
    case c0Public
    case c1TaskPrivate
    case c2Sensitive
    case c3NeverTransfer
}

enum Provider: Hashable {
    case onDevice
    case pcc
    case custom(String)
}

struct ContextField: Equatable {
    let name: String
    let value: String
    let classification: DataClass
    let source: String
    let subject: String
    let purpose: String
    let retention: String
    let redacted: Bool
}

struct BoundaryGrant: Equatable {
    let destination: Provider
    let purpose: String
    let allowedClasses: Set<DataClass>
    let allowedFieldNames: Set<String>
    let policyVersion: Int
}

struct TransitionEdge: Hashable {
    let sourceProfile: String
    let destinationProfile: String
}

struct TransitionProposal: Equatable {
    let destinationProfile: String
    let destinationProvider: Provider
    let purpose: String
    let fields: [ContextField]
    let grant: BoundaryGrant?
    let sourceStateVersion: Int
    let policyVersion: Int
}

enum EffectCommitStatus: Equatable {
    case notCommitted
    case uncertain(effectID: String)
}

enum Phase: Equatable {
    case stable
    case transitioning
    case recoveryRequired
    case terminated(String)

    var isRecoveryRequired: Bool {
        self == .recoveryRequired
    }
}

struct HandoffState: Equatable {
    struct Checkpoint: Equatable {
        let activeProfile: String
        let provider: Provider
        let stateVersion: Int
    }

    var activeProfile: String
    var provider: Provider
    var stateVersion: Int
    var policyVersion: Int
    var transitionCount: Int
    let maxTransitions: Int
    var phase: Phase
    var pendingTransition: TransitionProposal?
    var checkpoint: Checkpoint?
    let allowedEdges: Set<TransitionEdge>
    var executorCommandCount: Int
    var effectLedger: [String]
    var audit: [String]
}

enum SecurityEvent: Equatable {
    case untrustedContext(source: String, text: String)
    case proposeTransition(TransitionProposal)
    case transitionCommitted
    case transitionToolFailed(EffectCommitStatus)
    case cancel(EffectCommitStatus)
}

struct ExecutorCommand: Equatable {
    let kind: String
    let destination: Provider
}

struct ReducerDecision: Equatable {
    var state: HandoffState
    let command: ExecutorCommand?
    let providerRequest: String?
}

enum DiagnosticFieldOrigin: Equatable {
    case trustedLocal
    case nonLocal
}

struct DiagnosticField: Equatable {
    let name: String
    let value: String
    let origin: DiagnosticFieldOrigin
}

struct DiagnosticToolResult: Equatable {
    let originalResult: String
    let resultType: String
    let fields: [DiagnosticField]
    let originalExecutionCount: Int
}

struct DiagnosticRouteContext: Equatable {
    let callID: String
    let toolName: String
    let toolVersion: String
    let stateVersion: Int
}

struct DiagnosticRouteBinding: Equatable {
    let callID: String
    let toolName: String
    let toolVersion: String
    let stateVersion: Int
    let action: String
    let originalResultType: String
}

enum DiagnosticBridgeDestination: Equatable {
    case appleOnDevice
}

struct DiagnosticBridgeRequest: Equatable {
    let trigger: String
    let destination: DiagnosticBridgeDestination
    let binding: DiagnosticRouteBinding
    let fields: [DiagnosticField]
}

struct DiagnosticBridgeResponse: Equatable {
    let schemaVersion: Int
    let binding: DiagnosticRouteBinding
    let resultType: String
    let condensedResult: String
}

enum DiagnosticBridgeOutcome: Equatable {
    case response(DiagnosticBridgeResponse)
    case declined
    case failed(reason: String)
    case timedOut
    case cancelled
}

struct DiagnosticRoutingDecision: Equatable {
    let request: DiagnosticBridgeRequest
    let visibleResult: String
    let acceptedCondensation: Bool
    let normalizedError: String?
    let originalExecutionCount: Int
    let rerunOriginalTool: Bool
    let audit: [String]
}

/// Pure policy model for the host's diagnostic-result boundary. It neither
/// invokes the original tool nor calls an Apple runtime.
struct DiagnosticResultRoutingPolicy {
    static let action = "condense_diagnostic_output"
    static let approvedFieldNames: Set<String> = [
        "severity", "code", "message", "file", "line", "column",
    ]
    static let responseSchemaVersion = 1
    static let responseResultType = "diagnostic_condensation"

    static func resolve(
        result: DiagnosticToolResult,
        context: DiagnosticRouteContext,
        outcome: DiagnosticBridgeOutcome
    ) -> DiagnosticRoutingDecision {
        let binding = DiagnosticRouteBinding(
            callID: context.callID,
            toolName: context.toolName,
            toolVersion: context.toolVersion,
            stateVersion: context.stateVersion,
            action: action,
            originalResultType: result.resultType
        )
        let request = DiagnosticBridgeRequest(
            trigger: "PostToolUse",
            destination: .appleOnDevice,
            binding: binding,
            fields: result.fields.filter {
                $0.origin == .trustedLocal && approvedFieldNames.contains($0.name)
            }
        )

        switch outcome {
        case let .response(response)
            where response.schemaVersion == responseSchemaVersion
                && response.binding == binding
                && response.resultType == responseResultType:
            return decision(
                request: request,
                result: result,
                visibleResult: response.condensedResult,
                accepted: true,
                normalizedError: nil,
                auditDecision: "accepted"
            )

        case .response:
            return fallback(
                request: request,
                result: result,
                normalizedError: "diagnostic_bridge_invalid_response"
            )

        case .declined:
            return fallback(request: request, result: result, normalizedError: nil)

        case .failed:
            return fallback(
                request: request,
                result: result,
                normalizedError: "diagnostic_bridge_failed"
            )

        case .timedOut:
            return fallback(
                request: request,
                result: result,
                normalizedError: "diagnostic_bridge_timeout"
            )

        case .cancelled:
            return fallback(
                request: request,
                result: result,
                normalizedError: "diagnostic_bridge_cancelled"
            )
        }
    }

    private static func fallback(
        request: DiagnosticBridgeRequest,
        result: DiagnosticToolResult,
        normalizedError: String?
    ) -> DiagnosticRoutingDecision {
        decision(
            request: request,
            result: result,
            visibleResult: result.originalResult,
            accepted: false,
            normalizedError: normalizedError,
            auditDecision: normalizedError == nil ? "declined" : "preservedOriginal"
        )
    }

    private static func decision(
        request: DiagnosticBridgeRequest,
        result: DiagnosticToolResult,
        visibleResult: String,
        accepted: Bool,
        normalizedError: String?,
        auditDecision: String
    ) -> DiagnosticRoutingDecision {
        let errorMetadata = normalizedError.map { " error=\($0)" } ?? ""
        let audit = [
            "event=PostToolUse action=\(action) destination=appleOnDevice "
                + "decision=\(auditDecision) callID=\(request.binding.callID) "
                + "fieldCount=\(request.fields.count)\(errorMetadata)"
        ]
        return DiagnosticRoutingDecision(
            request: request,
            visibleResult: visibleResult,
            acceptedCondensation: accepted,
            normalizedError: normalizedError,
            originalExecutionCount: result.originalExecutionCount,
            rerunOriginalTool: false,
            audit: audit
        )
    }
}

struct HandoffSecurityPolicy {
    static func reduce(state: HandoffState, event: SecurityEvent) -> ReducerDecision {
        switch event {
        case .untrustedContext:
            var next = state
            next.audit.append("event=untrustedContext decision=ignored")
            return ReducerDecision(state: next, command: nil, providerRequest: nil)

        case let .proposeTransition(proposal):
            return proposeTransition(state: state, proposal: proposal)

        case .transitionCommitted:
            return commitTransition(state: state)

        case let .transitionToolFailed(status):
            return resolveInterruption(state: state, status: status, eventName: "transitionToolFailed")

        case let .cancel(status):
            return resolveInterruption(state: state, status: status, eventName: "cancel")
        }
    }

    private static func proposeTransition(
        state: HandoffState,
        proposal: TransitionProposal
    ) -> ReducerDecision {
        var next = state

        guard state.phase == .stable else {
            next.audit.append("event=proposeTransition decision=ignored reason=phase")
            return ReducerDecision(state: next, command: nil, providerRequest: nil)
        }

        guard state.transitionCount < state.maxTransitions else {
            next.phase = .terminated("transitionBudgetExceeded")
            next.pendingTransition = nil
            next.checkpoint = nil
            next.audit.append(
                "event=proposeTransition decision=terminated reason=transitionBudgetExceeded"
            )
            return ReducerDecision(state: next, command: nil, providerRequest: nil)
        }

        guard let grant = proposal.grant,
              state.allowedEdges.contains(
                  TransitionEdge(
                      sourceProfile: state.activeProfile,
                      destinationProfile: proposal.destinationProfile
                  )
              ),
              proposal.sourceStateVersion == state.stateVersion,
              proposal.policyVersion == state.policyVersion,
              grant.destination == proposal.destinationProvider,
              grant.purpose == proposal.purpose,
              grant.policyVersion == state.policyVersion,
              proposal.fields.allSatisfy({ field in
                  field.classification != .c3NeverTransfer
                      && field.purpose == proposal.purpose
                      && grant.allowedClasses.contains(field.classification)
                      && grant.allowedFieldNames.contains(field.name)
              })
        else {
            let classes = proposal.fields
                .map { "C\($0.classification.rawValue)" }
                .joined(separator: ",")
            next.audit.append(
                "event=proposeTransition decision=blocked classes=\(classes)"
            )
            return ReducerDecision(state: next, command: nil, providerRequest: nil)
        }

        next.checkpoint = HandoffState.Checkpoint(
            activeProfile: state.activeProfile,
            provider: state.provider,
            stateVersion: state.stateVersion
        )
        next.pendingTransition = proposal
        next.phase = .transitioning
        next.transitionCount += 1
        next.executorCommandCount += 1
        let classes = proposal.fields
            .map { "C\($0.classification.rawValue)" }
            .joined(separator: ",")
        next.audit.append("event=proposeTransition decision=allowed classes=\(classes)")

        let request = proposal.fields
            .map(\.value)
            .joined(separator: "\n")
        let command = ExecutorCommand(kind: "transition", destination: proposal.destinationProvider)
        return ReducerDecision(state: next, command: command, providerRequest: request)
    }

    private static func commitTransition(state: HandoffState) -> ReducerDecision {
        var next = state
        guard state.phase == .transitioning,
              let proposal = state.pendingTransition
        else {
            next.audit.append("event=transitionCommitted decision=ignored")
            return ReducerDecision(state: next, command: nil, providerRequest: nil)
        }

        next.activeProfile = proposal.destinationProfile
        next.provider = proposal.destinationProvider
        next.stateVersion += 1
        next.phase = .stable
        next.pendingTransition = nil
        next.checkpoint = nil
        next.audit.append("event=transitionCommitted decision=accepted")
        return ReducerDecision(state: next, command: nil, providerRequest: nil)
    }

    private static func resolveInterruption(
        state: HandoffState,
        status: EffectCommitStatus,
        eventName: String
    ) -> ReducerDecision {
        var next = state

        guard state.phase == .transitioning else {
            next.audit.append("event=\(eventName) decision=ignored reason=phase")
            return ReducerDecision(state: next, command: nil, providerRequest: nil)
        }

        switch status {
        case .notCommitted:
            if let checkpoint = state.checkpoint {
                next.activeProfile = checkpoint.activeProfile
                next.provider = checkpoint.provider
                next.stateVersion = checkpoint.stateVersion
            }
            next.phase = .stable
            next.pendingTransition = nil
            next.checkpoint = nil
            next.audit.append("event=\(eventName) decision=restored status=notCommitted")

        case let .uncertain(effectID):
            if !next.effectLedger.contains(effectID) {
                next.effectLedger.append(effectID)
            }
            next.phase = .recoveryRequired
            next.audit.append(
                "event=\(eventName) decision=recoveryRequired effectID=\(effectID)"
            )
        }

        return ReducerDecision(state: next, command: nil, providerRequest: nil)
    }
}
