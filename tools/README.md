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

The validator currently checks document-internal consistency including:

- duplicate command codes and alias collisions;
- broken command and data-format references;
- scalar ranges, defaults, and cross-command relations;
- `format_ref` versus command payload width;
- LINEAR11 and VOUT Linear representation constraints;
- fixed-exponent range and encoding-resolution consistency;
- programming step quantization;
- bit-field width and bit positions;
- string/block transaction and byte-length consistency.

Warnings are reported separately from errors and do not cause validation failure. This is used, for example, when an older ambiguous `resolution` field differs from the mathematically implied encoding LSB and should be migrated to either `encoding_resolution` or `published_resolution`.

See:

```text
spec/data-model.md
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
