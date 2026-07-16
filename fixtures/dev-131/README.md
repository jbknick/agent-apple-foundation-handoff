# DEV-131 offline evaluation proof

This fixture tree is a research proof for DEV-131, not the production harness
owned by DEV-139. It uses only the Python standard library and synthetic data.
It does not load a model, use a network, inspect credentials, require Apple
Foundation Models, or claim that a plugin was activated in either host.

The input cases contain normalized policy and result data. Expected statuses
and exact violation IDs exist only in `index.json`; `evaluate_case` cannot read
that oracle. The example evidence bundle is allowlisted and SHA-256 verified.
Rubric validation proves record integrity and thresholds, while a human reviewer
owns semantic scores.

Run the complete proof with:

```bash
python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v
python3 fixtures/dev-131/proof_runner.py
python3 -m compileall -q fixtures/dev-131
```

A missing optional host denominator is emitted as `not_applicable`. It is never
converted to a perfect rate or an offline capability pass.
