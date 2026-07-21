# DEV-142 deterministic contract proof

This repository-only proof verifies the closed `diagnostic-condensation-v1`
contract for `condense_diagnostic_output`. It runs with the Python standard
library and synthetic, hash-bound corpus inputs only.

Run the focused proof and refresh its committed normalized evidence with:

```bash
python3 fixtures/dev-142/proof_runner.py --output \
  docs/research/evidence/dev-142-contract-verification.json
python3 fixtures/dev-142/proof_runner.py --output /tmp/dev-142-proof.json
cmp docs/research/evidence/dev-142-contract-verification.json /tmp/dev-142-proof.json
```

The proof semantically validates all three schemas and their closed custom
vocabulary, validates the 24-case corpus and its aggregate SHA-256, exercises
command/routing and policy boundaries with injected deterministic outcomes,
scores every reviewed corpus expectation, and checks both provider-
normalization formulas plus the complete 96 arms and 48-pair release
arithmetic. Its JSON is sorted, indented, atomic when written to `--output`,
and limited to normalized metadata.

`status: pass` means only that this deterministic contract proof passed. It
does not invoke Apple, does not activate a host hook, does not execute a source
command, and does not establish parent-token savings. The live cost claim
remains `blocked/provider_usage_not_executed` until paired live provider usage
and the other release prerequisites are available. The evidence contains no
diagnostics, model content, credentials, paths, traces, or runtime telemetry.
