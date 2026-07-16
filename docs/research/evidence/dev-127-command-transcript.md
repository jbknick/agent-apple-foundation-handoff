# DEV-127 Repository Audit Command Transcript

Retrieval date: `2026-07-16`

This transcript normalizes the evidence gathered for DEV-127. Temporary
directories are represented as `<temporary-directory>`. No user-level Claude
Code or Codex configuration was modified.

Evidence labels have the following meanings:

- **Established:** directly observed in the authoritative fork or installed
  host tools.
- **Reference only:** observed in the pinned upstream bstack revision and not
  authoritative for this fork.
- **Blocked:** the requested check could not run successfully on this host.

## Authoritative fork

**Established.** The evidence artifact did not exist before this task.

```console
$ test ! -e docs/research/evidence/dev-127-command-transcript.md
```

Exit status: `0`.

**Established.** The authoritative fork revision is
`7ec92734127236e29ab88d66c1b41f663149ce0e`.

```console
$ git rev-parse HEAD
7ec92734127236e29ab88d66c1b41f663149ce0e
```

Exit status: `0`.

The command was captured at the authoritative revision before the DEV-127
documentation commits were created.

**Established.** The fork has one configured remote, `origin`, with the same
repository URL for fetch and push.

```console
$ git remote -v
origin  https://github.com/jbknick/agent-apple-foundation-handoff.git (fetch)
origin  https://github.com/jbknick/agent-apple-foundation-handoff.git (push)
```

Exit status: `0`.

**Established.** The authoritative revision tracks exactly three files.

```console
$ git ls-tree -r --name-only 7ec92734127236e29ab88d66c1b41f663149ce0e
COMMERCIAL-LICENSE.md
LICENSE
README.md
```

Exit status: `0`.

**Established.** Its two most recent commits were:

```console
$ git log --oneline --decorate -2
7ec9273 (HEAD -> main, origin/main, origin/HEAD) chore: initialize starter infrastructure
d5264c7 Initial commit
```

Exit status: `0`.

The decorations above are normalized to the authoritative checkout; only the
commit identities and subjects are material to this audit.

**Established.** None of the probed repository architecture paths exists at
the authoritative revision.

```console
$ for path in AGENTS.md CLAUDE.md package.json .claude-plugin .codex-plugin .agents plugins schemas scripts tests .github/workflows; do
>   if [ -e "$path" ]; then
>     printf 'PRESENT %s\n' "$path"
>   else
>     printf 'ABSENT %s\n' "$path"
>   fi
> done
ABSENT AGENTS.md
ABSENT CLAUDE.md
ABSENT package.json
ABSENT .claude-plugin
ABSENT .codex-plugin
ABSENT .agents
ABSENT plugins
ABSENT schemas
ABSENT scripts
ABSENT tests
ABSENT .github/workflows
```

Exit status: `0`.

## Pinned upstream reference

**Reference only.** The upstream bstack repository was cloned into an isolated
temporary directory and checked out at the pinned revision. It was not merged,
copied, or otherwise applied to the authoritative fork.

```console
$ upstream_dir="$(mktemp -d /tmp/dev127-bstack.XXXXXX)"
$ git clone --quiet https://github.com/baleen37/bstack.git "$upstream_dir"
$ git -C "$upstream_dir" checkout --quiet 34a04e16b8582d9ddc605563fea1f868732cca4e
$ git -C "$upstream_dir" rev-parse HEAD
34a04e16b8582d9ddc605563fea1f868732cca4e
```

Exit status: `0` for each command. Normalized value of `upstream_dir`:
`<temporary-directory>`.

**Reference only.** The pinned upstream root includes the following
directories.

```console
$ git -C "$upstream_dir" ls-tree -d --name-only HEAD
.agents
.claude-plugin
.claude
.github
docs
plugins
schemas
scripts
tests
```

Exit status: `0`.

**Reference only.** The filtered recursive inventory showed:

- `CLAUDE.md`;
- `.claude-plugin/marketplace.json`;
- `.agents/plugins/marketplace.json`;
- Claude manifests under `plugins/*/.claude-plugin/plugin.json`;
- generated Codex manifests under `plugins/*/.codex-plugin/plugin.json`;
- shared skills under `plugins/*/skills/**`;
- JSON schemas under `schemas/`;
- `scripts/generate-codex-plugin-manifests.sh`;
- `scripts/generate-codex-marketplace.sh`;
- `scripts/sync-codex-artifacts.sh`;
- `scripts/check-codex-artifacts.sh`; and
- BATS test files under `tests/`.

```console
$ git -C "$upstream_dir" ls-tree -r --name-only HEAD |
>   rg '(^|/)(AGENTS\.md|CLAUDE\.md|plugin\.json|marketplace\.json|.*sync.*|.*test.*|.*schema.*|SKILL\.md)$'
```

Exit status: `0`. The result above is summarized by artifact family to avoid
mistaking upstream paths for paths that exist in the authoritative fork.

**Reference only.** The pinned upstream Codex-artifact drift check passed and
produced no standard output.

```console
$ bash "$upstream_dir/scripts/check-codex-artifacts.sh"
```

Exit status: `0`.

## Host tooling

**Established.** The installed host tools reported these versions.

```console
$ claude --version
2.1.91 (Claude Code)
```

Exit status: `0`.

```console
$ codex --version
codex-cli 0.144.5
```

Exit status: `0`.

```console
$ swift --version
Apple Swift version 6.3.2
Target: arm64-apple-macosx26.0
```

Exit status: `0`.

**Blocked.** Full-Xcode validation is unavailable because the active developer
directory is the Command Line Tools installation rather than a full Xcode
installation.

```console
$ xcodebuild -version
xcode-select: error: tool 'xcodebuild' requires Xcode, but active developer directory '/Library/Developer/CommandLineTools' is a command line tools instance
```

Exit status: `1`.

For supporting command-line inspection, `jq` was present at
`/opt/homebrew/bin/jq`; `bats` was absent. These observations do not establish
repository-native validation because the authoritative fork contains no test
or validation setup.

## Claude Code isolated loading

**Reference only.** Claude Code validated, discovered, installed, and enabled
the representative `me@bstack` plugin from the pinned upstream checkout using
an isolated configuration directory.

```console
$ claude_home="$(mktemp -d /tmp/dev127-claude-home.XXXXXX)"
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin validate "$upstream_dir/plugins/me"
Validation passed
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin marketplace add "$upstream_dir" --scope user
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin list --available --json |
>   jq -e '.available[] | select(.pluginId == "me@bstack")'
{
  "pluginId": "me@bstack",
  "version": "17.32.1"
}
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin install me@bstack --scope user
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin list --json |
>   jq -e '.[] | select(.id == "me@bstack" and .enabled == true)'
{
  "id": "me@bstack",
  "enabled": true
}
```

Exit status: `0` for each command and pipeline. Normalized values of
`claude_home` and `upstream_dir`: `<temporary-directory>`. User-level Claude
Code configuration was not modified.

## Codex isolated loading

**Reference only.** Codex discovered, installed, and enabled the representative
`me@bstack` plugin from the pinned upstream checkout using an isolated Codex
home.

```console
$ codex_home="$(mktemp -d /tmp/dev127-codex-home.XXXXXX)"
$ CODEX_HOME="$codex_home" codex plugin marketplace add "$upstream_dir" --json |
>   jq -e 'select(.marketplaceName == "bstack")'
{
  "marketplaceName": "bstack",
  "alreadyAdded": false
}
$ CODEX_HOME="$codex_home" codex plugin list --available --json |
>   jq -e '.available[] | select(.pluginId == "me@bstack")'
{
  "pluginId": "me@bstack",
  "version": "17.32.1",
  "installed": false,
  "enabled": false
}
$ CODEX_HOME="$codex_home" codex plugin add me@bstack --json |
>   jq -e 'select(.pluginId == "me@bstack")'
{
  "pluginId": "me@bstack",
  "installedPath": "<temporary-directory>/plugins/cache/bstack/me/17.32.1"
}
$ CODEX_HOME="$codex_home" codex plugin list --json |
>   jq -e '.installed[] | select(.pluginId == "me@bstack" and .enabled == true)'
{
  "pluginId": "me@bstack",
  "installed": true,
  "enabled": true
}
```

Exit status: `0` for each command and pipeline. Normalized values of
`codex_home` and `upstream_dir`: `<temporary-directory>`. User-level Codex
configuration was not modified.

The two isolated loading demonstrations establish only that the installed
Claude Code and Codex CLIs can load a representative plugin with the pinned
upstream structure. They do **not** establish that this authoritative fork
already contains a plugin, implements cross-host loading, or has adopted the
upstream canonical-versus-generated file model.
