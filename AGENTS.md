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
- Two Apple model routes are allowed: on-device inference through the
  installed `/usr/bin/fm` (`on_device`, the default) and Apple Private Cloud
  Compute (`pcc`). PCC is opt-in per user configuration and must be probed as
  available before use; see `docs/pcc-research.md` for what that requires.
- Route order: when the user has opted into PCC, try `pcc` first and fall back
  to `on_device`; otherwise use `on_device` only. Every run records the route
  that served it, or that none did.
- Never add third-party or non-Apple providers, HTTP listeners, OAuth, remote
  telemetry, or model-requested tools. PCC code lives only in `src/pcc-*.ts`.
- A failure on one route falls back to the next allowed route. `needs_codex`
  is returned only when every allowed route failed or validation failed; it
  never invokes a non-Apple model.
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
