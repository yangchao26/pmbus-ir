# Semantic Validation v0.1

## Purpose

Semantic validation checks whether a PMBus IR document is internally consistent after it has passed structural JSON Schema validation.

It is intentionally separate from the PMBus specification itself. The validator does not embed normative definitions of PMBus commands and does not attempt to decide whether a device implementation complies with the PMBus standard.

The v0.1 implementation is in:

```text
tools/semantic_validator.py
```

The combined schema + semantic validation entry point is:

```text
tools/validate.py
```

## Validation model

Validation is performed in two layers:

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
            - internal consistency
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

v0.1 validates:

- command-level persistence references such as `commit_command` and `restore_command`;
- `constraints[].other_command` relation references;
- data-format exponent source commands;
- document-level `command` and `*_command` references under:
  - `standards`;
  - `addressing`;
  - `telemetry`;
  - `configuration`;
  - `status`;
  - `faults`;
  - `persistence`;
  - `behavior`.

`extensions` and `source_conflicts` are deliberately excluded. They may preserve names mentioned by source material even when those names are not part of the implemented normative `commands` map.

## Scalar and relation rules

### `invalid_range`

For scalar ranges, `min` must not be greater than `max`.

### `default_outside_range`

When a command has both a numeric scalar range and a single numeric default, the default must lie inside the declared range.

Variant-dependent defaults under `default.cases` are not evaluated in v0.1.

### `constraint_unit_mismatch`

A structured relation between two commands with different engineering units is rejected when no explicit relation unit is provided.

This check does not perform unit conversion in v0.1.

### `default_violates_constraint`

When both related commands have single numeric defaults, a structured relation constraint is evaluated against those defaults.

For example:

```yaml
constraints:
  - kind: relation
    operator: ge
    other_command: VIN_OFF
    offset: 2.0
    unit: V
```

means:

```text
VIN_ON >= VIN_OFF + 2.0 V
```

Supported relation operators are:

```text
gt
ge
lt
le
eq
ne
```

## Data IR format rules

The detailed model is defined in `spec/data-model.md`.

### `format_wire_width_mismatch`

A known numeric format descriptor must use its defined wire width. Data IR v0.1 recognizes:

```text
linear11    -> 2 bytes
vout_linear -> 2 bytes
```

### `format_payload_width_mismatch`

When a command references a reusable format with a declared `wire_bytes`, or uses a known inline numeric format, `commands.*.data.bytes` must match that width.

### `format_kind_mismatch`

`linear11` and `vout_linear` are scalar numeric formats. A command cannot select one of these formats while declaring a non-scalar `data.kind`.

### `invalid_fixed_exponent`

A declared fixed exponent for the v0.1 linear formats must fit the signed 5-bit exponent range:

```text
-16 .. 15
```

### `linear11_representation_mismatch`

When the expanded LINEAR11 representation is explicitly written, the validator requires the expected signed 11-bit mantissa and signed 5-bit exponent representation.

The compact form:

```yaml
format:
  type: linear11
```

already carries that representation meaning and does not require those fields to be repeated.

### `vout_linear_representation_mismatch`

When the expanded VOUT Linear representation is explicitly written, the mantissa must be represented as unsigned 16-bit data.

### `encoding_resolution_mismatch`

If a fixed exponent is known, the encoding LSB is:

```text
2 ^ fixed_exponent
```

A declared `encoding_resolution` must equal that value.

The same check is applied to reusable format-level source fields such as the QODN217A0B reference descriptor's `resolution_v`.

### `ambiguous_resolution_semantics` — warning

The early reference model used a generic `resolution` field before the distinction between encoding LSB and source-published device resolution was made explicit.

When that legacy field materially differs from the fixed-exponent encoding LSB, the validator emits a warning rather than an error.

New documents should use:

```yaml
encoding_resolution:
published_resolution:
```

This preserves source-derived values that do not equal the wire encoding LSB instead of silently rewriting them.

### `step_not_encoding_multiple`

When a fixed exponent is known, a declared programming `step` must be an integer multiple of the encoding LSB.

## Bit-field rules

### `invalid_bit_field_width`

A `bit_field` must declare at least one byte.

### `invalid_bit_index`

Bit keys must represent non-negative integer bit positions.

### `bit_out_of_range`

For `bytes: N`, valid bit positions are:

```text
0 .. (8 * N - 1)
```

## String and block rules

### `invalid_block_length`

A command using `read_block` or `write_block` must declare a positive data byte count.

### `invalid_string_length`

String data must declare a positive byte count.

### `string_requires_block_transaction`

String data must use block transaction semantics in Data IR v0.1.

### `missing_string_encoding`

String data must declare an encoding.

### `string_default_too_long`

A literal default string may not exceed the command's declared data byte count.

The validator does not infer vendor-specific padding, terminators, or whether a vendor table includes the SMBus block-count byte unless that convention is explicitly represented.

## Other data rules

### `none_data_has_payload`

`data.kind: none` requires `bytes: 0`.

## Error and warning format

The CLI reports a stable severity, code, document path, and human-readable message.

Example:

```text
ERROR unknown_format_ref $.commands.READ_VOUT.data.format_ref: format_ref 'missing' is not defined under data_formats.
WARNING ambiguous_resolution_semantics $.commands.READ_IOUT.data.resolution: ...
```

Stable codes are intended to support CI, editor integration, and future machine-readable output.

## CLI

Install the current tool dependencies:

```bash
python -m pip install -r tools/requirements.txt
```

Run structural and semantic validation together:

```bash
python tools/validate.py validate examples/reference/qodn217a0b.pmbus.yaml
```

Run semantic validation only:

```bash
python tools/validate.py validate --semantic-only examples/reference/qodn217a0b.pmbus.yaml
```

A document with no errors returns exit code `0`, even when warnings are present. A validation error returns exit code `1`. Input or file-loading failures return exit code `2`.

## Deliberate non-goals for v0.1

The semantic validator does not yet:

- reproduce or enforce normative PMBus command definitions;
- infer unsupported commands from absence;
- reconcile conflicting source statements;
- evaluate variant-dependent `default.cases`;
- perform engineering-unit conversions;
- prove every possible cross-command setting is valid;
- validate runtime state machines or timing sequences;
- validate dynamic limits that depend on runtime state;
- infer undocumented block-count-byte, padding, or terminator conventions;
- require manufacturer-specific commands that are only mentioned in source text but have no published command code.

## Next semantic layers

Likely follow-on rules include:

- persistence command roles and access semantics;
- referenced status/fault/telemetry role validation;
- variant-dependent defaults;
- richer dynamic-limit relationships;
- page/rail/phase reference validation;
- command dependency cycles;
- explicit block-content-length semantics;
- machine-readable JSON validation output.
