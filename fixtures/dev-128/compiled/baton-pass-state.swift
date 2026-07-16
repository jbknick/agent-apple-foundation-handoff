// Pseudocode / deterministic composition mock: this is not a shipped Apple
// `BatonPass` API or an OS 27 dynamic-profile fixture.

enum Profile: String {
    case research
    case review
}

enum HandoffEvent {
    case transfer(source: Profile, destination: Profile)
}

struct BatonPassState {
    let source: Profile
    let destination: Profile
    var active: Profile
    var finalResponseOwner: Profile
    var transferred: Bool

    mutating func apply(_ event: HandoffEvent) {
        switch event {
        case let .transfer(source, destination):
            precondition(source == self.source)
            precondition(destination == self.destination)
            precondition(active == source)
            precondition(!transferred)
            active = destination
            finalResponseOwner = destination
            transferred = true
        }
    }
}

@main
struct BatonPassStateProbe {
    static func main() {
        var state = BatonPassState(
            source: .research,
            destination: .review,
            active: .research,
            finalResponseOwner: .research,
            transferred: false
        )

        precondition(state.active == state.source)
        state.apply(.transfer(source: .research, destination: .review))
        precondition(state.active == state.destination)
        precondition(state.finalResponseOwner == state.destination)
        precondition(state.transferred)

        print(
            "source=\(state.source.rawValue) destination=\(state.destination.rawValue) "
                + "active=\(state.active.rawValue) "
                + "finalOwner=\(state.finalResponseOwner.rawValue) "
                + "transferred=\(state.transferred)"
        )
    }
}
