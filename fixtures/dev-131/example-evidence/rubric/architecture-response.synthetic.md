# Synthetic handoff architecture response

## handoff architecture fit

Route the normalized design request to one reviewer and return exactly one
final result to the declared owner. The transition graph is finite and bounded.

## context preservation

Include the request and constraints. Exclude the synthetic private-data marker.

## tool and authority correctness

Only the named actor may use the allowlisted synthetic tool under the matching
state and policy revisions.

## failure and recovery behavior

Record one effect ledger entry. A replay emits no executor command, and an
uncertain commit is reconciled before retry.

## security and privacy discipline

Authority is application policy. Evidence is synthetic, redacted, allowlisted,
and hash verified.

## evidence quality

Stable check IDs, exact negative oracles, commands, and capability facts make
the result reproducible without a model or network.

## limitations and host-boundary honesty

This offline result does not prove host activation, Foundation Models runtime
availability, Apple Evaluations execution, or Instruments profiling.
