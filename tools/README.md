# Tools

Executable tooling is available for PMBus IR structural and semantic validation.

## Validate

Install dependencies:

```bash
python -m pip install -r tools/requirements.txt
```

Run JSON Schema validation and Semantic Validation v0.1 together:

```bash
python tools/validate.py validate examples/reference/qodn217a0b.pmbus.yaml
```

Run only semantic validation:

```bash
python tools/validate.py validate --semantic-only examples/reference/qodn217a0b.pmbus.yaml
```

The validator checks document-internal consistency, including:

- command-code and alias uniqueness;
- command and data-format references;
- scalar ranges and defaults;
- LINEAR11 and VOUT Linear format semantics;
- encoding-resolution consistency;
- bit-field widths;
- canonical SMBus block content/count/payload lengths;
- string encoding and content length;
- cross-command relationships.

Canonical Data IR uses `encoding_resolution` and `published_resolution` explicitly. Legacy experimental `resolution` / `resolution_v` fields are accepted for compatibility but produce warnings.

For block commands, `data.bytes` means semantic content bytes. The block count prefix is represented separately under `data.block`.

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
