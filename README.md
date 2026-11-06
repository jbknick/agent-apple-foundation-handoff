# apple-offload

Local-only preprocessing for saved development artifacts using Apple Foundation
Models on macOS 27. Codex can call the runtime over STDIO MCP; the standalone
CLI uses the same runtime.

The v0 operations are diagnostic extraction, Git diff summarization, and issue
requirements extraction. Processing runs on-device by default. Apple Private
Cloud Compute is an opt-in route that falls back to on-device; there is no
third-party provider, HTTP listener, remote telemetry, OAuth, or model-requested
tool use.

## Requirements

- macOS 27 and Apple Intelligence for live `fm` processing
- Node.js 24.15 or newer
- pnpm 10

Apple's machine-wide `fm` terms must be accepted by the user before live model
checks can run. `apple-offload setup` makes that an explicit interactive stage;
it never runs from MCP or as a background side effect.

## Develop

```bash
pnpm install --frozen-lockfile
pnpm check
```

The first milestone is covered by `tests/runtime.test.ts`: a saved test log is
snapshotted, converted to validated diagnostics with line evidence, and recorded
once in local SQLite.

## CLI

```bash
pnpm build
node dist/cli.js setup
node dist/cli.js doctor
APPLE_OFFLOAD_MODE=on node dist/cli.js process diagnostics ./test.log
node dist/cli.js read <artifact-id> 1 20
node dist/cli.js stats
node dist/cli.js dashboard
node dist/cli.js purge
```

`APPLE_OFFLOAD_ROOTS` is a path-delimited allowlist and defaults to the launch
directory. `APPLE_OFFLOAD_STATE_DIR` defaults to the XDG state directory or
`~/.local/state/apple-offload`. `APPLE_OFFLOAD_MODE` defaults to `shadow`.
Runs share that state database across projects and worktrees. Each new run is
grouped by the launch directory name; set `APPLE_OFFLOAD_WORKSPACE` to choose a
stable display label.

`dashboard` writes a metadata-only static Site checkout to
`.apple-offload/dashboard-site`. It includes aggregate and recent run metadata,
but excludes prompts, artifacts, evidence, paths, run IDs, and model responses.
It never uploads automatically: publishing or refreshing the private Site is a
separate user-triggered Sites action.

## MCP

```bash
node dist/mcp.js
```

The MCP process reserves stdout for JSON-RPC. Operational messages go to stderr.

## Personal plugin

The canonical package is `plugins/apple-offload`. The staged personal copy is
`~/plugins/apple-offload` and is listed by the personal marketplace at
`~/.agents/plugins/marketplace.json`.

```bash
codex plugin add apple-offload@personal
codex plugin uninstall apple-offload@personal
```

In a fresh Codex task, save a test log with an already-approved shell command,
then ask the routing skill to call `offload_process` with task `diagnostics` and
that saved path. Evidence can be fetched with `offload_read` by artifact ID and
the cited 1-based line range.

## Claude Code plugin

The same package installs in Claude Code. It reuses the bundled MCP server and
skill; `.claude-plugin/plugin.json` only adds Claude Code's launch settings.

Install from this repository's marketplace (Claude Code 2.1.275 or later):

```text
/plugin install apple-offload --marketplace jbknick/agent-apple-foundation-handoff
```

Or add the marketplace first, then install:

```text
/plugin marketplace add jbknick/agent-apple-foundation-handoff
/plugin install apple-offload@apple-offload
```

For a local checkout, run `pnpm build:plugin`, then start Claude Code with
`claude --plugin-dir ./plugins/apple-offload`.

The tools appear as `mcp__plugin_apple-offload_apple_offload__offload_process`
and its three siblings. Approved folders default to the Claude Code project
directory only (`APPLE_OFFLOAD_ROOTS=${CLAUDE_PROJECT_DIR}`); files elsewhere
return `blocked`. Processing starts in `shadow` mode, as with Codex. Run
`apple-offload setup` yourself before any live `fm` processing.

## Live Apple verification

Run `node dist/cli.js setup` in an interactive terminal. It explains the
machine-wide effect, requires the exact confirmation `ACCEPT`, launches Apple's
own privileged `fm license` flow, and then runs `doctor`. The setup command is
the only project path allowed to invoke license acceptance. A live result is
valid only when installed help, default on-device selection, schema generation,
structured response, and the offline run are actually executed.

The current verification record is in [docs/benchmark.md](docs/benchmark.md).

## Who uses it

Developers who run coding agents on a Mac and want routine artifact reading
(test logs, diffs, issue text) handled by the on-device Apple model instead of
spending agent context on it.

## Code layout

| Path | Contents |
| --- | --- |
| `src/runtime.ts` | `AppleOffloadRuntime`: snapshotting, root and symlink policy, deterministic extraction, chunked local generation, evidence validation |
| `src/apple-local.ts` | `AppleLocalProvider`: probes and calls `/usr/bin/fm` |
| `src/provider.ts` | `Provider` interface and `MockProvider` for tests |
| `src/store.ts` | SQLite metadata store: runs, feedback, stats, dashboard snapshot |
| `src/schemas.ts` | Zod schemas for MCP inputs and results |
| `src/mcp.ts`, `src/cli.ts` | STDIO MCP server and CLI entry points |
| `src/dashboard.ts`, `src/setup.ts` | Static dashboard export and interactive license setup |
| `plugins/apple-offload/` | Packaged plugin: Codex and Claude Code manifests, `.mcp.json`, skill, bundled `dist/` |
| `scripts/` | Generated-artifact sync, boundary policy check, CLI, STDIO and Claude Code plugin smoke tests |
| `tests/` | Vitest suites and fixtures |
| `docs/` | Design notes, [glossary](docs/glossary.md), and the live verification record |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
and [AI_POLICY.md](AI_POLICY.md).

## License

[MIT](LICENSE).
