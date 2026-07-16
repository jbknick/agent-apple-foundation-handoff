import Foundation
import FoundationModels

// Compiled SDK 26.5. This file is type-checked but never executed by the
// default gate, so the response and streaming calls do not generate content.
@available(macOS 26.0, *)
struct EchoTool: Tool {
    let name = "echo"
    let description = "Echo structured arguments."

    func call(arguments: GeneratedContent) async throws -> String {
        arguments.jsonString
    }
}

@available(macOS 26.0, *)
func exerciseStableSurface() async throws {
    let model = SystemLanguageModel.default
    _ = model.availability
    _ = model.isAvailable
    _ = model.contextSize

    let tool = EchoTool()
    let options = GenerationOptions(
        sampling: .random(top: 8, seed: 42),
        temperature: 0.5,
        maximumResponseTokens: 64
    )
    let session = LanguageModelSession(
        model: model,
        tools: [tool],
        instructions: "Return concise JSON."
    )
    session.prewarm(promptPrefix: Prompt("prefix"))

    let response = try await session.respond(to: "hello", options: options)
    _ = response.content
    _ = response.rawContent
    _ = response.transcriptEntries

    let stream = session.streamResponse(to: "hello", options: options)
    for try await snapshot in stream {
        _ = snapshot.content
        _ = snapshot.rawContent
    }

    let copied = Transcript(entries: session.transcript)
    _ = LanguageModelSession(model: model, tools: [tool], transcript: copied)

    if #available(macOS 26.4, *) {
        let dynamic = DynamicGenerationSchema(
            name: "TokenCountSchema",
            properties: [
                .init(name: "value", schema: .init(type: String.self)),
            ]
        )
        let schema = try GenerationSchema(root: dynamic, dependencies: [])
        _ = try await model.tokenCount(for: Prompt("hello"))
        _ = try await model.tokenCount(for: Instructions("be concise"))
        _ = try await model.tokenCount(for: [tool])
        _ = try await model.tokenCount(for: schema)
        _ = try await model.tokenCount(for: session.transcript)
    }
}

@available(macOS 26.0, *)
func exerciseRuntimeSchema() throws {
    let handoff = DynamicGenerationSchema(
        name: "HandoffEnvelope",
        properties: [
            .init(name: "summary", schema: .init(type: String.self)),
            .init(name: "destination", schema: .init(type: String.self)),
        ]
    )
    _ = try GenerationSchema(root: handoff, dependencies: [])
}
