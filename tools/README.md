# Tools

Executable tooling is available for PMBus IR structural and semantic validation.

## Validate

Install the validator and command-line entry point from a repository checkout:

```bash
python -m pip install -e .
```

Run the packaged CLI:

```bash
pmbus-ir validate examples/reference/qodn217a0b.pmbus.yaml
pmbus-ir validate examples/reference/ebdw025a0b.pmbus.yaml
```

The earlier direct Python entry point remains supported for local development:

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
- unsigned16 fixed-scale calibration, signed16 offsets, and packed BCD descriptors;
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

The CLI is already available as `pmbus-ir validate` after `pip install -e .`. The direct `python tools/validate.py validate` entry point is retained for backward compatibility.
