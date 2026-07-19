# DEV-127 Repository Audit Command Transcript

Evidence collection range: `2026-07-16` through `2026-07-17`

This transcript normalizes the evidence gathered for DEV-127. Temporary
directories are represented as `<temporary-directory>`. The host-loading
commands were scoped to temporary configuration directories; the limits of the
available configuration-nonmutation evidence are classified in the relevant
sections below.

Evidence labels have the following meanings:

- **Established:** directly observed in the authoritative fork or installed
  host tools.
- **Reference only:** observed in the pinned upstream bstack revision and not
  authoritative for this fork.
- **Not established:** not demonstrated by authoritative fork evidence and
  reserved for an explicit downstream decision or additional proof.
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

**Not established.** Repository-native validation and generation commands are
not established for this fork. The authoritative tree contains only the three
documents listed above, with no package definition, scripts, tests, schemas, or
workflow configuration from which such commands could be derived.

**Not established.** The current fork has no plugin artifacts, so neither a
plugin architecture nor a canonical-versus-generated artifact model is
established. The upstream model documented below remains reference material
until a downstream issue explicitly selects and implements an architecture.

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
$ swiftc --version
Apple Swift version 6.3.2
Target: arm64-apple-macosx26.0
```

Exit status: `0`.

**Established.** A bare `FoundationModels` module import type-checked with
`swiftc` using the installed Command Line Tools SDK.

```console
$ printf 'import FoundationModels\n' | swiftc -typecheck -
```

Exit status: `0`; no standard output.

This establishes only that the installed Command Line Tools SDK exposes a
module that accepts a bare import. **Not established:** compilation of project
examples, because the authoritative fork contains no examples to compile.

### Historical Xcode blocker (2026-07-16/17)

**Historical evidence. Blocked.** Full-Xcode validation was unavailable because
the active developer directory was the Command Line Tools installation rather
than a full Xcode installation.

```console
$ xcodebuild -version
xcode-select: error: tool 'xcodebuild' requires Xcode, but active developer directory '/Library/Developer/CommandLineTools' is a command line tools instance
```

Exit status: `1`.

### 2026-07-19 Xcode host revalidation

**Established (limited).** On 2026-07-19, the host reported Xcode `26.6` (build
`17F113`), and `xcode-select -p` reported
`/Applications/Xcode.app/Contents/Developer`. Apple Swift was `6.3.3`; the
macOS SDK version remained `26.5`.

```console
$ xcodebuild -version
Xcode 26.6
Build version 17F113
$ xcode-select -p
/Applications/Xcode.app/Contents/Developer
$ swift --version
swift-driver version: 1.148.6 Apple Swift version 6.3.3 (swiftlang-6.3.3.1.3 clang-2100.1.1.101)
Target: arm64-apple-macosx26.0
$ xcrun --sdk macosx --show-sdk-version
26.5
```

Exit status: `0` for each command.

This revalidation establishes host Xcode tool availability and version only.
**Not established:** project example compilation, device or runtime proof, and
any `FoundationModels` behavior not run.

**Established.** For supporting command-line inspection, `jq` was present at
`/opt/homebrew/bin/jq`; `rg` availability is evidenced by successful transcript
commands; and `bats` was absent. **Not established:** the `rg` path and both
`jq` and `rg` versions were not recorded. These host-tool observations do not
establish repository-native validation or generation commands because the
authoritative fork contains no corresponding setup.

## Claude Code isolated loading

**Reference only.** Claude Code validated, discovered, installed, and enabled
the representative `me@bstack` plugin from the pinned upstream checkout using
an isolated configuration directory.

```console
$ claude_home="$(mktemp -d /tmp/dev127-claude-home.XXXXXX)"
```

Exit status: `0`. Normalized value of `claude_home`:
`<temporary-directory>`.

```console
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin validate "$upstream_dir/plugins/me"
Validation passed
```

Exit status: `0`.

```console
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin marketplace add "$upstream_dir" --scope user
```

Exit status: `0`. Normalized result: the pinned upstream marketplace was added
inside the isolated Claude Code configuration directory.

```console
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin list --available --json |
>   jq -e '.available[] | select(.pluginId == "me@bstack")'
{
  "pluginId": "me@bstack",
  "version": "17.32.1"
}
```

Exit status: `0` for the pipeline.

```console
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin install me@bstack --scope user
```

Exit status: `0`. Normalized result: `me@bstack` was installed inside the
isolated Claude Code configuration directory.

```console
$ CLAUDE_CONFIG_DIR="$claude_home" claude plugin list --json |
>   jq -e '.[] | select(.id == "me@bstack" and .enabled == true)'
{
  "id": "me@bstack",
  "enabled": true
}
```

Exit status: `0` for the pipeline. Normalized value of `upstream_dir`:
`<temporary-directory>`.

**Not established.** Setting `CLAUDE_CONFIG_DIR` scoped the observed commands
to the temporary directory, but no before-and-after diff of the ordinary host
configuration was captured. A broader claim that every user-level Claude Code
configuration file remained unchanged is therefore not established by this
transcript.

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
`codex_home` and `upstream_dir`: `<temporary-directory>`.

**Not established.** Setting `CODEX_HOME` scoped the observed commands to the
temporary directory, but no before-and-after diff of the ordinary host
configuration was captured. A broader claim that every user-level Codex
configuration file remained unchanged is therefore not established by this
transcript.

**Reference only.** The two isolated loading demonstrations establish only
that the installed Claude Code and Codex CLIs can load a representative plugin
with the pinned upstream structure. **Not established:** the current fork does
not thereby gain a plugin, cross-host loading implementation, or the upstream
canonical-versus-generated file model.
