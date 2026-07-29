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

    enum CodingKeys: String, CodingKey {
        case id, severity, code, message
        case file, line, column, failedTestID
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(severity, forKey: .severity)
        try container.encode(code, forKey: .code)
        try container.encode(message, forKey: .message)
        if let file {
            try container.encode(file, forKey: .file)
        } else {
            try container.encodeNil(forKey: .file)
        }
        if let line {
            try container.encode(line, forKey: .line)
        } else {
            try container.encodeNil(forKey: .line)
        }
        if let column {
            try container.encode(column, forKey: .column)
        } else {
            try container.encodeNil(forKey: .column)
        }
        if let failedTestID {
            try container.encode(failedTestID, forKey: .failedTestID)
        } else {
            try container.encodeNil(forKey: .failedTestID)
        }
    }
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

    enum CodingKeys: String, CodingKey {
        case status, reasonCode, appleAvailable, localeSupported
        case contextSize, occupiedTokens, appleAttempts, condensation
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(status, forKey: .status)
        if let reasonCode {
            try container.encode(reasonCode, forKey: .reasonCode)
        } else {
            try container.encodeNil(forKey: .reasonCode)
        }
        try container.encode(appleAvailable, forKey: .appleAvailable)
        try container.encode(localeSupported, forKey: .localeSupported)
        try container.encode(contextSize, forKey: .contextSize)
        try container.encode(occupiedTokens, forKey: .occupiedTokens)
        try container.encode(appleAttempts, forKey: .appleAttempts)
        if let condensation {
            try container.encode(condensation, forKey: .condensation)
        } else {
            try container.encodeNil(forKey: .condensation)
        }
    }
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
        Read only key=value lines before filler.
        Set commandOutcome to the exact outcome value.
        Set summary to the exact suite value, one ASCII space, then the
        exact outcome value.
        Copy the complete command-class, outcome, exit-status, and
        warning-count lines verbatim into summaryFacts in that order.
        Set warningCount to the warning-count integer.
        Set nextAction to the exact next-action value.
        Copy the complete command-finished and task-complete lines verbatim
        into completionFacts in that order.
        Copy only literal issue lines into diagnostics.
        Set omittedWarningCount to warningCount minus the number of emitted
        warning-severity diagnostics.
        Do not paraphrase, describe yourself, infer, or add content.
        """
    )
    let prompt = Prompt(
        """
        Respond with JSON answering the question.
        {"question":"What was the result of this synthetic unit test?"}
        Synthetic unit-test record:
        \(input.diagnosticText)
        """
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
