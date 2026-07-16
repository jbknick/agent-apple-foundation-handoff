import FoundationModels

// Compiled SDK 26.5. This offline probe constructs independent session state.
@main
struct SessionIsolationProbe {
    static func main() {
        guard #available(macOS 26.0, *) else { return }

        let parentTranscript = Transcript(entries: [
            .prompt(.init(segments: [.text(.init(content: "parent-only"))])),
        ])
        let childTranscript = Transcript(entries: [
            .prompt(.init(segments: [.text(.init(content: "child-only"))])),
        ])
        let parent = LanguageModelSession(transcript: parentTranscript)
        let child = LanguageModelSession(transcript: childTranscript)

        precondition(parent.transcript != child.transcript)
        precondition(parent.transcript == parentTranscript)
        precondition(child.transcript == childTranscript)
        print(
            "parentEntries=\(parent.transcript.count) "
                + "childEntries=\(child.transcript.count) isolated=true"
        )
    }
}
