# DEV-133 Deferred Validation Closure Plan

> **For Codex:** Execute this plan with `superpowers:executing-plans`,
> `superpowers:test-driven-development` for any proven defect, and
> `superpowers:verification-before-completion`.

**Goal:** Close only the three deferred DEV-133 acceptance gates when their
approved prerequisites are actually available.

**Architecture:** Treat closure as a fail-closed evidence transaction against
the merged repository guidance. Preflight the exact Claude Code 2.1.91
executable, `pre-commit`, and `markdownlint` before any model request. If any
prerequisite is unavailable or unspecified, record normalized blockers in
Linear and stop without changing repository evidence. If all prerequisites
pass, run the historical seven-assertion semantic contract read-only, run the
two required validation tools, then update only normalized DEV-133 evidence.

**Tech Stack:** POSIX shell, Claude Code 2.1.91, repository-provided Python 3
tests, `pre-commit`, `markdownlint`, Git, and Markdown evidence.

## Global Constraints

- Execute from a clean worktree based on current `origin/main`.
- Use `gpt-5.6-sol` at medium reasoning for execution and high reasoning for
  formal review.
- Never use Claude Code 2.1.140, Codex output, a weaker linter, or version
  presence as substitute evidence.
- Do not install dependencies, copy credentials, alter authentication, add
  configuration, or change repository guidance to make a gate pass.
- Capture one explicit executable per host/tool row, invoke only it, and
  recheck identity/version after use. Initial absence or mismatch is `blocked`;
  post-capture drift is `fail`.
- Keep raw prompts, responses, reasoning, diagnostics, events, configuration,
  credentials, `PATH`, session identifiers, and literal local paths transient.
- If an in-scope repository defect is proven, stop and obtain a refreshed
  Sol-authored repair task before editing implementation.
- A no-change blocker result needs a Linear evidence comment, not a commit or
  pull request.
- This plan must first be reviewed, merged, and linked from DEV-133. Task 1's
  clean-state gate applies to a later execution checkout after that merge, not
  to this planning-only branch.

### Task 1: Preflight the exact deferred prerequisites

**Files:**

- Read: `CLAUDE.md`
- Read: `AGENTS.md`
- Read: `docs/research/evidence/dev-133-repository-guidance-e2e.md`
- Read: `.pre-commit-config.yaml` or the owner-approved equivalent, if present
- Read: `.markdownlint.json`, `.markdownlint.yaml`, or the owner-approved
  equivalent, if present

**Interfaces:**

- Input: an owner-provided absolute `DEV133_CLAUDE_BIN` identifying Claude Code
  2.1.91.
- Output: normalized prerequisite rows containing tool, version or `null`,
  `<host-path>` or `null`, stable reason, exit code, and status.

- [ ] **Step 1: Confirm clean current-main state**

```bash
git fetch origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
test -z "$(git status --short)"
```

Expected: all commands exit `0`.

- [ ] **Step 2: Capture the exact Claude executable**

```bash
test -n "${DEV133_CLAUDE_BIN:-}"
test "${DEV133_CLAUDE_BIN#/}" != "$DEV133_CLAUDE_BIN"
test -f "$DEV133_CLAUDE_BIN"
test -x "$DEV133_CLAUDE_BIN"
claude_resolved="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$DEV133_CLAUDE_BIN")"
claude_identity="$(stat -f '%d:%i:%p:%z:%m:%c' "$claude_resolved")"
"$DEV133_CLAUDE_BIN" --version
```

Expected stdout is exactly one line:

```text
2.1.91 (Claude Code)
```

Any missing candidate, nonzero exit, multiline output, path-bearing output, or
different version is `blocked`; normalize the version to `null` when malformed.

- [ ] **Step 3: Capture the required validation tools and configuration**

```bash
pre_commit_bin="$(command -v pre-commit)"
markdownlint_bin="$(command -v markdownlint)"
test -f .pre-commit-config.yaml
pre_commit_resolved="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$pre_commit_bin")"
markdownlint_resolved="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$markdownlint_bin")"
pre_commit_identity="$(stat -f '%d:%i:%p:%z:%m:%c' "$pre_commit_resolved")"
markdownlint_identity="$(stat -f '%d:%i:%p:%z:%m:%c' "$markdownlint_resolved")"
pre_commit_version="$("$pre_commit_bin" --version)"
markdownlint_version="$("$markdownlint_bin" --version)"
```

Expected: both executables resolve and return a single stable version line, and
the repository-owned pre-commit configuration exists. If the approved
Markdown configuration or exact accepted versions are not already established
in DEV-133, record `blocked:validation_contract_unspecified`; do not invent
them.

- [ ] **Step 4: Stop honestly on any blocked prerequisite**

If any prior step is blocked, add one DEV-133 comment with only normalized
rows, current `origin/main`, and the unchanged evidence path. Leave DEV-133
`In Review`. Do not edit or commit a file.

### Task 2: Execute the deferred gates only after Task 1 passes

**Files:**

- Modify only if every row passes:
  `docs/research/evidence/dev-133-repository-guidance-e2e.md`

**Interfaces:**

- Semantic output: one closed JSON object with exactly seven typed fields:
  `canonicalGuidancePath`, `generatedNonEditablePaths`,
  `generationCheckCommand`,
  `repositoryTestCommand`, `pluginSourceAndFallback`,
  `generatedManifestEditResponse`, and
  `structuralGuidanceProvesCapability`.
- Evidence output: normalized metadata and assertion counts only.

- [ ] **Step 1: Create the exact transient prompt, schema, and output paths**

```bash
set -euo pipefail
probe_dir="$(mktemp -d)"
probe_schema="$probe_dir/schema.json"
probe_prompt="$probe_dir/prompt.txt"
probe_output="$probe_dir/output.json"
cleanup_probe() {
  probe_status=$?
  set +e
  current_claude_resolved="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$DEV133_CLAUDE_BIN" 2>/dev/null)"
  current_claude_identity="$(stat -f '%d:%i:%p:%z:%m:%c' "$current_claude_resolved" 2>/dev/null)"
  current_claude_version="$("$DEV133_CLAUDE_BIN" --version 2>/dev/null)"
  rm -f "$probe_output" "$probe_prompt" "$probe_schema"
  cleanup_status=$?
  rmdir "$probe_dir"
  cleanup_status=$((cleanup_status || $?))
  trap - EXIT
  if test "$current_claude_resolved" != "$claude_resolved" ||
     test "$current_claude_identity" != "$claude_identity" ||
     test "$current_claude_version" != "2.1.91 (Claude Code)"; then
    printf '%s\n' \
      'probe=claude-repository-guidance status=fail reason=host_identity_or_version_drift' >&2
    exit 1
  fi
  if test "$cleanup_status" -ne 0; then
    printf '%s\n' \
      'probe=claude-repository-guidance status=fail reason=cleanup_incomplete' >&2
    exit 1
  fi
  exit "$probe_status"
}
trap cleanup_probe EXIT
python3 - "$probe_schema" "$probe_prompt" <<'PY'
import json
import pathlib
import sys

schema_path, prompt_path = map(pathlib.Path, sys.argv[1:])
properties = {
    "canonicalGuidancePath": {"type": "string"},
    "generatedNonEditablePaths": {
        "type": "array",
        "items": {"type": "string"},
        "uniqueItems": True,
    },
    "generationCheckCommand": {"type": "string"},
    "repositoryTestCommand": {"type": "string"},
    "pluginSourceAndFallback": {"type": "string"},
    "generatedManifestEditResponse": {"type": "string"},
    "structuralGuidanceProvesCapability": {"type": "boolean"},
}
schema_path.write_text(
    json.dumps(
        {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }
    ),
    encoding="utf-8",
)
prompt_path.write_text(
    """Read the repository guidance that applies from this checkout and return
only the requested structured result. Identify the canonical guidance path;
all generated non-editable paths; the generation check command; the repository
test command; the selected plugin source and whether a fallback remains; how
you would handle a request to edit a generated Codex manifest directly; and
whether structural guidance or installation proves behavioral capability.
Do not execute commands or modify files.""",
    encoding="utf-8",
)
PY
```

Expected: the schema and prompt exist only below the untracked temporary
directory; the output path does not exist until the host invocation.

- [ ] **Step 2: Run the exact read-only Claude semantic probe**

```bash
"$DEV133_CLAUDE_BIN" --print --no-session-persistence \
  --permission-mode plan --output-format json \
  --json-schema "$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_text())' "$probe_schema")" \
  "$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_text())' "$probe_prompt")" \
  >"$probe_output"
```

Expected: exit `0`; the transient response validates against the closed schema
and all seven values match the current tracked `CLAUDE.md`/`AGENTS.md`
contract. Recheck executable identity and the exact version afterward. Any
host/auth/model/session failure is `blocked`; identity or version drift is
`fail`.

- [ ] **Step 3: Verify all seven semantic assertions**

```bash
python3 - "$probe_output" <<'PY'
import json
import pathlib
import sys

raw = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
actual = raw.get("structured_output")
expected = {
    "canonicalGuidancePath": "CLAUDE.md",
    "generatedNonEditablePaths": [
        "AGENTS.md",
        ".agents/plugins/marketplace.json",
        "plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json",
    ],
    "generationCheckCommand":
        "python3 scripts/sync_generated_artifacts.py --check",
    "repositoryTestCommand":
        "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover "
        "-s tests -p 'test_*.py' -v",
    "pluginSourceAndFallback":
        "./plugins/apple-foundation-models-handoff; no active fallback",
    "generatedManifestEditResponse":
        "refuse direct edit; change canonical input and run the generator",
    "structuralGuidanceProvesCapability": False,
}
if actual != expected:
    raise SystemExit("semantic_assertion_mismatch")
print("probe=claude-repository-guidance version=2.1.91 "
      "status=pass assertions=7")
PY
```

Expected: exactly the normalized one-line pass record shown in the script. The
EXIT trap always rechecks the captured executable before deleting prompt,
schema, output, and the empty temporary directory. Host drift takes precedence
over the original probe status; cleanup failure takes precedence over success.

- [ ] **Step 4: Run the approved repository validators**

```bash
set +e
"$pre_commit_bin" run --all-files
pre_commit_exit=$?
"$markdownlint_bin" '**/*.md'
markdownlint_exit=$?
current_pre_commit_resolved="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$pre_commit_bin" 2>/dev/null)"
current_markdownlint_resolved="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$markdownlint_bin" 2>/dev/null)"
current_pre_commit_identity="$(stat -f '%d:%i:%p:%z:%m:%c' "$current_pre_commit_resolved" 2>/dev/null)"
current_markdownlint_identity="$(stat -f '%d:%i:%p:%z:%m:%c' "$current_markdownlint_resolved" 2>/dev/null)"
current_pre_commit_version="$("$pre_commit_bin" --version 2>/dev/null)"
current_markdownlint_version="$("$markdownlint_bin" --version 2>/dev/null)"
set -e
if test "$current_pre_commit_resolved" != "$pre_commit_resolved" ||
   test "$current_markdownlint_resolved" != "$markdownlint_resolved" ||
   test "$current_pre_commit_identity" != "$pre_commit_identity" ||
   test "$current_markdownlint_identity" != "$markdownlint_identity" ||
   test "$current_pre_commit_version" != "$pre_commit_version" ||
   test "$current_markdownlint_version" != "$markdownlint_version"; then
  printf '%s\n' 'status=fail reason=validator_identity_or_version_drift' >&2
  exit 1
fi
test "$pre_commit_exit" -eq 0
test "$markdownlint_exit" -eq 0
```

Expected: both exit `0` with the already-approved repository configuration.
Every identity/version postcheck must also exit `0`; post-capture drift is
`fail`. Do not weaken rules or exclude files to obtain a pass.

- [ ] **Step 5: Run current merged-tree regression gates**

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p 'test_*.py' -v
bats tests/plugin_skeleton.bats
git diff --check
```

Expected: synchronized generation, all tests green with only documented skips,
Bats green, and no whitespace errors.

- [ ] **Step 6: Update normalized evidence only**

Update these existing sections without adding new peer sections:

- `Current evidence identity`: current branch, tested `origin/main` commit,
  execution date, normalized repository/host identities.
- `Current source artifact hashes`: recompute every already-listed artifact.
- `Current deterministic validation`: replace counts/results with the fresh
  generator, full-suite, Bats, validator, privacy, diff, and clean-state rows.
- `Current prerequisite snapshot`: replace the Claude, `pre-commit`, and
  `markdownlint` rows with exact version, exit code, status, and assertion count
  where applicable.
- `Historical semantic rows, not rerun`: retain every dated historical row
  unchanged.
- `Scope, privacy, and nonclaims`: remove only the now-obsolete current-blocker
  sentence; retain every runtime/capability/release nonclaim and keep the new
  closure plan explicitly separate from the historical six-path implementation
  scope.

- [ ] **Step 7: Verify the evidence delta**

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
test "$(git diff --name-only)" = \
  docs/research/evidence/dev-133-repository-guidance-e2e.md
```

Expected: all gates pass and the evidence file is the only changed path.

- [ ] **Step 8: Review, publish, and close**

Obtain fresh Sol formal review with zero unresolved findings. Commit the
evidence atomically. Before push, PR creation, merge, or Linear status change,
confirm explicit current user authority for those actions. If authorized,
publish one DEV-133 pull request, verify merged-tree equivalence after merge,
then attach exactly this normalized Linear payload:

```text
DEV-133 deferred validation closure
sourceCommit=<sha>
evidenceCommit=<sha-or-none>
claudeVersion=2.1.91
claudeStatus=pass
claudeAssertions=7
preCommitVersion=<version>
preCommitExitCode=0
markdownlintVersion=<version>
markdownlintExitCode=0
repositoryTests=<passed>/<total>
bats=<passed>/<total>
privacy=pass
cleanup=complete
review=no_findings
pr=<url-or-none>
mergeCommit=<sha-or-none>
```

Mark DEV-133 `Done` only after every field is proven and any evidence PR is
merged. If no repository file changed, use `evidenceCommit=none`, `pr=none`,
and `mergeCommit=none`; all other fields remain mandatory.
