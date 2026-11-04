# AI Policy

AI coding assistants (Claude Code, Codex, Copilot, and similar) are welcome in
this project. Much of the existing code was written with them.

## Expectations

- **You own what you submit.** Read and understand every line in your PR. You
  should be able to explain any change during review without asking the tool.
- **Run the checks yourself.** `pnpm check` must pass on your machine. Don't
  submit output an assistant claims passes without running it.
- **Say how you used it.** The PR template has a line for this. A short note
  such as "drafted tests with Claude Code, edited by hand" is enough.
- **Keep the boundary.** Assistants often reach for HTTP clients, cloud
  fallbacks, or extra models. The rules in [CLAUDE.md](CLAUDE.md) still apply,
  and `pnpm test:policy` enforces some of them.
- **No secrets or private data in prompts.** Don't paste credentials, tokens,
  or other people's logs into an external assistant.
- **Mentorship tasks are for learning.** Using an assistant is fine; having it
  produce the whole PR without your understanding defeats the purpose.

Commits may carry `Co-Authored-By` trailers for assistants.
