# Glossary

Terms used in the code, issues, and docs.

| Term | Meaning |
| --- | --- |
| **Artifact** | A saved local file the agent wants summarized: a test/build log, a Git diff, or issue text. |
| **Agent** | The coding assistant calling apple-offload, such as Codex or Claude Code. |
| **MCP** | Model Context Protocol. How the agent calls apple-offload's tools (`offload_process`, `offload_read`, `offload_feedback`, `offload_stats`). |
| **Local model** | Apple's on-device Foundation Model, called through the `/usr/bin/fm` command. |
| **PCC** | Apple Private Cloud Compute: Apple's server-side model service. Not used yet (milestone M3). What it takes to reach it: [PCC research](pcc-research.md). |
| **Route** | Which path handled a run: `deterministic` (pattern matching, no model) or `local` (the local model). |
| **Model route** | Which Apple model served a `local` run: `on_device` (default) or `pcc` (opt-in with `APPLE_OFFLOAD_ROUTE=pcc_preferred`, falling back to `on_device`). Recorded as `modelRoute`; `null` when no route served the run. |
| **Deterministic extraction** | Regex-based parsing in `src/runtime.ts` that handles well-known formats without a model. It runs first. |
| **Handoff** | Sending an artifact to the local model instead of having the agent read it. |
| **Mode** | `off` (do nothing), `shadow` (process and record, but don't return results), `on` (return results). Set by `APPLE_OFFLOAD_MODE`; default `shadow`. |
| **Status** | Result of a run: `ready` (here is the summary), `shadow` (recorded only), `needs_agent` (the agent should read the artifact itself), `blocked` (refused for policy reasons). |
| **`needs_agent`** | The "fall back to the agent" status. Formerly `needs_codex`; stored `needs_codex` rows are counted as `needs_agent`. |
| **`legacyStatus`** | Deprecated. Set to `needs_codex` on every `needs_agent` result for one minor release, then removed. The stats field `needsCodex` is likewise a deprecated alias of `needsAgent`. |
| **Reason** | Short code saying why a run fell back or was blocked, such as `no_supported_facts` or `fm_license_not_accepted`. |
| **Evidence** | Line ranges in the artifact that back up each extracted fact. Checked before results are returned. |
| **Coverage** | Whether the result covers the whole artifact (`complete`) or only part of it (`partial`). |
| **Snapshot** | A private copy of the artifact taken at processing time, kept for 24 hours. |
| **Approved roots** | Folders apple-offload may read from (`APPLE_OFFLOAD_ROOTS`). Anything outside is blocked. |
| **Skill** | `plugins/apple-offload/skills/apple-offload/SKILL.md`: instructions that tell the agent when to call apple-offload. |
| **Activation** | The agent actually deciding to call `offload_process` when it should. |
| **`MockProvider`** | A fake local model in `src/provider.ts` for tests, so they run without Apple hardware. |
| **M1–M4** | Milestones: M1 observability, M2 reliable handoff, M3 PCC, M4 Claude Code support. |
