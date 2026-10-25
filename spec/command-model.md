# Command IR Model v0.1

This document defines the **PMBus IR Command Model v0.1**. It is derived from the first full reference implementation, `examples/reference/qodn217a0b.pmbus.yaml`, rather than from an abstract command table.

The companion machine-readable schema is `schema/command.schema.json`.

## Scope

A command entry describes **how one device implements one PMBus command**. The model captures command identity, implementation completeness, access, SMBus transaction shape, payload/data semantics, defaults, constraints, persistence, timing, behavior, and source ambiguity. It does not reproduce normative PMBus command definitions.

## Command map

Commands are stored in a map keyed by a canonical command identifier:

```yaml
commands:
  READ_VOUT:
    ...
  MFR_DEVICE_TYPE:
    ...
```

Use the standard PMBus command name for standard commands. Use the vendor-published name for manufacturer-specific commands, normalized to uppercase ASCII with `_` separators. Alternate source names may be preserved with `aliases`.

Example:

```yaml
READ_TEMPERATURE_1:
  aliases: [READ_TEMP1]
```

## Required fields

Every v0.1 command entry requires:

```yaml
code:
origin:
support:
access:
transaction:
data:
```

Optional common fields are:

```yaml
roles:
aliases:
default:
constraints:
limitations:
conditions:
persistence:
timing:
behavior:
source:
notes:
```

## `code`

`code` is the one-byte command code represented as a YAML integer. Hexadecimal authoring is recommended:

```yaml
code: 0x8B
```

Decimal integer authoring is semantically equivalent. Quoted strings such as `"0x8B"` are not valid v0.1 command-code values.

## `origin`

Allowed values:

```text
standard
manufacturer_specific
```

Semantic classification belongs in `roles`, not in `origin`.

## `support`

Allowed values:

```text
full
partial
conditional
```

- `full`: the documented implementation is fully supported.
- `partial`: only some functions, bits, modes, or response settings are implemented.
- `conditional`: availability depends on an explicit condition and therefore requires `conditions`.

Absence from `commands` does not automatically mean unsupported unless the source explicitly provides a complete supported/unsupported matrix.

## `roles`

v0.1 roles:

```text
operation
configuration
capability
persistence
protection_limit
protection_response
status
telemetry
identification
manufacturer_control
```

A command may have multiple roles.

## `access`

Allowed values:

```text
read_only
write_only
read_write
execute
```

`execute` is used for payload-free action commands such as `CLEAR_FAULTS`.

## `transaction`

Read transactions:

```text
read_byte
read_word
read_block
unknown
```

Write transactions:

```text
send_byte
write_byte
write_word
write_block
unknown
```

Read and write directions are represented separately:

```yaml
transaction:
  read: read_word
  write: write_word
```

Do not use synthetic values such as `read_write_word`.

## `data`

`data` always contains `kind` and `bytes`.

v0.1 kinds:

```text
none
scalar
bit_field
string
structured
```

Scalar example:

```yaml
data:
  kind: scalar
  bytes: 2
  format_ref: vout_linear
  quantity: voltage
  unit: V
  range: {min: 9.5, max: 12.5}
  resolution: 0.000244140625
```

Bit fields live under `data.bits`, strings use `kind: string`, and vendor-specific packed payloads may use `kind: structured` with `fields`.

A command may use either `format_ref` or inline `format`, but not both.

## `default`

Defaults use one structured field:

```yaml
default:
  value: 12.0
  raw: "0xC000"
```

Variant-dependent defaults use `cases`. If a default is not documented, omit the field rather than inventing a sentinel value.

## `constraints`

Cross-command relations are represented structurally:

```yaml
constraints:
  - kind: relation
    operator: ge
    other_command: VIN_OFF
    offset: 2.0
    unit: V
```

v0.1 supports `relation`, `dynamic_limit`, and `allowed_values` constraint kinds.

## `limitations`

Use `limitations` to state why a command is only partially implemented.

## `conditions`

Conditions affect availability or behavior. Each condition requires `kind` and remains extensible in v0.1.

## `persistence`

Document persistence only where the source supports it:

```yaml
persistence:
  mode: nonvolatile_via_command
  commit_command: STORE_DEFAULT_ALL
  restore_command: RESTORE_DEFAULT_ALL
```

If persistence is not documented, omit it rather than inferring volatility.

## `timing`

Command-specific timing belongs under `timing`.

## `behavior`

`behavior` captures source-backed product-specific semantics that do not yet justify a common field, such as side effects, retry behavior, hardware-pin dependencies, sensor interpretation, and calibration behavior.

## `source`

`source` preserves command-specific ambiguity or conflicts. Document-wide conflicts belong under document-level `source_conflicts`.

## Validation rules in v0.1

The companion JSON Schema enforces:

1. required core fields;
2. integer command codes from 0 through 255;
3. closed v0.1 enumerations for origin/support/access/roles/transaction/data kind;
4. consistency between access and transaction direction;
5. conditions for `conditional` support;
6. a commit command for `nonvolatile_via_command` persistence;
7. mutual exclusion of `format_ref` and inline `format`;
8. rejection of unknown top-level command fields.

Semantic validation beyond JSON Schema will later check duplicate codes, command references, format references, ranges, cross-command inequalities, and future registry consistency.

## QODN217A0B migration result

The QODN217A0B reference implementation is now migrated to this v0.1 command shape.

The migration normalizes:

- all 48 commands in the datasheet quick-reference inventory;
- command codes as YAML integers authored in hexadecimal;
- support state to `full`, `partial`, or `conditional`;
- access and SMBus transaction direction;
- payload and engineering semantics under `data`;
- defaults under one `default` object;
- cross-command constraints into structured relations where possible;
- persistence only where explicitly documented;
- status reset behavior under `behavior`;
- `READ_TEMPERATURE_1` as canonical identifier with `READ_TEMP1` retained as an alias;
- source conflicts without silently reconciling them.

All 48 migrated command entries validate against `schema/command.schema.json`.
