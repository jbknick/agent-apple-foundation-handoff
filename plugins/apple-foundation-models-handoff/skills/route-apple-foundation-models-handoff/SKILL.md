---
name: route-apple-foundation-models-handoff
description: 'Route a non-positive Apple Foundation Models handoff request before workflow selection: reject App Intents or Shortcuts, Apple Handoff or NSUserActivity, generic Swift or actors, generic Core ML, coding-session handoff, Agent Skills, and Foundation Models runtime Skills; ask one clarification for ambiguous Apple handoff wording or implementation without an approved architecture and exact change boundary. Return only no_activation or clarification_required; never use for a confirmed request that can select design, implement, review, debug, or validate.'
---

# Route Apple Foundation Models Handoff

## Decision Procedure

domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown

1. Evaluate the four router fields in the shown order.
2. Domain ambiguity takes precedence over every other branch.
3. For `domain = ambiguous`, return the domain clarification.
4. For `domain = out_of_domain`, return no_activation.
5. For a confirmed Foundation Models handoff implementation request without both an approved architecture and an exact change boundary, return the approved-contract clarification.
6. For every confirmed request eligible for design, implement, review, debug, or validate, stop because this router is inapplicable.

## Output Contract

Return exactly one branch template as one fenced `text` block and emit nothing else.
Replace a clarification placeholder with one concise question whose value contains exactly one `?` and ends with it.

### no_activation

```text
activationStatus = no_activation
reasonCode = out_of_domain
domain = out_of_domain
requestedOperation = unspecified
```

### domain clarification_required

```text
activationStatus = clarification_required
clarificationKind = domain
missingInput = domain
question = <one concise domain question ending in exactly one question mark>
```

### approved_contract clarification_required

```text
activationStatus = clarification_required
clarificationKind = approved_contract
missingInput = approved_contract
question = <one concise approved-contract question ending in exactly one question mark>
```

## Prohibitions

- Never emit positive activation, selectedSkill, routerInput, architectureResult, an architecture field, a heading, a workflow section, or a version label.
- Never name, invoke, emulate, or redirect internally to another skill.
- Never inspect the repository, SDK, host, application, artifact, or evidence.
- Never read or link a progressive-disclosure reference.
- Never make an Apple API, security, runtime, effect, or release claim.
- Never add explanatory prose before or after the result fence.
