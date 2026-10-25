# Command IR Model v0.1

## Status

This document defines the **PMBus IR Command Model v0.1**.

The model was derived from the first full reference implementation,
`examples/reference/qodn217a0b.pmbus.yaml`, rather than from an abstract command table.

The v0.1 goal is to freeze the common shape of a command entry while leaving
device-specific behavior extensible.

The companion machine-readable schema is:

```text
schema/command.schema.json
```

## Scope

A command entry describes **how one device implements one PMBus command**.

The command model captures:

- command identity and code;
- standard versus manufacturer-specific origin;
- implementation completeness;
- read/write/execute access;
- SMBus transaction shape;
- transferred data shape and engineering semantics;
- defaults;
- range and cross-command constraints;
- persistence;
- timing;
- conditions, side effects, and device-specific behavior;
- optional source/provenance notes.

The command model does **not** reproduce the normative definition of a PMBus
command. Standard command semantics remain defined by the PMBus specification.

## Command map

Commands are stored in a map keyed by a canonical command identifier:

```yaml
commands:
  READ_VOUT:
    ...
  MFR_DEVICE_TYPE:
    ...
```

### Command identifier

The map key is the canonical command identifier.

Rules:

1. Use the standard PMBus command name when the command is standard.
2. Use the vendor-published command name for manufacturer-specific commands,
   normalized to uppercase ASCII with `_` separators.
3. The identifier must match `^[A-Z][A-Z0-9_]*$`.
4. A vendor spelling or abbreviation may be preserved with `aliases`.
5. Do not duplicate the identifier inside the command object.

Example:

```yaml
READ_TEMPERATURE_1:
  aliases: [READ_TEMP1]
  ...
```

## Required fields

Every v0.1 command entry has these required fields:

```yaml
code:
origin:
support:
access:
transaction:
data:
```

The top-level command shape is:

```yaml
COMMAND_ID:
  code: 0x00
  origin: standard
  support: full
  roles: []
  aliases: []
  access: read_only
  transaction: {}
  data: {}
  default: {}
  constraints: []
  limitations: []
  conditions: []
  persistence: {}
  timing: {}
  behavior: {}
  source: {}
  notes: []
```

Only the six core fields are required. The remaining fields are present when
they carry device-specific meaning.

## `code`

`code` is the one-byte command code and is represented as a YAML integer.
Hexadecimal authoring is recommended because it matches PMBus documentation:

```yaml
code: 0x8B
```

Decimal integer authoring is semantically equivalent and remains valid:

```yaml
code: 139
```

Both forms parse to the same integer value and must compare identically in semantic diff.
Quoted strings such as `"0x8B"` are not valid command-code values in v0.1.

## `origin`

Allowed values:

```text
standard
manufacturer_specific
```

Semantic classification belongs in `roles`, not `origin`.

## `support`

Allowed values:

```text
full
partial
conditional
```

`partial` means only some functions, bits, modes, or response settings are implemented.
`conditional` requires `conditions`.

A command absent from `commands` must not automatically be interpreted as unsupported unless the source explicitly provides a complete supported/unsupported matrix.

## `roles`

v0.1 values:

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

## `aliases`

`aliases` preserves alternate source names without creating a second command.

Example:

```yaml
READ_TEMPERATURE_1:
  aliases: [READ_TEMP1]
```

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

Read and write are represented separately:

```yaml
transaction:
  read: read_word
  write: write_word
```

Do not use synthetic combined values such as `read_write_word`.
Use `unknown` when the source is incomplete or internally inconsistent and preserve the reason in `source`, `notes`, or document-level `source_conflicts`.

## `data`

`data` describes the transferred payload and always contains:

```yaml
data:
  kind:
  bytes:
```

v0.1 `kind` values:

```text
none
scalar
bit_field
string
structured
```

### Scalar engineering value

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

### Bit field

Bit definitions live under `data.bits`:

```yaml
data:
  kind: bit_field
  bytes: 1
  bits:
    "7":
      name: ON
      access: read_write
      default: 1
```

Quote bit keys so YAML parsers treat bit positions consistently.

### String

```yaml
data:
  kind: string
  bytes: 5
  encoding: 8_bit_character
```

### Structured data

```yaml
data:
  kind: structured
  bytes: 2
  fields:
    ...
```

## Data format reuse

Use either a reusable document-level format:

```yaml
data:
  format_ref: vout_linear
```

or a command-specific inline format:

```yaml
data:
  format:
    type: linear11
    fixed_exponent: -3
```

A command must not provide both.

## `default`

Defaults use one structured field:

```yaml
default:
  value: 12.0
  raw: "0xC000"
```

Variant-dependent defaults use `cases`:

```yaml
default:
  cases:
    - when:
        option_any: ["-A", "-P"]
      value: 1.7
    - when:
        option_none: ["-A", "-P"]
      value: 0
```

If the source does not define a default, omit `default`.

## `constraints`

Cross-command relationships use machine-readable constraints:

```yaml
constraints:
  - kind: relation
    operator: ge
    other_command: VIN_OFF
    offset: 2.0
    unit: V
```

v0.1 relation operators are `gt`, `ge`, `lt`, `le`, `eq`, and `ne`.
Complex automatic clamping may use `dynamic_limit`; restricted enumerations may use `allowed_values`.

## `limitations`

Use `limitations` to explain why a command is partial.

## `conditions`

Conditions affect availability or behavior. Each condition requires `kind` and remains extensible in v0.1.

## `persistence`

Document persistence only when the source supports it.

```yaml
persistence:
  mode: nonvolatile_via_command
  commit_command: STORE_DEFAULT_ALL
  restore_command: RESTORE_DEFAULT_ALL
```

If persistence is not documented, omit it rather than inferring volatility.

## `timing`

Command-specific timing stays under `timing`, for example:

```yaml
timing:
  execution_time_ms:
    max: 500
  block_further_commands_until_complete: true
```

## `behavior`

`behavior` captures product-specific semantics that do not yet justify a common field, such as side effects, retry behavior, hardware-pin dependencies, sensor interpretation, or calibration behavior.

## `source`

`source` preserves command-specific ambiguity or conflicts. Document-wide conflicts belong under `source_conflicts`.

## `notes`

`notes` is for concise human-readable information that does not yet justify a structured field. It must not replace an existing structured field.

## Canonical examples

### Scalar configuration command

```yaml
VOUT_COMMAND:
  code: 0x21
  origin: standard
  support: full
  roles: [configuration]
  access: read_write
  transaction:
    read: read_word
    write: write_word
  data:
    kind: scalar
    bytes: 2
    format_ref: vout_linear
    quantity: voltage
    unit: V
    range: {min: 9.5, max: 12.5}
    resolution: 0.000244140625
  default:
    value: 12.0
    raw: "0xC000"
  persistence:
    mode: nonvolatile_via_command
    commit_command: STORE_DEFAULT_ALL
    restore_command: RESTORE_DEFAULT_ALL
```

### Telemetry command

```yaml
READ_VIN:
  code: 0x88
  origin: standard
  support: full
  roles: [telemetry]
  access: read_only
  transaction:
    read: read_word
  data:
    kind: scalar
    bytes: 2
    format:
      type: linear11
      fixed_exponent: -3
    quantity: voltage
    unit: V
    range: {min: 0, max: 127.875}
    resolution: 0.125
```

### Manufacturer-specific structured command

```yaml
MFR_DEVICE_TYPE:
  code: 0xD0
  origin: manufacturer_specific
  support: partial
  roles: [manufacturer_control, identification]
  access: read_write
  transaction:
    read: read_word
    write: write_word
  data:
    kind: structured
    bytes: 2
    fields:
      ...
```

## Validation rules in v0.1

The companion JSON Schema enforces:

1. `code`, `origin`, `support`, `access`, `transaction`, and `data` are required.
2. `code` is an integer from 0 through 255.
3. core enumerations are closed in v0.1.
4. access and transaction direction must agree.
5. `conditional` support requires `conditions`.
6. `nonvolatile_via_command` persistence requires `commit_command`.
7. `data` may use either `format_ref` or inline `format`, but not both.
8. unknown top-level command fields are rejected.

Semantic validation beyond JSON Schema will later check duplicate codes, command references, format references, ranges, cross-command inequalities, and registry consistency.

## QODN217A0B migration result

The QODN217A0B reference implementation has been migrated to this v0.1 command shape.

The migration normalizes:

- all 48 commands in the datasheet quick-reference inventory;
- support state to `full`, `partial`, or `conditional`;
- command access and SMBus read/write transaction direction;
- payload and engineering-value semantics under `data`;
- defaults under one `default` object;
- cross-command constraints into structured relations where possible;
- persistence only where explicitly documented;
- status reset behavior under `behavior`;
- `READ_TEMPERATURE_1` as the canonical identifier with `READ_TEMP1` retained as an alias;
- documented source conflicts without silently reconciling them.

All 48 migrated command entries validate against `schema/command.schema.json`.
