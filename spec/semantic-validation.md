# Semantic Validation v0.1

## Purpose

Semantic validation checks whether a PMBus IR document is internally consistent after structural JSON Schema validation.

It is intentionally separate from the PMBus specification itself. The validator does not embed normative definitions of PMBus commands and does not decide whether a device implementation complies with the PMBus standard.

The current implementation is split across:

```text
tools/semantic_validator.py
tools/data_semantics.py
```

The combined entry point is:

```text
tools/validate.py
```

## Validation model

```text
PMBus IR YAML
     |
     +--> JSON Schema validation
     |      - document structure
     |      - command-entry structure
     |      - data-format structure
     |
     +--> Semantic validation
            - cross-object references
            - uniqueness
            - data-format compatibility
            - content/framing length consistency
            - cross-command relationships
```

A document is valid when no validation errors are present. Warnings are reported but do not cause a nonzero exit code.

## Command and reference rules

### `duplicate_command_code`

A device command map must not assign the same command code to multiple canonical command identifiers.

### `alias_collides_with_command`

An alias must not collide with another canonical command identifier.

### `duplicate_alias`

The same alias must not be owned by multiple canonical commands.

### `unknown_format_ref`

Every `commands.*.data.format_ref` must refer to an entry under the document-level `data_formats` map.

### `unknown_command_ref`

Command references must resolve to a canonical command identifier or declared alias.

v0.1 validates persistence references, relation references, data-format exponent-source commands, and document-level `command` / `*_command` references in the normative semantic domains.

`extensions` and `source_conflicts` remain excluded because they may preserve source terminology that is not part of the implemented command map.

## Scalar and relation rules

### `invalid_range`

For scalar ranges, `min` must not be greater than `max`.

### `default_outside_range`

A single numeric default must lie inside the declared scalar range.

### `constraint_unit_mismatch`

A relation between commands with different engineering units requires an explicit relation unit.

### `default_violates_constraint`

When both commands have single numeric defaults, structured relation constraints are evaluated against those defaults.

## Numeric Data IR rules

The detailed model is defined in `spec/data-model.md`.

### `format_wire_width_mismatch`

Known numeric formats must use their defined wire width:

```text
linear11     -> 2 bytes
vout_linear  -> 2 bytes
```

### `format_payload_width_mismatch`

A command's `data.bytes` must match the selected numeric representation width.

### `format_kind_mismatch`

`linear11` and `vout_linear` require `data.kind: scalar`.

### `invalid_fixed_exponent`

A fixed exponent must fit the signed five-bit range:

```text
-16 .. 15
```

### `linear11_representation_mismatch`

Expanded LINEAR11 representation fields must agree with the signed 11-bit mantissa / signed five-bit exponent model.

### `vout_linear_representation_mismatch`

Expanded VOUT Linear representation fields must agree with the unsigned 16-bit mantissa model.

### `encoding_resolution_mismatch`

When a fixed exponent is known:

```text
encoding_resolution == 2 ^ fixed_exponent
```

This applies to command-level and reusable format-level canonical `encoding_resolution` fields.

### `legacy_resolution_field` — warning

The earlier experimental fields:

```yaml
resolution:
resolution_v:
```

are ambiguous. New/reference documents must use explicit canonical fields:

```yaml
encoding_resolution:
published_resolution:
```

Legacy fields remain readable for compatibility but produce a warning through `tools/data_semantics.py`.

### `ambiguous_resolution_semantics` — legacy warning

The original semantic validator may additionally report this warning when a legacy `resolution` value materially differs from the encoding LSB. Canonical Reference IR documents should no longer contain the legacy field.

### `step_not_encoding_multiple`

A programming `step` must be an integer multiple of the fixed-exponent encoding LSB.

## Bit-field rules

### `invalid_bit_field_width`

A `bit_field` must declare at least one byte.

### `invalid_bit_index`

Bit keys must represent non-negative integer positions.

### `bit_out_of_range`

For `data.bytes: N`, valid bit positions are:

```text
0 .. (8 * N - 1)
```

## Canonical block length rules

For all block transactions, `data.bytes` means semantic content bytes. It excludes the SMBus count prefix, PEC, address, command code, and ACK/NACK framing.

A canonical block command declares:

```yaml
data:
  bytes: 4
  block:
    content_bytes: 4
    count_prefix_bytes: 1
    transaction_payload_bytes: 5
```

### `missing_block_metadata`

Every `read_block` or `write_block` command must declare `data.block`.

### `block_metadata_without_block_transaction`

`data.block` is invalid unless the command transaction is `read_block` or `write_block`.

### `block_content_length_mismatch`

The semantic content length must satisfy:

```text
data.bytes == block.content_bytes
```

### `invalid_block_count_prefix`

Data IR v0.1 models the SMBus block count prefix as exactly one byte:

```text
block.count_prefix_bytes == 1
```

### `block_transaction_payload_length_mismatch`

The transaction payload length must satisfy:

```text
block.transaction_payload_bytes ==
    block.content_bytes + block.count_prefix_bytes
```

The transaction payload length deliberately excludes PEC and bus framing.

## String rules

### `invalid_string_length`

String data must declare a positive semantic content length.

### `string_requires_block_transaction`

String data uses block transaction semantics in Data IR v0.1.

### `missing_string_encoding`

String data must declare an encoding.

### `string_default_too_long`

A literal default string may not exceed the declared semantic content length.

## Other data rules

### `none_data_has_payload`

`data.kind: none` requires `data.bytes: 0`.

## QODN217A0B reference interpretation

The public QODN217A0B quick-reference table lists `MFR_ID` as five data bytes while its default value is `OMPW`, a four-character string. The reference IR records four content bytes and one block count byte, and applies that same quick-table convention to the adjacent standard MFR block-string rows.

`MFR_MOD_DATE_LOC_SN` is preserved as a source conflict: the detailed command text states read support for a 12-byte block, while the quick-reference table also reports `DATA BYTES = 12`. The Reference IR uses 12 semantic content bytes from the detailed description and explicitly records the quick-table counting ambiguity rather than silently converting it to 11.

## Error and warning format

The CLI reports severity, stable code, document path, and human-readable message.

Example:

```text
ERROR block_content_length_mismatch $.commands.MFR_ID.data.block.content_bytes: ...
WARNING legacy_resolution_field $.commands.READ_IOUT.data.resolution: ...
```

## CLI

Install dependencies:

```bash
python -m pip install -r tools/requirements.txt
```

Run structural and semantic validation:

```bash
python tools/validate.py validate examples/reference/qodn217a0b.pmbus.yaml
```

Run semantic validation only:

```bash
python tools/validate.py validate --semantic-only examples/reference/qodn217a0b.pmbus.yaml
```

No errors returns exit code `0`; validation errors return `1`; file/input failures return `2`.

## Deliberate non-goals for v0.1

The validator does not yet:

- reproduce normative PMBus command definitions;
- infer unsupported commands from absence;
- reconcile conflicting source statements;
- infer an undocumented vendor block-count convention without an explicit IR/source interpretation;
- evaluate variant-dependent `default.cases`;
- perform engineering-unit conversions;
- validate runtime state machines or dynamic runtime limits;
- require manufacturer-specific commands that are only mentioned in source text but have no published command code.

## Next semantic layers

Likely follow-on work includes:

- persistence-role and access-semantic checks;
- page/rail/phase reference validation;
- variant-dependent defaults;
- richer dynamic limits;
- dependency-cycle detection;
- semantic diff based on normalized command and data models;
- machine-readable JSON validation output.
