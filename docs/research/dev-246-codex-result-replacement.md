# DEV-246 Codex result-replacement capability result

## Current verdict

Exact host version: `0.145.0`

Status: `blocked`

Reason: `host_replacement_unavailable`

The captured executable passed strict preflight and the official manual and
synthetic plugin were hash-bound. The frozen official manual states both that
`suppressOutput` is parsed but not implemented and that it is not currently
supported for `PostToolUse`. The probe therefore stopped before authentication,
marketplace registration, plugin installation, hook trust, or a model task.

Running the documented unsupported effect could not prove replacement, so no
credential was requested or copied from the user's default Codex home. The
normalized evidence contains no raw prompt, tool result, response, transcript,
configuration, credential, or private executable path.

## Evidence identity

- Manual SHA-256:
  `6cff0c5701d5a8b10ae497b5dda6ee70f478518d4fa029558168ee2bcc18918b`
- Synthetic plugin SHA-256: read from the normalized evidence and verified
  against the clean fixture by the deterministic test suite.
- Executable identity: `<host-path>`
- Strict version preflight exit code: `0`
- Hook invocations: `0`
- Trust confirmed: `false`
- Cleanup: `complete`

## Limitation and downstream action

This row records the authoritative host-contract blocker. It does not infer
capability from model prose or feedback and it does not claim a direct
next-request observation.

DEV-143, DEV-144, DEV-139, DEV-140, and DEV-141 are canceled after this
terminal blocker rather than advertised as implementation-ready. The project
must not adopt feedback-only output, transcript mutation, an additional parent
turn, an MCP detour, or another runtime. Resumption requires a later
owner-approved Codex baseline whose official contract supports model-visible
replacement, followed by a refreshed spec, Sol-authored plans, and exact-host
proof.
