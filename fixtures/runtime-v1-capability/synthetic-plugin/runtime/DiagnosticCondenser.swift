import Foundation
import FoundationModels

@available(macOS 26.4, *)
@Generable
struct GeneratedDiagnostic: Codable {
    @Guide(description: "Stable diagnostic identifier.")
    let id: String
    @Guide(description: "Exactly fatal, error, warning, or info.")
    let severity: String
    let code: String
    let message: String
    let file: String?
    let line: Int?
    let column: Int?
    let failedTestID: String?
}

@available(macOS 26.4, *)
@Generable
struct DiagnosticCondensation: Codable {
    @Guide(description: "Exactly success, failure, or interrupted.")
    let commandOutcome: String
    let summary: String
    let summaryFacts: [String]
    let diagnostics: [GeneratedDiagnostic]
    let warningCount: Int
    let omittedWarningCount: Int
    let nextAction: String
    let completionFacts: [String]
}

@available(macOS 26.4, *)
struct BridgeInput: Decodable {
    let diagnosticText: String
}

@available(macOS 26.4, *)
struct BridgeOutput: Encodable {
    let status: String
    let reasonCode: String?
    let appleAvailable: Bool
    let localeSupported: Bool
    let contextSize: Int
    let occupiedTokens: Int
    let appleAttempts: Int
    let condensation: DiagnosticCondensation?
}

@available(macOS 26.4, *)
func classifyGenerationError(
    _ error: LanguageModelSession.GenerationError
) -> (status: String, reasonCode: String) {
    switch error {
    case .assetsUnavailable:
        return ("declined", "generation_assets_unavailable")
    case .unsupportedLanguageOrLocale:
        return ("declined", "generation_unsupported_language_or_locale")
    case .rateLimited:
        return ("declined", "generation_rate_limited")
    case .concurrentRequests:
        return ("declined", "generation_concurrent_requests")
    case .exceededContextWindowSize:
        return ("fail", "generation_exceeded_context_window_size")
    case .guardrailViolation:
        return ("fail", "generation_guardrail_violation")
    case .unsupportedGuide:
        return ("fail", "generation_unsupported_guide")
    case .decodingFailure:
        return ("fail", "generation_decoding_failure")
    case .refusal:
        return ("fail", "generation_refusal")
    @unknown default:
        return ("fail", "generation_unknown_error")
    }
}

@available(macOS 26.4, *)
func consult(_ input: BridgeInput) async -> BridgeOutput {
    let model = SystemLanguageModel.default
    let contextSize = model.contextSize

    guard case .available = model.availability else {
        return BridgeOutput(
            status: "declined",
            reasonCode: "apple_unavailable",
            appleAvailable: false,
            localeSupported: false,
            contextSize: contextSize,
            occupiedTokens: 0,
            appleAttempts: 0,
            condensation: nil
        )
    }
    guard model.supportsLocale() else {
        return BridgeOutput(
            status: "declined",
            reasonCode: "locale_unsupported",
            appleAvailable: true,
            localeSupported: false,
            contextSize: contextSize,
            occupiedTokens: 0,
            appleAttempts: 0,
            condensation: nil
        )
    }

    let instructions = Instructions(
        """
        Condense only literal facts in the supplied synthetic diagnostic.
        Use the suite and outcome values for the summary. Preserve the ordered
        command-class, outcome, exit-status, and warning-count facts. Use the
        source next-action value unchanged. Preserve command-finished and
        task-complete as ordered completion facts. Emit diagnostics only for
        literal fatal, error, warning, or info records. Do not add paths,
        secrets, diagnoses, or advice.
        """
    )
    let prompt = Prompt(
        "Synthetic diagnostic to condense:\n\(input.diagnosticText)"
    )
    let responseReserve = 1024

    let occupiedTokens: Int
    do {
        let instructionTokens =
            try await model.tokenCount(for: instructions)
        let promptTokens = try await model.tokenCount(for: prompt)
        let schemaTokens = try await model.tokenCount(
            for: DiagnosticCondensation.generationSchema
        )
        occupiedTokens =
            instructionTokens + promptTokens + schemaTokens + responseReserve
    } catch {
        return BridgeOutput(
            status: "declined",
            reasonCode: "generation_preflight_unavailable",
            appleAvailable: true,
            localeSupported: true,
            contextSize: contextSize,
            occupiedTokens: 0,
            appleAttempts: 0,
            condensation: nil
        )
    }
    guard occupiedTokens * 4 <= contextSize * 3 else {
        return BridgeOutput(
            status: "declined",
            reasonCode: "context_budget_exceeded",
            appleAvailable: true,
            localeSupported: true,
            contextSize: contextSize,
            occupiedTokens: occupiedTokens,
            appleAttempts: 0,
            condensation: nil
        )
    }

    let session = LanguageModelSession(
        model: model,
        tools: [],
        instructions: instructions
    )
    let appleAttempts = 1
    do {
        let response = try await session.respond(
            to: prompt,
            generating: DiagnosticCondensation.self,
            options: GenerationOptions(
                sampling: .greedy,
                maximumResponseTokens: 1024
            )
        )
        return BridgeOutput(
            status: "applied",
            reasonCode: nil,
            appleAvailable: true,
            localeSupported: true,
            contextSize: contextSize,
            occupiedTokens: occupiedTokens,
            appleAttempts: appleAttempts,
            condensation: response.content
        )
    } catch let generationError
        as LanguageModelSession.GenerationError {
        let classification = classifyGenerationError(generationError)
        return BridgeOutput(
            status: classification.status,
            reasonCode: classification.reasonCode,
            appleAvailable: true,
            localeSupported: true,
            contextSize: contextSize,
            occupiedTokens: 0,
            appleAttempts: appleAttempts,
            condensation: nil
        )
    } catch {
        return BridgeOutput(
            status: "fail",
            reasonCode: "generation_unknown_error",
            appleAvailable: true,
            localeSupported: true,
            contextSize: contextSize,
            occupiedTokens: 0,
            appleAttempts: appleAttempts,
            condensation: nil
        )
    }
}

@main
struct DiagnosticCondenserMain {
    static func main() async {
        guard #available(macOS 26.4, *) else {
            return
        }
        do {
            let inputData = FileHandle.standardInput.readDataToEndOfFile()
            let input = try JSONDecoder().decode(
                BridgeInput.self,
                from: inputData
            )
            let output = await consult(input)
            var encoded = try JSONEncoder().encode(output)
            encoded.append(0x0A)
            FileHandle.standardOutput.write(encoded)
        } catch {
            let output = BridgeOutput(
                status: "fail",
                reasonCode: "contract_invariant_failed",
                appleAvailable: false,
                localeSupported: false,
                contextSize: 1,
                occupiedTokens: 0,
                appleAttempts: 0,
                condensation: nil
            )
            if var encoded = try? JSONEncoder().encode(output) {
                encoded.append(0x0A)
                FileHandle.standardOutput.write(encoded)
            }
        }
    }
}
