# DEV-127 Repository Architecture Audit Design

## Purpose

Produce a current-fork-first architecture audit that prevents later project
issues from inheriting repository structures that do not exist. The audit will
describe the repository at commit `7ec92734127236e29ab88d66c1b41f663149ce0e`, compare it with the project
brief's upstream bstack assumptions without treating upstream as authoritative,
and record every unsupported validation or host-loading claim as a blocker.

## Selected approach

Use a three-layer report:

1. An authoritative inventory derived from the tracked files, Git history,
   remotes, and locally installed host tooling.
2. A non-authoritative upstream comparison pinned to an exact bstack revision.
3. A downstream constraint table that separates established facts from
   decisions that DEV-132 and later issues must still make.

Importing upstream architecture was rejected because the current fork is
authoritative. Omitting upstream comparison was rejected because it would leave
the project's bstack-based expectations unexplained.

## Deliverables

- `docs/research/dev-127-repository-architecture.md`: durable architecture
  report with exact paths, revisions, classifications, gaps, and downstream
  constraints.
- `docs/research/evidence/dev-127-command-transcript.md`: redacted,
  reproducible commands and observed results for repository inventory,
  available validation, and Claude Code/Codex host inspection.
- `docs/superpowers/plans/2026-07-16-dev-127-repository-audit.md`: atomic
  implementation and verification plan.

No plugin, manifest, guidance adapter, generator, schema, test suite, runtime
fixture, or release file will be created by this issue.

## Evidence model

Every report claim will be one of:

- **Established:** directly observed in the authoritative fork or local tool
  output.
- **Reference only:** observed in a pinned upstream revision and explicitly
  non-authoritative for this repository.
- **Not established:** absent from the authoritative fork and reserved for a
  downstream decision.
- **Blocked:** a host-level proof could not run; the transcript includes the
  command, exit status, and reason.

Absence is not converted into an inferred bstack default.

## Validation and host behavior

The audit will run repository-native checks if they exist. Because the current
fork contains no setup or test configuration, the minimum repository proof is
tracked-file inventory, clean-status verification, `git diff --check`, and
explicit confirmation that no validation/generation command exists.

Installed `claude` and `codex` CLIs will be inspected using their help and
version surfaces. The audit must not mutate ordinary Claude Code or Codex
configuration. It may use an isolated temporary `CLAUDE_CONFIG_DIR` and
`CODEX_HOME` to install the representative plugin from the exact pinned upstream
revision solely as **Reference only** host-loading evidence. That isolated
installation neither installs nor proves the current fork. If safe isolation or
a required host check cannot be demonstrated, including full-Xcode validation,
the transcript must record the command, exit status, and explicit **Blocked**
reason rather than claim a pass.

## Downstream contract

DEV-132 must choose the canonical metadata and generation model, repository
shape, runtimes, and validation strategy. DEV-133 must establish repository
guidance. DEV-135 must scaffold the chosen plugin model. DEV-139 must validate
the implemented host-loading paths. None of those issues may cite current-fork
behavior that DEV-127 classifies as not established.

## Review and completion

The issue is ready for review only when the report and transcript agree with a
fresh clean-checkout inventory, all claims are classified, no out-of-scope files
changed, the downstream Linear decisions are present, and the issue-scoped PR
contains only DEV-127 documentation.
