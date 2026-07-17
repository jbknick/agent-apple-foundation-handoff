# DEV-135 Minimal Plugin Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the minimal honest plugin package, deterministically generate its Codex metadata, and prove isolated Codex 0.144.5 structural installation without advertising unfinished skills.

**Architecture:** Canonical shared/Claude metadata lives at the repository marketplace and conventional plugin package paths. The existing Python 3 standard-library sync entry point combines shared identity with two authored Codex-only inputs to generate `AGENTS.md`, the plugin Codex manifest, and the Codex marketplace. Closed schemas, custom validators, adversarial generation tests, BATS definitions, and an isolated local Codex probe enforce the boundary.

**Tech Stack:** Python 3 standard library, `unittest`, JSON Schema documents, BATS, shell validation, Codex CLI 0.144.5, and existing Swift/Python regression fixtures.

## Global Constraints

- Work only on `codex/dev-135-minimal-plugin-skeleton`, stacked on DEV-134 commit `759013caf4d6c2662fb3266046e6b29c399a0098`.
- Use plugin ID `apple-foundation-models-handoff`, display name `Apple Foundation Models Handoff`, version `0.1.0`, and package root `plugins/apple-foundation-models-handoff`.
- Use marketplace `agent-apple-foundation-handoff`, source `./plugins/apple-foundation-models-handoff`, both category values `Developer Tools`, installation `AVAILABLE`, and authentication `ON_INSTALL`.
- Canonical inputs are `CLAUDE.md`, root `.claude-plugin/marketplace.json`, root `metadata/codex-marketplace.json`, plugin `.claude-plugin/plugin.json`, and plugin `metadata/codex-interface.json`.
- Generated outputs are only root `AGENTS.md`, root `.agents/plugins/marketplace.json`, and plugin `.codex-plugin/plugin.json`; never hand-edit them.
- Create no `skills/`, `references/`, hooks, MCP servers, commands, agents, plugin-local scripts, runtime dependencies, assets, or plugin-local README.
- Keep `skills` absent and `capabilities` equal to `[]` until DEV-136 creates complete production skills.
- Use Python 3 standard library only. Default checks require no network, credentials, PCC, paid provider, model generation, or hardware entitlement.
- Active host proof is Codex CLI `0.144.5`. Claude Code `2.1.91`, `pre-commit`, and `markdownlint` remain `blocked/deferred_by_owner`.
- `bats` is absent at planning time. Add the required BATS file, but record `blocked/missing_binary` unless that exact runner becomes available. Do not install or vendor a runner without approval.
- Do not weaken an oracle, hide a prerequisite, publish, merge, tag, or release.

## File responsibility map

| Path | Responsibility |
| --- | --- |
| `.claude-plugin/marketplace.json` | Authored Claude marketplace and conventional source. |
| `metadata/codex-marketplace.json` | Authored Codex source/order, category, and policy input. |
| `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json` | Authored shared identity and license. |
| `plugins/apple-foundation-models-handoff/metadata/codex-interface.json` | Authored Codex presentation with zero capabilities. |
| `schemas/codex-interface-input.schema.json` | Closed interface input contract. |
| `schemas/codex-marketplace-input.schema.json` | Closed marketplace input contract. |
| `scripts/sync_generated_artifacts.py` | Single read/validate/render/check/write entry point. |
| `tests/test_plugin_contract.py` | Metadata, schema, tree, parity, and honesty assertions. |
| `tests/test_generated_artifacts.py` | Multi-output validation, drift, obstruction, and race assertions. |
| `tests/plugin_skeleton.bats` | Shell-level generation, idempotence, and drift definitions. |
| `tests/e2e/codex_plugin_load.py` | Isolated Codex marketplace/install/cache probe. |
| `docs/research/evidence/dev-135-plugin-skeleton-e2e.md` | Normalized evidence and blocker matrix. |

---

### Task 1: Add canonical metadata and closed schemas

**Files:**
- Create: `.claude-plugin/marketplace.json`
- Create: `metadata/codex-marketplace.json`
- Create: `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`
- Create: `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`
- Create: `schemas/codex-interface-input.schema.json`
- Create: `schemas/codex-marketplace-input.schema.json`
- Create: `tests/test_plugin_contract.py`

**Interfaces:**
- Consumes: approved DEV-135 identity, placement, category, policy, and zero-capability decisions.
- Produces: four authored JSON inputs and two schemas consumed by Task 2.

- [ ] **Step 1: Write the failing canonical-contract test**

Create `tests/test_plugin_contract.py` with `unittest` cases that load the exact paths above and assert this contract:

```python
PLUGIN_ID = "apple-foundation-models-handoff"
VERSION = "0.1.0"
SOURCE = "./plugins/apple-foundation-models-handoff"
MARKETPLACE = "agent-apple-foundation-handoff"
REPOSITORY = "https://github.com/jbknick/agent-apple-foundation-handoff"

def test_canonical_identity_is_exact_and_honest(self):
    manifest = load_json(
        "plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json"
    )
    self.assertEqual(PLUGIN_ID, manifest["name"])
    self.assertEqual(VERSION, manifest["version"])
    self.assertNotIn("skills", manifest)
    for field in ("hooks", "mcpServers", "apps", "commands", "agents"):
        self.assertNotIn(field, manifest)

def test_codex_interface_has_zero_capabilities(self):
    interface = load_json(
        "plugins/apple-foundation-models-handoff/metadata/codex-interface.json"
    )
    self.assertEqual("Developer Tools", interface["category"])
    self.assertEqual([], interface["capabilities"])
    self.assertEqual(1, len(interface["defaultPrompt"]))
    self.assertLessEqual(len(interface["defaultPrompt"][0]), 128)

def test_marketplaces_use_the_conventional_source(self):
    claude = load_json(".claude-plugin/marketplace.json")
    codex = load_json("metadata/codex-marketplace.json")
    self.assertEqual(MARKETPLACE, claude["name"])
    self.assertEqual(SOURCE, claude["plugins"][0]["source"])
    entry = codex["plugins"][0]
    self.assertEqual({"source": "local", "path": SOURCE}, entry["source"])
    self.assertEqual(
        {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        entry["policy"],
    )
    self.assertEqual("Developer Tools", entry["category"])
    self.assertNotIn("products", entry["policy"])
```

Add schema assertions for `additionalProperties: false`, interface `defaultPrompt.maxItems: 3`, `capabilities.minItems: 0`, and marketplace `plugins.minItems/maxItems: 1`. Add a package-tree assertion that the plugin initially contains only its canonical manifest and interface input.

- [ ] **Step 2: Verify the focused test is red**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_plugin_contract -v
```

Expected: nonzero `FileNotFoundError` for missing canonical metadata; no skip.

- [ ] **Step 3: Add the canonical shared manifest**

Create `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`:

```json
{
  "name": "apple-foundation-models-handoff",
  "version": "0.1.0",
  "description": "Installable metadata scaffold for Apple Foundation Models handoff workflows; production skills are not included yet.",
  "author": {
    "name": "Joseph Knickerbocker",
    "url": "https://github.com/jbknick"
  },
  "homepage": "https://github.com/jbknick/agent-apple-foundation-handoff",
  "repository": "https://github.com/jbknick/agent-apple-foundation-handoff",
  "license": "LicenseRef-PolyForm-Noncommercial-1.0.0",
  "keywords": ["apple", "foundation-models", "handoff", "swift", "agents"]
}
```

- [ ] **Step 4: Add canonical Claude and Codex marketplace inputs**

Create `.claude-plugin/marketplace.json`:

```json
{
  "name": "agent-apple-foundation-handoff",
  "owner": {"name": "Joseph Knickerbocker"},
  "plugins": [
    {
      "name": "apple-foundation-models-handoff",
      "source": "./plugins/apple-foundation-models-handoff",
      "description": "Installable metadata scaffold for Apple Foundation Models handoff workflows; production skills are not included yet.",
      "version": "0.1.0"
    }
  ]
}
```

Create `metadata/codex-marketplace.json`:

```json
{
  "name": "agent-apple-foundation-handoff",
  "interface": {"displayName": "Agent Apple Foundation Handoff"},
  "plugins": [
    {
      "name": "apple-foundation-models-handoff",
      "source": {
        "source": "local",
        "path": "./plugins/apple-foundation-models-handoff"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
```

- [ ] **Step 5: Add the canonical Codex interface input**

Create `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`:

```json
{
  "displayName": "Apple Foundation Models Handoff",
  "shortDescription": "Inspect the installable handoff plugin scaffold.",
  "longDescription": "Metadata-only scaffold for an Apple Foundation Models handoff plugin. Production design, implementation, review, debugging, and validation skills are not included in version 0.1.0.",
  "developerName": "Joseph Knickerbocker",
  "category": "Developer Tools",
  "capabilities": [],
  "websiteURL": "https://github.com/jbknick/agent-apple-foundation-handoff",
  "defaultPrompt": [
    "Inspect the installed plugin metadata and report which capabilities are currently available."
  ]
}
```

- [ ] **Step 6: Add both closed JSON Schemas**

`schemas/codex-interface-input.schema.json` must use draft 2020-12, `type: object`, `additionalProperties: false`, and require all eight interface keys. Use `const: "Developer Tools"`, an HTTPS pattern for `websiteURL`, unique non-empty string capabilities with `minItems: 0`, and one to three non-empty prompts capped at 128 characters.

`schemas/codex-marketplace-input.schema.json` must use draft 2020-12 and close every object. Require the exact marketplace/display/plugin/source/category constants, exactly one plugin, and exactly the two policy keys with `AVAILABLE` and `ON_INSTALL`. The policy schema must reject `products`.

- [ ] **Step 7: Verify and commit the canonical contract**

Run:

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_plugin_contract -v
git diff --check
```

Expected: five focused tests pass; no generated Codex output exists.

Commit:

```bash
git add .claude-plugin metadata plugins schemas tests/test_plugin_contract.py
git diff --cached --check
git commit -m "feat(DEV-135): add canonical plugin metadata contracts"
```

---

### Task 2: Add strict validation and deterministic Codex rendering

**Files:**
- Create: `tests/test_generated_artifacts.py`
- Modify: `scripts/sync_generated_artifacts.py:1-266`

**Interfaces:**
- Consumes: Task 1 canonical files and existing `render_agents(canonical_text: str) -> str`.
- Produces: `CanonicalInputs`, `load_canonical_inputs(root: Path) -> CanonicalInputs`, `render_codex_manifest(inputs) -> bytes`, `render_codex_marketplace(inputs) -> bytes`, and `expected_artifacts(root) -> dict[Path, bytes]`.

- [ ] **Step 1: Write failing render and mutation tests**

Create `tests/test_generated_artifacts.py`. Import the sync module through `importlib.util`, copy all five canonical inputs into isolated roots, and assert:

```python
def test_expected_artifacts_are_the_exact_three_paths(self):
    artifacts = sync.expected_artifacts(ROOT)
    self.assertEqual(
        {
            Path("AGENTS.md"),
            Path(".agents/plugins/marketplace.json"),
            Path("plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json"),
        },
        set(artifacts),
    )
    for content in artifacts.values():
        self.assertTrue(content.endswith(b"\n"))
        self.assertNotIn(b"\r", content)

def test_rendered_manifest_is_honest(self):
    rendered = json.loads(sync.render_codex_manifest(sync.load_canonical_inputs(ROOT)))
    self.assertEqual("0.1.0", rendered["version"])
    self.assertEqual([], rendered["interface"]["capabilities"])
    self.assertNotIn("skills", rendered)

def test_rendered_marketplace_preserves_distinct_policy(self):
    rendered = json.loads(sync.render_codex_marketplace(sync.load_canonical_inputs(ROOT)))
    entry = rendered["plugins"][0]
    self.assertEqual("Developer Tools", entry["category"])
    self.assertEqual(
        {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        entry["policy"],
    )
```

Add table-driven isolated mutations for duplicate keys, unknown fields, wrong identity/version/source/category/policy, product gating, empty/overlong prompts, empty capability strings, non-HTTPS URLs, and Claude/Codex marketplace identity drift. Every mutation must raise `CanonicalInputError` without an absolute path.

- [ ] **Step 2: Verify missing render interfaces fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_generated_artifacts -v
```

Expected: nonzero `AttributeError` for `load_canonical_inputs` or a render function.

- [ ] **Step 3: Add the canonical model and shared validation helpers**

Add `json`, `re`, `dataclass`, and `Mapping` imports. Define:

```python
@dataclass(frozen=True)
class CanonicalInputs:
    guidance: str
    claude_marketplace: Mapping[str, object]
    codex_marketplace: Mapping[str, object]
    shared_manifest: Mapping[str, object]
    codex_interface: Mapping[str, object]

PLUGIN_ID = "apple-foundation-models-handoff"
PLUGIN_ROOT = Path("plugins") / PLUGIN_ID
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
CODEX_MARKETPLACE_INPUT = Path("metadata/codex-marketplace.json")
SHARED_MANIFEST = PLUGIN_ROOT / ".claude-plugin/plugin.json"
CODEX_INTERFACE_INPUT = PLUGIN_ROOT / "metadata/codex-interface.json"
CODEX_MANIFEST = PLUGIN_ROOT / ".codex-plugin/plugin.json"
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
GENERATED_PATHS = (Path("AGENTS.md"), CODEX_MARKETPLACE, CODEX_MANIFEST)
EXPECTED_SOURCE = "./plugins/apple-foundation-models-handoff"
STRICT_SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
```

Implement `_pairs_without_duplicates`, `_json_input`, `_closed_object`, `_string`, and `_https`. `_closed_object` rejects missing and unknown keys. `_json_input` uses the existing secure regular-file reader, UTF-8, and `object_pairs_hook`; it converts parse/type failures into `CanonicalInputError` containing only the relative path.

- [ ] **Step 4: Add exact closed validators**

Implement four validators:

```python
def _validate_shared_manifest(value):
    fields = {
        "name", "version", "description", "author", "homepage",
        "repository", "license", "keywords",
    }
    _closed_object(value, fields, fields)
    if value["name"] != PLUGIN_ID:
        raise ValueError("plugin identity")
    if STRICT_SEMVER.fullmatch(_string(value["version"])) is None:
        raise ValueError("strict semver")
    _string(value["description"])
    author = _closed_object(value["author"], {"name", "url"}, {"name", "url"})
    _string(author["name"])
    _https(author["url"])
    _https(value["homepage"])
    _https(value["repository"])
    _string(value["license"])
    if not isinstance(value["keywords"], list) or not value["keywords"]:
        raise ValueError("keywords")
    if len(set(value["keywords"])) != len(value["keywords"]):
        raise ValueError("duplicate keywords")
    for keyword in value["keywords"]:
        _string(keyword)

def _validate_codex_interface(value):
    fields = {
        "displayName", "shortDescription", "longDescription", "developerName",
        "category", "capabilities", "websiteURL", "defaultPrompt",
    }
    _closed_object(value, fields, fields)
    for field in ("displayName", "shortDescription", "longDescription", "developerName"):
        _string(value[field])
    if value["category"] != "Developer Tools":
        raise ValueError("interface category")
    if not isinstance(value["capabilities"], list):
        raise ValueError("capabilities")
    for capability in value["capabilities"]:
        _string(capability)
    prompts = value["defaultPrompt"]
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        raise ValueError("prompt count")
    for prompt in prompts:
        if len(_string(prompt)) > 128:
            raise ValueError("prompt length")
    _https(value["websiteURL"])
```

`_validate_claude_marketplace` must require the exact marketplace name/owner and one entry equal to the shared name, description, version, and conventional source. `_validate_codex_marketplace` must close every nested object and require the exact marketplace/display/plugin/source/category/policy values with no `products` key.

- [ ] **Step 5: Load canonical inputs and render explicit-order JSON**

Implement:

```python
def load_canonical_inputs(root: Path) -> CanonicalInputs:
    guidance = _read_canonical(root / "CLAUDE.md").decode("utf-8")
    shared = _json_input(root, SHARED_MANIFEST)
    claude_marketplace = _json_input(root, CLAUDE_MARKETPLACE)
    codex_interface = _json_input(root, CODEX_INTERFACE_INPUT)
    codex_marketplace = _json_input(root, CODEX_MARKETPLACE_INPUT)
    _adapter_body(guidance)
    _validate_shared_manifest(shared)
    _validate_claude_marketplace(claude_marketplace, shared)
    _validate_codex_interface(codex_interface)
    _validate_codex_marketplace(codex_marketplace, shared)
    return CanonicalInputs(
        guidance, claude_marketplace, codex_marketplace, shared, codex_interface
    )

def _json_bytes(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
```

`render_codex_manifest` must build an ordered dictionary literal with shared fields in this order: `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `interface`. The nested interface order is the canonical eight-field order. `render_codex_marketplace` must explicitly build top-level `name`, `interface`, `plugins` and nested `name`, `source`, `policy`, `category`. Do not serialize canonical mappings directly.

`expected_artifacts(root)` must return:

```python
{
    Path("AGENTS.md"): render_agents(inputs.guidance).encode("utf-8"),
    CODEX_MARKETPLACE: render_codex_marketplace(inputs),
    CODEX_MANIFEST: render_codex_manifest(inputs),
}
```

- [ ] **Step 6: Verify and commit deterministic rendering**

Run:

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_generated_artifacts -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_guidance -v
git diff --check
```

Expected: render/mutation tests and all 18 inherited guidance tests pass; CLI behavior is still the inherited single-output behavior in this commit.

Commit:

```bash
git add scripts/sync_generated_artifacts.py tests/test_generated_artifacts.py
git diff --cached --check
git commit -m "feat(DEV-135): render Codex metadata from canonical inputs"
```

---

### Task 3: Synchronize all outputs safely and add BATS definitions

**Files:**
- Modify: `scripts/sync_generated_artifacts.py`
- Modify: `tests/test_generated_artifacts.py`
- Modify: `tests/test_repository_guidance.py`
- Modify: `tests/test_plugin_contract.py`
- Modify: `CLAUDE.md`
- Generate: `AGENTS.md`
- Generate: `.agents/plugins/marketplace.json`
- Generate: `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
- Create: `tests/plugin_skeleton.bats`

**Interfaces:**
- Consumes: `expected_artifacts(root)` from Task 2.
- Produces: `synchronize(root: Path, write: bool) -> bool` across three outputs, descriptor-anchored atomic replacement, parent creation, preflight, drift, and unexpected-path detection.

- [ ] **Step 1: Add failing batch-synchronization tests**

Add subprocess cases that copy all canonical inputs and the sync script into isolated roots, then assert:

- first `--write` creates the exact three outputs;
- second `--write` is byte-idempotent and prints `generated artifacts are synchronized`;
- `--check` rejects drift in each output without writing;
- a later `.agents` obstruction prevents an earlier stale `AGENTS.md` from changing;
- a symlinked nested parent cannot mutate its external target;
- a generated output symlink cannot mutate its target;
- an unexpected file below `.agents/plugins` or plugin `.codex-plugin` fails check;
- missing nested parents are clean drift in check mode and are safely created in write mode;
- temporary swap and atomic replace failures remain normalized and clean all temporary files.

Run three new cases and expect nonzero because the current synchronizer handles only `AGENTS.md`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_generated_artifacts.GeneratedArtifactTests.test_write_creates_all_outputs \
  tests.test_generated_artifacts.GeneratedArtifactTests.test_preflight_prevents_partial_write \
  tests.test_generated_artifacts.GeneratedArtifactTests.test_nested_parent_symlink_is_rejected \
  -v
```

- [ ] **Step 2: Add descriptor-anchored parent and output operations**

Add `secrets`. Implement `_open_directory_chain(root, relative, create) -> int | None` by opening the root and every component with `O_DIRECTORY | O_NOFOLLOW` and `dir_fd`; create a missing component with `os.mkdir(..., dir_fd=parent_fd)` only in write mode. Close the previous descriptor after opening each child.

Implement `_regular_output_at(parent_fd, name)` with `os.stat(..., follow_symlinks=False)`. Implement `_write_generated_at(parent_fd, name, expected)` with a random hidden name, `O_CREAT | O_EXCL | O_NOFOLLOW`, `fsync`, inode comparison, `os.replace(..., src_dir_fd=parent_fd, dst_dir_fd=parent_fd)`, post-replace inode/type verification, and descriptor-relative cleanup.

No path-based temporary creation is allowed for nested outputs. No absolute path or raw exception may enter diagnostics.

- [ ] **Step 3: Replace the single-output synchronization loop**

Batch order must be exact:

1. render and validate all expected artifacts;
2. scan the two reserved generated namespaces for non-directory entries outside `GENERATED_PATHS`;
3. preflight every existing parent and output before any write;
4. if checking, report every missing/changed output as relative drift and write nothing;
5. if writing, create missing parents only after full preflight;
6. hold final parent descriptors while reading/replacing their output;
7. write only changed bytes; and
8. close every descriptor in `finally`.

Preserve `synchronize(root, write) -> bool`. `_synchronize` returns `(synchronized, changed)`. Diagnostics are only:

```text
<canonical-relative-path>: invalid canonical metadata input
<generated-relative-path>: generated content is out of date
<generated-relative-path>: unsafe or unwritable generated output
generated artifacts: unexpected generated path
```

- [ ] **Step 4: Update repository guidance to selected present state**

Patch `CLAUDE.md` so canonical manifest/interface/future skill/reference paths are plugin-local, root marketplace inputs remain root paths, conventional placement is selected, and DEV-135 structural installation is present. State that the five production workflows remain unimplemented until DEV-136/137 and structural evidence cannot prove capability activation.

Update `tests/test_repository_guidance.py` expected strings without weakening private-path, evidence, host-drift, or capability-proof checks. Change every isolated helper to copy all five canonical inputs.

- [ ] **Step 5: Generate outputs only through the canonical command**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --write
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
```

Expected first stdout: `updated generated artifacts`. Expected second stdout: `generated artifacts are synchronized`.

Update `tests/test_plugin_contract.py` to expect the generated `.codex-plugin/plugin.json`, assert shared identity/interface parity, and assert generated marketplace equality with the canonical Codex marketplace input. It must still prove no skills/references/agents/hooks/MCP/commands/scripts/assets.

- [ ] **Step 6: Add exact BATS shell coverage**

Create `tests/plugin_skeleton.bats` with three tests:

```bash
#!/usr/bin/env bats

setup() {
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd -P)"
  SCRIPT="$REPO_ROOT/scripts/sync_generated_artifacts.py"
}

@test "tracked generated artifacts are synchronized" {
  run env PYTHONDONTWRITEBYTECODE=1 python3 "$SCRIPT" --check
  [ "$status" -eq 0 ]
  [ "$output" = "generated artifacts are synchronized" ]
}

@test "write mode is idempotent for all generated artifacts" {
  copy_canonical_inputs "$BATS_TEST_TMPDIR/repository"
  run env PYTHONDONTWRITEBYTECODE=1 python3 \
    "$BATS_TEST_TMPDIR/repository/scripts/sync_generated_artifacts.py" --write
  [ "$status" -eq 0 ]
  snapshot_generated_outputs "$BATS_TEST_TMPDIR/repository" "$BATS_TEST_TMPDIR/first"
  run env PYTHONDONTWRITEBYTECODE=1 python3 \
    "$BATS_TEST_TMPDIR/repository/scripts/sync_generated_artifacts.py" --write
  [ "$status" -eq 0 ]
  compare_generated_outputs "$BATS_TEST_TMPDIR/repository" "$BATS_TEST_TMPDIR/first"
}

@test "check mode rejects generated Codex manifest drift" {
  copy_canonical_inputs "$BATS_TEST_TMPDIR/repository"
  env PYTHONDONTWRITEBYTECODE=1 python3 \
    "$BATS_TEST_TMPDIR/repository/scripts/sync_generated_artifacts.py" --write
  printf 'drift\n' >> \
    "$BATS_TEST_TMPDIR/repository/plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json"
  run env PYTHONDONTWRITEBYTECODE=1 python3 \
    "$BATS_TEST_TMPDIR/repository/scripts/sync_generated_artifacts.py" --check
  [ "$status" -eq 1 ]
  [[ "$output" == *".codex-plugin/plugin.json: generated content is out of date"* ]]
}
```

Define `copy_canonical_inputs`, `snapshot_generated_outputs`, and `compare_generated_outputs` in the same file using `mkdir`, `cp`, and `cmp` for the exact five canonical inputs and three generated outputs. No network or home-directory state is allowed.

- [ ] **Step 7: Run complete repository checks and the BATS row honestly**

Run:

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
codex_home="${CODEX_HOME:-${HOME}/.codex}"
python3 "$codex_home/skills/.system/plugin-creator/scripts/validate_plugin.py" \
  plugins/apple-foundation-models-handoff
git diff --check
```

Then:

```bash
if command -v bats >/dev/null 2>&1; then
  bats tests/plugin_skeleton.bats
else
  printf '%s\n' 'BATS status=blocked reason=missing_binary'
  exit 2
fi
```

Expected at planning time: repository/validator gates pass; BATS exits 2 blocked. Do not substitute another runner or claim pass.

- [ ] **Step 8: Commit the synchronized package**

```bash
git add CLAUDE.md AGENTS.md .agents plugins scripts tests
git diff --cached --check
git commit -m "feat(DEV-135): generate installable Codex plugin metadata"
```

---

### Task 4: Prove isolated Codex discovery, installation, and cache integrity

**Files:**
- Create: `tests/e2e/codex_plugin_load.py`
- Create: `docs/research/evidence/dev-135-plugin-skeleton-e2e.md`

**Interfaces:**
- Consumes: Task 3 generated marketplace/manifest and canonical plugin package.
- Produces: normalized JSON status on stdout and committed structural evidence. It cannot emit capability-activation pass.

- [ ] **Step 1: Write the isolated Codex probe**

Create `tests/e2e/codex_plugin_load.py` with these exact constants and result contract:

```python
ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ID = "apple-foundation-models-handoff"
MARKETPLACE = "agent-apple-foundation-handoff"
PLUGIN_ROOT = ROOT / "plugins" / PLUGIN_ID
VERSION_RE = re.compile(r"^codex-cli 0\.144\.5$")
EXPECTED_CACHE_FILES = {
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "metadata/codex-interface.json",
}
```

Use `shutil.which("codex")` once, invoke only the captured executable, require strict version `codex-cli 0.144.5`, and recheck resolution plus exact version after all operations. Missing/non-runnable/wrong version returns exit 2 with:

```json
{"evidenceId":"E-CODEX-LOAD-001","reason":"missing_binary_or_version_mismatch","status":"blocked"}
```

In a fresh `TemporaryDirectory`, set only `CODEX_HOME` and run:

```python
["plugin", "marketplace", "add", str(ROOT), "--json"]
["plugin", "list", "--available", "--json"]
["plugin", "add", f"{PLUGIN_ID}@{MARKETPLACE}", "--json"]
["plugin", "list", "--json"]
```

Parse JSON and require:

- marketplace add `marketplaceName == agent-apple-foundation-handoff`;
- available entry `pluginId == apple-foundation-models-handoff@agent-apple-foundation-handoff`, version `0.1.0`, installed/enabled false;
- add result exact plugin ID and an installed path below the isolated `CODEX_HOME`;
- final installed entry exact ID/version with installed/enabled true;
- cached relative file set equals `EXPECTED_CACHE_FILES`;
- every cached file and source file is regular, not a symlink, and SHA-256 equal; and
- generated manifest interface capabilities equal `[]`.

Any executed contradiction returns exit 1 and normalized reason class without raw stderr or paths. Success returns exit 0 and stable sorted JSON:

```python
{
    "status": "pass",
    "evidenceId": "E-CODEX-LOAD-001",
    "host": "codex",
    "hostPath": "<host-path>",
    "hostVersion": "0.144.5",
    "marketplace": MARKETPLACE,
    "pluginId": f"{PLUGIN_ID}@{MARKETPLACE}",
    "pluginVersion": "0.1.0",
    "enabled": True,
    "capabilities": [],
    "cacheFiles": sorted(EXPECTED_CACHE_FILES),
    "canonicalManifestSha256": sha256(PLUGIN_ROOT / ".claude-plugin/plugin.json"),
    "generatedManifestSha256": sha256(PLUGIN_ROOT / ".codex-plugin/plugin.json"),
    "capabilityActivation": "blocked/production_skill_not_implemented",
}
```

- [ ] **Step 2: Run the actual Codex probe twice**

Run:

```bash
set -e
first="$(PYTHONDONTWRITEBYTECODE=1 python3 tests/e2e/codex_plugin_load.py)"
second="$(PYTHONDONTWRITEBYTECODE=1 python3 tests/e2e/codex_plugin_load.py)"
test "$first" = "$second"
printf '%s\n' "$first" | jq -e '
  select(
    .status == "pass" and
    .hostVersion == "0.144.5" and
    .pluginVersion == "0.1.0" and
    .enabled == true and
    .capabilities == [] and
    .capabilityActivation == "blocked/production_skill_not_implemented" and
    (.cacheFiles | length) == 3
  )'
```

Expected: both invocations exit 0 and emit byte-identical normalized JSON. Exit 2 is an explicit host blocker; exit 1 is a failed structural oracle.

- [ ] **Step 3: Record normalized evidence**

Use `apply_patch` to create `docs/research/evidence/dev-135-plugin-skeleton-e2e.md` with:

- candidate branch and exact tested commit;
- generator write/check/idempotence and mutation counts;
- canonical/generated identity, version, category, policy, and zero-capability parity;
- the exact normalized JSON line emitted by the probe;
- exact cache file allowlist and verified source/cache hash equality;
- `E-CODEX-ACTIVATE-001 blocked production_skill_not_implemented`;
- `E-CLAUDE-LOAD-001 blocked deferred_by_owner` with no Claude invocation;
- `BATS blocked missing_binary` unless BATS actually ran;
- `pre-commit blocked deferred_by_owner` and `markdownlint blocked deferred_by_owner`; and
- a statement that structural discovery/installation is not capability proof.

Copy every runtime count and SHA from current output. Exclude raw prompts, responses, reasoning, tool arguments, diagnostics, absolute paths, credentials, and private host state.

- [ ] **Step 4: Scan and commit Codex probe/evidence**

Run:

```bash
set -e
git diff --check
mac_root='/'"Users/"
linux_root='/'"home/"
temp_root='/'"tmp/"
if rg -n -F -e "$mac_root" -e "$linux_root" -e "$temp_root" \
  tests/e2e/codex_plugin_load.py \
  docs/research/evidence/dev-135-plugin-skeleton-e2e.md; then
  exit 1
fi
git add tests/e2e/codex_plugin_load.py \
  docs/research/evidence/dev-135-plugin-skeleton-e2e.md
git diff --cached --check
git commit -m "test(DEV-135): prove isolated Codex plugin installation"
```

---

### Task 5: Run final verification, attach evidence, and open the stacked PR

**Files:**
- Verify: every DEV-135 path
- Update only when actual evidence changes: `docs/research/evidence/dev-135-plugin-skeleton-e2e.md`

**Interfaces:**
- Consumes: all DEV-135 commits and gate catalog.
- Produces: final SHA, normalized matrix, Linear evidence, and a stacked review PR. It does not merge or release.

- [ ] **Step 1: Run generation, repository, schema, validator, and Codex gates**

Run:

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --write
git diff --exit-code -- AGENTS.md .agents/plugins/marketplace.json \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
codex_home="${CODEX_HOME:-${HOME}/.codex}"
python3 "$codex_home/skills/.system/plugin-creator/scripts/validate_plugin.py" \
  plugins/apple-foundation-models-handoff
PYTHONDONTWRITEBYTECODE=1 python3 tests/e2e/codex_plugin_load.py | \
  jq -e 'select(.status == "pass")'
```

Expected: no generation diff; all repository tests, official current Codex validation, and isolated Codex structural load pass.

- [ ] **Step 2: Run the BATS row without substitution**

```bash
if command -v bats >/dev/null 2>&1; then
  bats tests/plugin_skeleton.bats
else
  printf '%s\n' 'BATS status=blocked reason=missing_binary'
  exit 2
fi
```

If this remains blocked, DEV-135 cannot be marked Done under its current Definition of Done. The PR may be opened for review with the blocker stated.

- [ ] **Step 3: Rerun DEV-131 deterministic evaluation**

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
pycache_root="$(mktemp -d)"
PYTHONPYCACHEPREFIX="$pycache_root" python3 -m compileall -q fixtures/dev-131
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
```

Expected: 26 tests pass, 11/11 oracle matches, evidence/rubric checks pass, and zero denominator remains `not_applicable`.

- [ ] **Step 4: Rerun DEV-130 security golden**

```bash
set -e
artifact_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$artifact_dir/dev130-adversarial"
"$artifact_dir/dev130-adversarial" > "$artifact_dir/first.out"
diff -u fixtures/dev-130/expected-output.txt "$artifact_dir/first.out"
"$artifact_dir/dev130-adversarial" > "$artifact_dir/second.out"
cmp "$artifact_dir/first.out" "$artifact_dir/second.out"
rg -q '^SUMMARY passed=7 failed=0$' "$artifact_dir/first.out"
```

Expected: seven pass, zero fail, repeated output byte-identical.

- [ ] **Step 5: Rerun DEV-128 compiled SDK 26.5 matrix**

```bash
set -e
artifact_dir="$(mktemp -d)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
TARGET=arm64-apple-macos26.0
swiftc -warnings-as-errors -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/availability-probe.swift -o "$artifact_dir/availability"
"$artifact_dir/availability" > "$artifact_dir/availability.out"
rg -q '^availability=' "$artifact_dir/availability.out"
rg -q '^isAvailable=' "$artifact_dir/availability.out"
rg -q '^contextSize=[0-9]+$' "$artifact_dir/availability.out"
rg -q '^supportsCurrentLocale=' "$artifact_dir/availability.out"
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/transcript-roundtrip.swift -o "$artifact_dir/transcript"
test "$("$artifact_dir/transcript")" = 'entries=3 codableRoundTrip=true rehydrated=true'
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/session-isolation.swift -o "$artifact_dir/isolation"
test "$("$artifact_dir/isolation")" = 'parentEntries=1 childEntries=1 isolated=true'
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/baton-pass-state.swift -o "$artifact_dir/baton"
test "$("$artifact_dir/baton")" = \
  'source=research destination=review active=review finalOwner=review transferred=true'
```

Expected: five compiled checks pass.

- [ ] **Step 6: Run privacy, cache, generated-boundary, and scope checks**

```bash
set -e
git diff --check 759013caf4d6c2662fb3266046e6b29c399a0098..HEAD
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
test -z "$(find . -type f \( -name '*.trace' -o -name '*.xcresult' \) -print -quit)"
for surface in skills references agents hooks mcp commands scripts assets; do
  test ! -e "plugins/apple-foundation-models-handoff/$surface"
done
git status --short
```

Expected: clean worktree, no cache/trace/private artifacts, and no unapproved package surfaces.

- [ ] **Step 7: Invoke verification and independent review**

Read and follow `superpowers:verification-before-completion`. Re-run its required commands against final HEAD. Then use the subagent-driven workflow's specification reviewer and code-quality reviewer on the entire DEV-135 diff. Correct every finding in focused commits and rerun affected plus complete gates.

Expected: no review findings remain. BATS stays a named blocker if absent; Claude Code, `pre-commit`, and `markdownlint` stay owner-deferred.

- [ ] **Step 8: Push and open the stacked PR without merging**

Push `codex/dev-135-minimal-plugin-skeleton` and open a PR targeting `codex/dev-134-skill-architecture`. Title it `DEV-135: scaffold generated cross-host plugin metadata`.

The PR body must list conventional placement, canonical/generated ownership, commits, exact gate counts, zero skills/capabilities, structural-not-activation boundary, owner-deferred rows, and BATS missing-binary blocker if unresolved. Do not merge, tag, publish, or release.

- [ ] **Step 9: Attach Linear evidence and set truthful status**

Comment on DEV-135 with final SHA, PR URL, design/plan/evidence links, pass/fail/blocked matrix, Codex identity/version/cache/hashes, activation blocker, BATS row, and deferred rows.

If BATS is blocked, leave DEV-135 `In Review` and keep downstream blockers. If BATS passes and every non-deferred row is proven, mark DEV-135 complete only under the approved Codex-first policy. Never represent deferred Claude proof as pass.
