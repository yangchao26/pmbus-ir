# Tests

The test suite now includes Semantic Validation v0.1 coverage.

Run:

```bash
python -m pip install -r tools/requirements.txt
python -m unittest discover -s tests -p "test_*.py"
```

Current semantic-validation coverage includes:

- a valid minimal PMBus IR document;
- duplicate command codes;
- broken command references;
- missing `format_ref` definitions;
- invalid scalar ranges;
- defaults outside declared ranges;
- cross-command default relation violations;
- the full QODN217A0B Reference IR as a regression case.

Additional planned test categories include:

- invalid JSON Schema fixtures;
- equivalent semantic representations;
- command compatibility cases;
- data-format incompatibility cases;
- behavior-difference cases;
- semantic-diff regression cases.
