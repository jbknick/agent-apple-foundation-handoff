# Orchestration Pattern Selection

## Scope and authority

This reference solely owns the distinctions among baton-pass, isolated
consultation, deterministic routing, and transcript transfer: topology,
history visibility, trigger/control, final-response ownership, and selection.
It does not own framework declarations or authorization. Read
[Apple API availability](apple-api-availability.md) for exact API status and
[security, context, and recovery](security-context-and-recovery.md) before any
context, provider, tool, or effect boundary.

Apple's WWDC26 session 242 describes baton-pass and phone-a-friend as
composition patterns. No first-class framework type named `BatonPass` or
`PhoneFriendTool` is claimed here.

## Selection questions

Ask in order:

1. Must another role finish the same user-facing task, or only return bounded
   expertise to a parent?
2. Must the destination see selected shared history, an independent child
   transcript, or explicitly copied entries in a new session?
3. Does a profile/tool event transfer control, or does application policy pick
   one route before work begins?
4. Who owns the final response after success, failure, cancellation, and
   fallback?

Use this exact selection rule:

```text
destination finishes the user-facing task + selected shared history -> baton-pass
parent needs bounded expertise + isolated child transcript -> consultation
application chooses one route before work -> deterministic routing
new session is initialized from selected entries -> transcript transfer
```

## Four-pattern comparison

| Pattern | Topology | History | Trigger/control | Final-response owner |
| --- | --- | --- | --- | --- |
| Baton-pass | One session with changing active profiles | Selected target-necessary shared history | A tool or trusted application event changes the active profile | Destination becomes active and owns the final response |
| Isolated consultation | Parent plus a short-lived child session | Independent child transcript and minimized input envelope | Parent invokes a bounded consultation tool; child returns one typed result | Parent receives a typed result and retains final ownership |
| Deterministic routing | Application selects one route | Defined by the selected route; no transfer promise | Deterministic application policy chooses before delegated work | Selected route owns its result; routing is not inherently a handoff |
| Transcript transfer | Distinct destination session initialized from selected entries | Only explicitly copied entries | Application filters/serializes entries and constructs the destination | Destination session owns its result; mechanics do not grant transfer authority |

## Baton-pass

| Sequence | Contract |
| --- | --- |
| Propose | Current source proposes one allowed destination and a minimized context envelope |
| Authorize | Application reducer validates versions, edge, grants, tools, effects, and budgets |
| Checkpoint | Source authority, active profile, final owner, and repair input are retained |
| Transfer | One command changes the active profile after validation |
| Commit | Destination activation is confirmed and the destination becomes final owner |
| Recover | Known pre-commit failure rolls back; uncertain commit enters recovery |

Shared session history is not permission to disclose every entry. The target
view must be selected for purpose and classification. A history transform can
narrow a request-local view, but exact beta availability is owned by the Apple
reference.

## Isolated consultation

| Sequence | Contract |
| --- | --- |
| Request | Parent prepares a purpose-bound, minimized, typed envelope |
| Child | A short-lived child session receives independent instructions and transcript |
| Result | Child returns one typed result with provenance and limitations |
| Parent | Parent validates the result, retains final ownership, and decides whether to use it |
| Failure | Parent remains authoritative and may return a bounded fallback without adopting child state |

Only the typed result crosses back. The child does not inherit the parent
transcript, authorization, tools, effect permission, or final-response role.

## Deterministic routing

Routing chooses a route before work from trusted application facts such as
availability, an approved capability, policy, or user selection. It does not
itself transfer authority between already-active roles, promise shared history,
or create consultation. Record the selected route and owner explicitly.

## Transcript transfer

Transcript transfer constructs a distinct destination session from all or a
selected subset of serialized entries. Only explicitly copied entries are
visible. Rehydration proves mechanics, not authorization, provenance quality,
or semantic safety. Validate complete tool-call/output pairs, classification,
and destination purpose before copying.

## Anti-conflation boundaries

- Baton-pass is not deterministic routing: it changes the active owner within
  an ongoing collaboration.
- Consultation is not baton-pass: the child disappears and the parent returns
  the final response.
- Transcript transfer is not baton-pass: it creates a distinct session from
  selected entries.
- Foundation Models runtime Skills, coding-agent skills, Apple Handoff, App
  Intents, and coding-session handoff are separate systems.
- Illustrative WWDC sample names are examples, not reusable framework
  declarations.

## Context and cache implications

Prefer the smallest history compatible with the selected pattern and purpose.
Baton-pass may preserve more shared prefix state; consultation deliberately
isolates history; routing inherits the chosen route's policy; transcript
transfer changes the destination prefix according to the copied entries.

No cache hit or performance advantage is guaranteed. Changing model/provider,
instructions, tools, configuration, or history can change prefix reuse. Pin
those variables and measure them using the qualifications in
[Apple API availability](apple-api-availability.md).

## Failure ownership

| Pattern | Failure owner | Safe result |
| --- | --- | --- |
| Baton-pass | Source until confirmed activation; destination afterward | Roll back known pre-commit failure or enter recovery for uncertain commit |
| Isolated consultation | Parent throughout | Reject or bound the child result; parent returns or degrades |
| Deterministic routing | Selected route under application policy | Return route-specific failure or choose a separately authorized fallback |
| Transcript transfer | Source owns selection; destination owns its new-session result | Reject invalid/incomplete entries; never imply authority from serialization |

The state mechanics are in [architecture and state](architecture-and-state.md),
and the evidence matrix is in
[evaluation and observability](evaluation-and-observability.md).

## Related references

- [Architecture and state](architecture-and-state.md)
- [Apple API availability](apple-api-availability.md)
- [Security, context, and recovery](security-context-and-recovery.md)
- [Evaluation and observability](evaluation-and-observability.md)

## Source ledger

| Source | Retrieved | Use |
| --- | --- | --- |
| [WWDC26 session 242](https://developer.apple.com/videos/play/wwdc2026/242/) | 2026-07-17 | Baton-pass and phone-a-friend topology, history, and final-owner distinctions |
| [Composing dynamic sessions](https://developer.apple.com/documentation/foundationmodels/composing-dynamic-sessions-with-instructions-and-profiles) | 2026-07-17 | Official beta profile/history composition context; declarations stay in the Apple owner |
| [LanguageModelSession](https://developer.apple.com/documentation/foundationmodels/languagemodelsession) | 2026-07-17 | Session and transcript context |

## Limitations

Pattern selection does not authorize a provider, context field, tool, or
effect. It does not prove live model behavior, child quality, activation, cache
reuse, or external commit. Every implementation still needs the state,
security, Apple API, and evaluation contracts linked above.
