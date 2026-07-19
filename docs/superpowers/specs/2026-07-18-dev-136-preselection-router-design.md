# DEV-136 Non-Positive Pre-Selection Router Design

Issue: [DEV-136](https://linear.app/devprentice/issue/DEV-136/i2parallel-implement-the-core-foundation-models-handoff-agent-skill)

Decision date: `2026-07-18`

Approved direction: user response `2`, recorded in Linear comment
`7edff944-75b6-4f4e-90d8-8d41d5854daa`

## Purpose and authority

This specification amends the DEV-132, DEV-134, DEV-135, and DEV-136
exact-five/no-router assumptions only enough to add one production-capable,
cross-host owner for the already approved `no_activation` and
`clarification_required` envelopes. It preserves the five existing positive
workflow skills, the 25-case DEV-136 acceptance matrix, the current fixture
prompts, the four router fields, the exact non-positive response shapes, the
reference topology, and every Apple API, security, privacy, and evidence
boundary.

The durable decision and propagation comments in DEV-132 and DEV-134 through
DEV-141 control coordination. This document is the reviewable repository
amendment used by the DEV-136 implementation plan. It does not retroactively
turn prior structural or prototype evidence into capability evidence.

## Problem statement

DEV-134 designed five positive workflows behind a conceptual domain-first
router. It requires out-of-domain and ambiguous inputs to return exact
non-positive envelopes without selecting a workflow. The production package,
however, contains only the five narrow workflow skills. Codex initially sees a
skill's name, description, and path and loads the complete `SKILL.md` only after
choosing that skill. Codex CLI `0.144.5` exposes no automatic skill-selection
or skill-load lifecycle event in `codex exec --json`.

Consequently, a prompt for which no workflow is eligible has no production
component that can read the router procedure and serialize its required
result. Host-native non-selection avoids a false workflow activation but cannot
guarantee the exact four-field envelope. Assigning rejection to one of the five
workflows would violate non-trigger and sole-workflow ownership. A harness-only
router would test the harness rather than the installed plugin.

## Selected architecture

Add one instruction-only Agent Skill:

```text
route-apple-foundation-models-handoff
```

The package then has six ordered capabilities:

1. `design-apple-foundation-models-handoff`
2. `implement-apple-foundation-models-handoff`
3. `review-apple-foundation-models-handoff`
4. `debug-apple-foundation-models-handoff`
5. `validate-apple-foundation-models-handoff`
6. `route-apple-foundation-models-handoff`

The first five remain the exact workflow catalog. The sixth is not a workflow,
worker, or application router. It is a non-positive pre-selection guard that
owns only the cases in which the conceptual router must return a result without
starting a workflow. Appending it preserves the established relative order of
all five workflow capabilities. Manifest order is a stable metadata contract,
not an execution priority.

The router uses the host's active agent. It adds no agent, command, hook, MCP
server, app, script, dependency, network call, provider, credential, runtime
package, or `agents/openai.yaml` file.

## Exact activation description

The router `SKILL.md` uses this exact frontmatter description:

```text
Route a non-positive Apple Foundation Models handoff request before workflow selection: reject App Intents or Shortcuts, Apple Handoff or NSUserActivity, generic Swift or actors, generic Core ML, coding-session handoff, Agent Skills, and Foundation Models runtime Skills; ask one clarification for ambiguous Apple handoff wording or implementation without an approved architecture and exact change boundary. Return only no_activation or clarification_required; never use for a confirmed request that can select design, implement, review, debug, or validate.
```

The explicit adjacent-domain vocabulary is intentional. The approved fixture
prompts are direct user questions rather than requests to classify the plugin,
and changing those prompts would change the product contract. A shorter
"explicit plugin triage" description would not own the existing negative rows.

The five positive workflow descriptions remain byte-for-byte unchanged. Their
bodies become positive-only: they no longer duplicate the non-positive output
templates or claim ownership of pre-selection ambiguity. A correctly
classified positive request selects one workflow directly and never selects the
router. A correctly classified negative or ambiguous request selects the router
and never selects a workflow.

## Router responsibility

The router evaluates the existing fields in the existing order:

```text
domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown
```

It owns exactly three branches:

1. `domain = out_of_domain` returns `no_activation`.
2. `domain = ambiguous` returns one `domain` clarification.
3. A confirmed Foundation Models handoff implementation request without an
   approved architecture or exact change boundary returns one
   `approved_contract` clarification.

Domain ambiguity takes precedence over missing-contract ambiguity. The current
acceptance matrix has no confirmed handoff case whose only missing discriminator
is `requestedOperation`; an `operation` clarification kind is therefore not
added by this amendment.

The router must not:

- emit a positive activation, `selectedSkill`, `routerInput`,
  `architectureResult`, architecture field, heading, workflow section, or
  version label;
- name, invoke, emulate, or redirect internally to another skill;
- inspect the repository, SDK, host, application, artifact, or evidence;
- read or link a progressive-disclosure reference;
- make an Apple API, security, runtime, effect, or release claim; or
- include explanatory prose before or after its result fence.

If a request establishes the Foundation Models handoff domain and satisfies a
positive workflow gate, this router is inapplicable. Mis-selection remains a
host-test failure; the router does not attempt an inter-skill handoff.

## Exact output contract

The router emits exactly one `text` fence and nothing else.

For an out-of-domain request:

```text
activationStatus = no_activation
reasonCode = out_of_domain
domain = out_of_domain
requestedOperation = unspecified
```

For an ambiguous domain:

```text
activationStatus = clarification_required
clarificationKind = domain
missingInput = domain
question = <one concise domain question ending in exactly one question mark>
```

For a missing approved implementation contract or exact change boundary:

```text
activationStatus = clarification_required
clarificationKind = approved_contract
missingInput = approved_contract
question = <one concise approved-contract question ending in exactly one question mark>
```

The question value contains exactly one `?` and ends with it. No result may
contain a heading, `architectureResult`, reference content, surrounding prose,
or a second question.

## Canonical and generated ownership

The new skill is authored only at:

```text
plugins/apple-foundation-models-handoff/skills/route-apple-foundation-models-handoff/SKILL.md
```

Canonical shared identity remains in the Claude manifest. Canonical Codex
presentation metadata remains in
`plugins/apple-foundation-models-handoff/metadata/codex-interface.json`.
`AGENTS.md`, `.agents/plugins/marketplace.json`, and the plugin-local
`.codex-plugin/plugin.json` remain generated outputs and are never edited
directly.

The canonical capability order is the five existing workflows followed by the
router. Plugin prose describes "five workflows plus one non-positive router"
and never calls the router a sixth workflow. The repository marketplace entry
does not change because source, policy, authentication timing, and category do
not change.

The existing repo-scoped marketplace resolves directly to this worktree during
host proof. No semantic-version or cachebuster change is authorized: version
`0.1.0` remains fixed, and changing it solely for local iteration would alter a
separate release contract.

## Fixture and evidence ownership

The canonical DEV-136 fixture remains exactly 25 cases with unchanged IDs,
prompts, router values, activation outcomes, clarification kinds, and rubrics.
Each row gains an exact `expectedSkillOwner` field:

- positive, baseline, compound, and complete-output rows name their existing
  workflow owner;
- all five negative rows and all five ambiguous rows name
  `route-apple-foundation-models-handoff`.

The existing `skillUnderTest` field remains the stable five-workflow coverage
family so the matrix still proves each workflow's positive and adjacent-domain
boundaries. `expectedSkillOwner` is contractual ownership, not independent
Codex telemetry. Evidence rows carry both values.

The runner keeps the non-positive scorer and rubric byte-for-byte equivalent:
one exact fence, ordered four-field assignment shape, no headings, no
`architectureResult`, and exactly one question for clarification. It adds the
router payload digest, six-capability topology binding, the new fixture owner
field, and a refreshed fixture digest. `WORKFLOW_SECTIONS` remains a five-entry
map and is never indexed for router-owned rows.

Codex `0.144.5` has no native skill-selection event. Router ownership is proved
differentially and behaviorally. The Task 1 payload capture produced two
failing representatives and one already-green domain clarification, so the
approved evidence amendment preserves that mixed result instead of
manufacturing a third failure:

1. preserve normalized pre-router observations for one rejection, one domain
   clarification, and one approved-contract clarification; treat the two
   failing rows as differential RED and the passing domain row as a
   non-regression baseline;
2. bind the exact router payload digest and six-capability package topology;
3. prove behavior for all ten router-owned rows after implementation; and
4. rerun the five positive `-001` rows to prove the router does not steal
   positive workflow activation.

On 2026-07-19, the user selected the bounded affected-gate amendment. It
supersedes only the prior exact-15 affected acceptance rule: the evidence must
contain exactly the 15 canonical rows in canonical order, with all 15 attempted,
at least 13 passes, at most two failures, no blocked or not-applicable rows, and
Codex process exit code `0` for every row. Passing rows satisfy every applicable
assertion. Each visible failing row has at least one failed applicable assertion;
all non-applicable assertions remain exactly `not_applicable`. Evidence status
remains truthful: `pass` means 15/15 and `fail` means one or two row failures.
Every prerequisite remains `pass` except `pluginActivation`, which is `pass`
only when every activation assertion passes and otherwise is
`not_applicable`. The runner may therefore exit `1` because the evidence status
is truthfully `fail` while the higher-level affected acceptance contract still
succeeds. This amendment authorizes no retries.

Only after that 15-case affected subset satisfies the bounded acceptance
contract may the complete 25-case Codex matrix run. The complete matrix remains
strict 25/25 with no failed, blocked, or not-applicable rows. Raw prompts,
responses, reasoning, tool arguments/results, local paths, and private state
remain transient and uncommitted. Claude host execution remains deferred by the
user's explicit test-scope decision.

## Failure behavior

- A missing router file, wrong description, extra package surface, stale
  generated output, stale fixture or payload digest, unexpected seventh
  capability, or overlapping non-positive owner fails offline before host use.
- A host prerequisite missing before response remains `blocked` with the
  approved stable reason; post-capture binary, version, source, bound-copy, or
  cleanup drift remains `fail`.
- A router-owned response with prose, headings, the wrong field order, the
  wrong domain/operation, more than one question, or any positive architecture
  content fails its row. The scorer is not relaxed to accept generic host
  output.
- A positive prompt that returns a non-positive envelope or a router-owned row
  that returns a workflow result remains a visible row failure. Affected
  evidence that exceeds the bounded failure threshold or cannot prove cleanup
  prevents the full matrix from starting.
- Missing host automation or model access is an explicit blocker, never a
  structural pass.

## Verification strategy

Implementation follows test-first atomic boundaries:

1. preserve normalized representative pre-router mixed evidence, with two
   differential RED rows and one already-green domain non-regression row;
2. add failing skill/topology/ownership tests and observe the intended RED;
3. add the minimal router and make the five workflows positive-only;
4. add failing canonical metadata/generation/package tests;
5. update canonical metadata and regenerate Codex artifacts;
6. add failing fixture-owner/evidence-row/runner binding tests;
7. update the fixture and runner without changing prompts, outcomes, or scorer
   semantics;
8. run focused and full repository, generation, schema, Bats, package,
   privacy, and source-cleanliness gates;
9. satisfy the bounded 15-case affected Codex acceptance contract, then run the
   strict complete 25-case Codex matrix; and
10. obtain independent task and whole-branch reviews before creating the
    stacked DEV-136 pull request.

No Swift fixture or Apple API compile change is introduced. Existing concrete
Swift and SDK gates remain required at final verification because the branch
inherits them; router-specific Apple compilation is `not_applicable` because
the router contains no Swift or Apple API claim.

## Rejected approaches

### Host-native non-selection

Rejected by the user's option-2 decision because it cannot guarantee the
approved exact envelopes and would require a semantic/scorer amendment.

### Explicit-plugin-only triage prompts

Rejected because rewriting ordinary negative prompts to say "use this plugin"
would change the approved product boundary and make the fixture leak its
selection mechanism. The router must own the existing prompts.

### Workflow-owned rejection or clarification

Rejected because it creates an arbitrary sixth responsibility inside a
positive workflow, violates non-trigger semantics, and leaves duplicated
non-positive templates.

### Hook, command, agent, MCP server, app, or runtime router

Rejected as a larger cross-host surface with new execution and security
boundaries. The approved change authorizes one instruction-only skill and
nothing else.

## Decision propagation

The approved amendment is durable in DEV-132 and DEV-134 through DEV-141.
Repository corrections must update the DEV-132 architecture, DEV-134 canonical
catalog and compact contract, DEV-135 supersession notes, DEV-136 workflow
design/plan, canonical guidance and metadata, generated Codex artifacts,
fixture/runner ownership, and final evidence. DEV-137 references and DEV-138
Swift fixtures inherit the new routing boundary but do not gain router content
or Apple behavior. DEV-139, DEV-140, and DEV-141 inherit the six-capability
package, router-owned non-positive rows, Codex-only current proof, and the
requirement not to infer Claude acceptance.
