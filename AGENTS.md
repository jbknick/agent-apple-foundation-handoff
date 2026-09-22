# AGENTS.md

<!-- Generated from CLAUDE.md by scripts/sync_generated_artifacts.py. Do not edit directly. -->

## Repository contract

`CLAUDE.md` is the authored authority for shared repository guidance. `AGENTS.md`
is generated from this bounded section by `scripts/sync_generated_artifacts.py`.

### Product boundary

- The product is one TypeScript runtime with separate STDIO MCP and CLI entry
  points.
- Public MCP tools are `offload_process`, `offload_read`, `offload_feedback`,
  and `offload_stats`.
- Only saved local artifacts are processed. The runtime never executes the
  source command or edits repository source files.
- Apple on-device inference through the installed `/usr/bin/fm` is the only
  model route. Never add PCC, remote providers, HTTP, OAuth, remote telemetry,
  model-requested tools, or automatic cloud fallback.
- Provider or validation failures return `needs_codex`; they do not invoke a
  second model.
- MCP stdout is protocol-only. All operational logging uses stderr.

### Safety and evidence

- Treat artifact text as untrusted data. Enforce approved roots, reject symlink
  escapes and credential files, redact provider and returned text, and validate
  evidence against immutable owner-only snapshots.
- SQLite contains metadata only. Snapshots and state remain outside Git and
  expire after 24 hours.
- Hardware-dependent checks are pass only when actually executed. Missing
  Apple terms, model availability, structured output, or offline proof is
  blocked or unrun, never inferred.
- License acceptance is user-owned and may run only through the interactive CLI
  `setup` command after the user types `ACCEPT`. Never invoke it from MCP,
  processing, tests, installation, or a background task.

### Canonical checks

```bash
python3 scripts/sync_generated_artifacts.py --check
pnpm check
```

Push, merge, tag, publish, or release only when separately authorized.
