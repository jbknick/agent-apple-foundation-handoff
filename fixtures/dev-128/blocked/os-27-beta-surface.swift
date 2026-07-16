// Intentionally non-compiling on the recorded host: SDK 26.5 lacks the OS 27
// DynamicProfile, Profile, profile-session, and toolCallingMode declarations.
import FoundationModels

@available(macOS 27.0, *)
struct HandoffProfile: LanguageModelSession.DynamicProfile {
    var body: some LanguageModelSession.DynamicProfile {
        LanguageModelSession.Profile {
            Instructions("Receive the baton and answer.")
        }
    }
}

@available(macOS 27.0, *)
func exerciseOS27BetaSurface() {
    _ = LanguageModelSession(profile: HandoffProfile(), history: [])
    _ = GenerationOptions(toolCallingMode: .required)
}
