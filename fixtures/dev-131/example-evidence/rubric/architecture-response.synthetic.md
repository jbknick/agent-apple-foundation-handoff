# Synthetic handoff architecture response

## pattern selection

Use a deterministic relay for the bounded, reviewable handoff and keep the
application as the authority for routing, ownership, effects, and recovery.

## Apple API grounding and version labeling

Use `LanguageModelSession` for generation and `Transcript` for session records
on supported Foundation Models hosts. Label the installed SDK 26 interfaces as
stable and the optional Evaluations evidence layer as requiring Xcode 27.

## security-policy completeness

Only the named actor may use the allowlisted synthetic tool under matching
state and policy revisions. Authority remains application policy.

## context minimization

Include only the request and constraints. Exclude the synthetic private-data
marker and keep raw user content outside committed evidence.

## failure and recovery behavior

Record one effect ledger entry. A replay emits no executor command, and an
uncertain commit is reconciled before retry.

## testability and observability

Stable check IDs, exact negative oracles, commands, and capability facts make
the result reproducible without a model or network.

## limitation honesty

This offline result does not prove host activation, Foundation Models runtime
availability, Apple Evaluations execution, or Instruments profiling.
