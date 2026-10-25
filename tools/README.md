# Tools

The first executable tooling is now available for PMBus IR validation.

## Validate

Install dependencies:

```bash
python -m pip install -r tools/requirements.txt
```

Run structural JSON Schema validation and Semantic Validation v0.1 together:

```bash
python tools/validate.py validate examples/reference/qodn217a0b.pmbus.yaml
```

Run only semantic validation:

```bash
python tools/validate.py validate --semantic-only examples/reference/qodn217a0b.pmbus.yaml
```

The semantic validator checks document-internal consistency such as duplicate command codes, broken command and data-format references, invalid ranges, defaults outside ranges, and structured cross-command relationships.

See:

```text
spec/semantic-validation.md
```

The validator deliberately does not embed normative PMBus command definitions. It consumes the IR and validates the semantics represented by the IR itself.

## Planned tools

Additional planned commands remain:

```text
pmbus-ir diff <document-a> <document-b>
pmbus-ir render <document>
```

Future CLI packaging may expose the current validation entry point directly as `pmbus-ir validate`.
