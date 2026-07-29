# Runtime V1 production installation

Runtime V1 is a Codex `0.145.0` direct-mode `PostToolUse` consultation. Codex
executes the original command once, owns the final response, and keeps the
untouched original whenever the local Apple consultation declines or fails.
Apple Foundation Models is the only added generation provider.

## Supported host

The production proof requires:

- macOS with the installed SDK reporting exactly `26.5`;
- Apple Intelligence and `SystemLanguageModel.default` available locally;
- the exact captured `codex-cli 0.145.0` executable;
- a runnable captured Python 3 executable;
- an authenticated Codex session available to the isolated `CODEX_HOME`; and
- explicit hook trust for the inspected installed hash.

Missing authentication, trust, SDK, model, hardware, locale, or cleanup is a
blocker. Compilation, installation, or discovery alone is not a capability
pass.

## Bounded proof

From `<repo>`, capture the two executable paths and inspect the staged and
installed identities:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_production.py \
  --codex-executable <codex-path> \
  --python-executable <python-path> \
  --inspect
```

After those exact plugin and hook hashes are independently approved, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_production.py \
  --codex-executable <codex-path> \
  --python-executable <python-path> \
  --approved-plugin-sha256 <approved-plugin-sha256> \
  --approved-hook-hash <approved-hook-hash> \
  --output <evidence-output>
```

The harness performs the bounded operation:

1. Copies the canonical plugin into a temporary staging root.
2. Compiles `runtime/DiagnosticCondenser.swift` with the macOS SDK into that
   staged plugin.
3. Creates an isolated marketplace and `CODEX_HOME`, adds the marketplace, and
   installs `apple-foundation-models-handoff@agent-apple-foundation-handoff`.
4. Rejects any staged, installed, or listed identity that differs from the
   independently approved plugin and hook hashes, then writes explicit trust
   and reads back `trusted`.
5. Launches captured Codex in direct mode with exactly
   `RUNTIME_V1_PYTHON`, `RUNTIME_V1_BRIDGE_EXECUTABLE`, and
   `RUNTIME_V1_REPO_ROOT`.
6. Relies on Codex to inject `PLUGIN_ROOT`. The adapter proves that value is
   the executing installed plugin tree; the harness does not create a
   `RUNTIME_V1_PLUGIN_ROOT` alias.
   `DEV254_PROBE_COMMAND_COUNTER` and `DEV254_PROBE_PROVIDER_KEY` are isolated
   harness-only controls, not runtime configuration.
7. Runs one real Apple-applied row and one C2 no-output fallback row, each with
   one original command and the normal two parent requests only.
8. Rechecks Codex, Python, and installed-plugin identities, then removes the
   complete temporary marketplace, cache, workspaces, bridge, and isolated
   configuration.

The successful row is valid only when the next parent request contains the
validated condensation and excludes the verbose original. The fallback row is
valid only when the next request contains the byte-exact untouched original.
There is no retry, command rerun, remote inference, PCC, network model
fallback, Apple tool, or extra parent turn.

## Runtime data boundary

The adapter derives and validates application-owned source facts, applies a
conservative purpose-bound C1 grant, and sends one closed
`{diagnosticText, sourceFacts}` value to a fresh local Apple session. Apple
receives no tools or execution authority. Prompts, diagnostic content, source
facts, responses, Apple output, transcripts, tool contents, credentials,
private paths, and configuration must not be written to evidence or committed.
Only normalized hashes, versions, counters, statuses, and cleanup results may
be retained.

## Removal

The proof harness removes its isolated state automatically. For a separate
operator-created isolated home, remove only that explicitly captured directory
after verifying it is the intended `CODEX_HOME`; do not use a home-directory
or recursive wildcard target. Remove any separately staged bridge and evidence
file by their exact captured paths.

Packaging and actual parent-token savings remain unproved until DEV-255 passes
its 24-pair, 48-arm benchmark and release gates.
