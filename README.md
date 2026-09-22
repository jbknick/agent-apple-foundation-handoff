# apple-offload

Local-only preprocessing for saved development artifacts using Apple Foundation
Models on macOS 27. Codex can call the runtime over STDIO MCP; the standalone
CLI uses the same runtime.

The v0 operations are diagnostic extraction, Git diff summarization, and issue
requirements extraction. There is no cloud provider, HTTP listener, remote
telemetry, OAuth, model-requested tool use, or automatic fallback model.

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
node dist/cli.js purge
```

`APPLE_OFFLOAD_ROOTS` is a path-delimited allowlist and defaults to the launch
directory. `APPLE_OFFLOAD_STATE_DIR` defaults to the XDG state directory or
`~/.local/state/apple-offload`. `APPLE_OFFLOAD_MODE` defaults to `shadow`.

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

## Live Apple verification

Run `node dist/cli.js setup` in an interactive terminal. It explains the
machine-wide effect, requires the exact confirmation `ACCEPT`, launches Apple's
own privileged `fm license` flow, and then runs `doctor`. The setup command is
the only project path allowed to invoke license acceptance. A live result is
valid only when installed help, default on-device selection, schema generation,
structured response, and the offline run are actually executed.

The current verification record is in [docs/benchmark.md](docs/benchmark.md).

## License

Noncommercial use is licensed under the PolyForm Noncommercial License 1.0.0.
See [LICENSE](LICENSE) and [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md).
