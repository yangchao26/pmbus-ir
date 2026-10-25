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
     |
     +--> Semantic validation
            - cross-object references
            - uniqueness
            - internal consistency
            - cross-command relationships
```

A document is valid only when both layers pass.

## v0.1 semantic rules

### `duplicate_command_code`

A device command map must not assign the same command code to multiple canonical command identifiers.

### `alias_collides_with_command`

An alias must not collide with another canonical command identifier.

### `duplicate_alias`

The same alias must not be owned by multiple canonical commands.

### `unknown_format_ref`

Every `commands.*.data.format_ref` must refer to an entry under the document-level `data_formats` map.

### `invalid_range`

For scalar ranges, `min` must not be greater than `max`.

### `default_outside_range`

When a command has both a numeric scalar range and a single numeric default, the default must lie inside the declared range.

Variant-dependent defaults under `default.cases` are not evaluated in v0.1.

### `unknown_command_ref`

Command references must resolve to a canonical command identifier or declared alias.

v0.1 validates:

- command-level persistence references such as `commit_command` and `restore_command`;
- `constraints[].other_command` relation references;
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

## Error format

The CLI reports stable error codes, a document path, and a human-readable message.

Example:

```text
ERROR unknown_format_ref $.commands.READ_VOUT.data.format_ref: format_ref 'missing' is not defined under data_formats.
```

Stable error codes are intended to support CI, editor integration, and future machine-readable output.

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

A valid document returns exit code `0`. A validation failure returns exit code `1`. Input or file-loading failures return exit code `2`.

## Deliberate non-goals for v0.1

The first semantic validator does not yet:

- reproduce or enforce normative PMBus command definitions;
- infer unsupported commands from absence;
- reconcile conflicting source statements;
- evaluate variant-dependent `default.cases`;
- perform engineering-unit conversions;
- prove every possible cross-command setting is valid;
- validate runtime state machines or timing sequences;
- validate dynamic limits that depend on runtime state;
- require manufacturer-specific commands that are only mentioned in source text but have no published command code.

## Next semantic layers

Likely follow-on rules include:

- validating `format_ref` compatibility with command payload width;
- validating persistence command roles and access semantics;
- validating referenced status/fault/telemetry roles;
- evaluating variant-dependent defaults;
- richer dynamic-limit relationships;
- page/rail/phase reference validation;
- command dependency cycles;
- machine-readable warning severity in addition to errors.
