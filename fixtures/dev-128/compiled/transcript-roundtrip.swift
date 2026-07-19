import Foundation
import FoundationModels

// Compiled SDK 26.5. This is an offline transcript serialization probe.
@main
struct TranscriptRoundTripProbe {
    static func main() throws {
        guard #available(macOS 26.0, *) else { return }

        let original = Transcript(entries: [
            .instructions(.init(
                segments: [.text(.init(content: "Act as the source profile."))],
                toolDefinitions: []
            )),
            .prompt(.init(
                segments: [.text(.init(content: "Prepare a handoff."))]
            )),
            .response(.init(
                assetIDs: [],
                segments: [.text(.init(content: "Summary for the destination."))]
            )),
        ])

        let encoded = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(Transcript.self, from: encoded)
        precondition(decoded == original)

        let destination = LanguageModelSession(transcript: decoded)
        precondition(destination.transcript == original)
        print("entries=\(destination.transcript.count) codableRoundTrip=true rehydrated=true")
    }
}
