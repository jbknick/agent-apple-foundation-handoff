// Intentionally non-compiling on the recorded host: the active Command Line
// Tools installation lacks the FoundationModelsMacros implementation plugin.
import FoundationModels

@available(macOS 26.0, *)
@Generable
struct HandoffEnvelope {
    let summary: String

    @Guide(description: "The receiving profile name.")
    let destination: String
}
