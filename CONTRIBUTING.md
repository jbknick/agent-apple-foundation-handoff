# Contributing to apple-offload

Thanks for helping. This guide covers local setup, checks, conventions, and
review. New to the project's terms? See [docs/glossary.md](docs/glossary.md).
Read [CLAUDE.md](CLAUDE.md) first: it is the authority for the product
and safety boundary, and a change that crosses it will not be merged.

## Set up locally

Requirements:

- Node.js 24.15 or newer
- pnpm 10.31.0 (`corepack enable` picks up the version pinned in `package.json`)
- Python 3 (used by the generated-artifact check)
- macOS 27 with Apple Intelligence only if you want to run live `fm` checks;
  everything else works on Linux or older macOS

```bash
git clone https://github.com/jbknick/agent-apple-foundation-handoff.git
cd agent-apple-foundation-handoff
pnpm install --frozen-lockfile
pnpm check
```

## Run tests and checks

`pnpm check` is the full gate and is what CI runs. It chains:

| Command | What it does |
| --- | --- |
| `pnpm check:generated` | Verifies `AGENTS.md` matches the generated section of `CLAUDE.md` |
| `pnpm typecheck` | `tsc --noEmit` |
| `pnpm test` | Vitest unit tests in `tests/` |
| `pnpm build` / `pnpm build:plugin` | Compiles `dist/` and the bundled plugin in `plugins/apple-offload/dist` |
| `pnpm test:cli` / `pnpm test:stdio` | Smoke tests for the CLI and the STDIO MCP server |
| `pnpm test:policy` | `scripts/check-boundaries.mjs`, which rejects forbidden imports and patterns in `src/` |

While iterating, `pnpm test` or `pnpm vitest run tests/runtime.test.ts` is
faster. Use `MockProvider` from `src/provider.ts` for anything that would
otherwise need the Apple model, so tests pass on Linux CI.

There is no separate linter; `tsc` in strict mode and `git diff --check`
(whitespace) are the style gates.

Rules for tests:

- Never call `apple-offload setup` or `fm license` from a test, script, or CI.
  License acceptance belongs to the user, in an interactive terminal.
- Hardware-dependent checks count as passing only when they actually ran on
  Apple hardware. Do not mock a live result and report it as live.
- If you edit `CLAUDE.md`, run `python3 scripts/sync_generated_artifacts.py --write`
  and commit the regenerated `AGENTS.md`.
- If you change anything under `src/`, run `pnpm build:plugin` and commit the
  updated `plugins/apple-offload/dist/` bundle.

## Branches and commits

- Branch from `main`. Name branches `<type>/<issue-number>-<short-slug>`, for
  example `feat/12-reason-breakdown` or `docs/15-stats-guide`.
- Use [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`. Keep the subject
  under 72 characters, in the imperative mood.
- Keep each PR to one issue. Small PRs get reviewed faster.

## Open a pull request

1. Comment on the issue you want so it can be assigned to you.
2. Push your branch and open a PR into `main`. The template asks for a summary,
   the linked issue (`Closes #N`), and how you tested it.
3. Make sure `pnpm check` passes locally. `main` is protected: every change
   lands through a pull request.

## Review

- The maintainer reviews PRs within 2 business days. Mentorship-program PRs
  are prioritized.
- Expect review comments on correctness, the safety boundary in `CLAUDE.md`,
  and tests. Push follow-up commits to the same branch; don't force-push after
  review has started unless asked.
- PRs are merged with a merge commit once checks pass and review is resolved.

## Ask questions

- For questions about an issue, comment on that issue.
- For anything else, open a
  [discussion-style issue](https://github.com/jbknick/agent-apple-foundation-handoff/issues/new/choose)
  with the `question` label.
- For conduct concerns, see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## AI tools

See [AI_POLICY.md](AI_POLICY.md).
