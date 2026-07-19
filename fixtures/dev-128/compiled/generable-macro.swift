import FoundationModels

// Compiled SDK 26.5 with Xcode 26.6. The default gate only type-checks this
// file; it never invokes the async function or generates model content.
@available(macOS 26.0, *)
@Generable
struct HandoffEnvelope {
    let summary: String

    @Guide(description: "The receiving profile name.")
    let destination: String
}

@available(macOS 26.0, *)
func exerciseStructuredResponse() async throws {
    let session = LanguageModelSession()
    let response = try await session.respond(
        to: "Prepare a handoff.",
        generating: HandoffEnvelope.self
    )
    _ = response.content.summary
    _ = response.content.destination
}
