#!/usr/bin/env bats

setup() {
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd -P)"
  SCRIPT="$REPO_ROOT/scripts/sync_generated_artifacts.py"
}

copy_canonical_inputs() {
  destination="$1"
  mkdir -p \
    "$destination/.claude-plugin" \
    "$destination/metadata" \
    "$destination/plugins/apple-foundation-models-handoff/.claude-plugin" \
    "$destination/plugins/apple-foundation-models-handoff/metadata" \
    "$destination/scripts"
  cp "$REPO_ROOT/CLAUDE.md" "$destination/CLAUDE.md"
  cp "$REPO_ROOT/.claude-plugin/marketplace.json" \
    "$destination/.claude-plugin/marketplace.json"
  cp "$REPO_ROOT/metadata/codex-marketplace.json" \
    "$destination/metadata/codex-marketplace.json"
  cp "$REPO_ROOT/plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json" \
    "$destination/plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json"
  cp "$REPO_ROOT/plugins/apple-foundation-models-handoff/metadata/codex-interface.json" \
    "$destination/plugins/apple-foundation-models-handoff/metadata/codex-interface.json"
  cp -R "$REPO_ROOT/plugins/apple-foundation-models-handoff/skills" \
    "$destination/plugins/apple-foundation-models-handoff/skills"
  cp "$SCRIPT" "$destination/scripts/sync_generated_artifacts.py"
}

snapshot_generated_outputs() {
  repository="$1"
  snapshot="$2"
  mkdir -p \
    "$snapshot/.agents/plugins" \
    "$snapshot/plugins/apple-foundation-models-handoff/.codex-plugin"
  cp "$repository/AGENTS.md" "$snapshot/AGENTS.md"
  cp "$repository/.agents/plugins/marketplace.json" \
    "$snapshot/.agents/plugins/marketplace.json"
  cp "$repository/plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json" \
    "$snapshot/plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json"
}

compare_generated_outputs() {
  repository="$1"
  snapshot="$2"
  cmp "$repository/AGENTS.md" "$snapshot/AGENTS.md"
  cmp "$repository/.agents/plugins/marketplace.json" \
    "$snapshot/.agents/plugins/marketplace.json"
  cmp "$repository/plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json" \
    "$snapshot/plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json"
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
