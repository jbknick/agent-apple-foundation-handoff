import Foundation
import FoundationModels

// Compiled SDK 26.5. This host-state probe never invokes model generation.
@main
struct AvailabilityProbe {
    static func main() {
        guard #available(macOS 26.0, *) else {
            print("availability=unsupportedOS")
            print("isAvailable=false")
            print("contextSize=0")
            print("supportsCurrentLocale=false")
            return
        }

        let model = SystemLanguageModel.default
        print("availability=\(model.availability)")
        print("isAvailable=\(model.isAvailable)")
        print("contextSize=\(model.contextSize)")
        print("supportsCurrentLocale=\(model.supportsLocale())")
    }
}
