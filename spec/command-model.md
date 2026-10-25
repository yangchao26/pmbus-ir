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
3. The identifier must match:

```text
^[A-Z][A-Z0-9_]*$
```

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

`origin` identifies whether the command code/name comes from the PMBus command
space or is manufacturer-defined.

Allowed values:

```text
standard
manufacturer_specific
```

Do not encode semantic roles into `origin`. For example, standard MFR identity
commands use:

```yaml
origin: standard
roles: [identification]
```

rather than introducing an origin such as `standard_identification`.

## `support`

`support` describes the completeness of the implementation of the command.

Allowed values:

```text
full
partial
conditional
```

### `full`

All behavior relevant to the device's documented implementation of the command
is supported.

### `partial`

The command is implemented, but only some functions, bits, modes, or response
settings are supported.

A partial command should normally explain the limitation using one or more of:

```yaml
limitations:
constraints:
behavior:
```

### `conditional`

The command exists only under a stated device/variant/state condition.

`conditional` requires `conditions`.

Example:

```yaml
support: conditional
conditions:
  - kind: product_option
    option: -P
```

### Absence is not `unsupported`

A command that is absent from `commands` must **not** automatically be treated
as unsupported unless the source is explicitly a complete supported/unsupported
matrix.

A PMBus IR document records known implemented commands. Missing evidence is not
a negative capability assertion.

## `roles`

`roles` provides semantic classification independent of command origin.

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

Example:

```yaml
roles: [configuration, protection_limit]
```

## `aliases`

`aliases` preserves alternate source names without changing the canonical map
key.

Example:

```yaml
READ_TEMPERATURE_1:
  aliases: [READ_TEMP1]
```

Aliases are names only. They do not create additional commands.

## `access`

Allowed values:

```text
read_only
write_only
read_write
execute
```

`execute` is used for commands whose operation is triggered by the transaction
and which do not transfer a payload, for example:

```yaml
CLEAR_FAULTS:
  access: execute
  transaction:
    write: send_byte
  data:
    kind: none
    bytes: 0
```

Command access and individual bit access are separate concepts.

## `transaction`

`transaction` records SMBus transaction shape independently for read and write.

Possible read values:

```text
read_byte
read_word
read_block
unknown
```

Possible write values:

```text
send_byte
write_byte
write_word
write_block
unknown
```

Examples:

```yaml
# Read-only
transaction:
  read: read_word
```

```yaml
# Read/write
transaction:
  read: read_byte
  write: write_byte
```

```yaml
# Execute
transaction:
  write: send_byte
```

`unknown` is used when the source does not provide enough information or is
internally inconsistent. The reason should also be preserved in `source`,
`notes`, or document-level `source_conflicts`.

Do not use synthetic combined values such as:

```yaml
transaction: read_write_word
```

The read and write operations are separate facts.

## `data`

`data` describes the transferred payload.

Required subfields:

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

### No payload

```yaml
data:
  kind: none
  bytes: 0
```

### Scalar engineering value

```yaml
data:
  kind: scalar
  bytes: 2
  format_ref: vout_linear
  quantity: voltage
  unit: V
  range:
    min: 9.5
    max: 12.5
  resolution: 0.000244140625
```

### Bit field

Bit definitions live under `data.bits`, not as a separate top-level `bits`
field:

```yaml
data:
  kind: bit_field
  bytes: 1
  bits:
    "7":
      name: ON
      access: read_write
      default: 1
    "6":
      name: reserved_or_unsupported
      access: read_only
      default: 0
```

Quote bit keys so YAML parsers treat ranges and numeric positions
consistently.

### String

```yaml
data:
  kind: string
  bytes: 5
  encoding: 8_bit_character
```

### Structured manufacturer data

```yaml
data:
  kind: structured
  bytes: 2
  fields:
    ...
```

## Data format reuse

A command may reference a document-level reusable format:

```yaml
data:
  format_ref: vout_linear
```

or define a command-specific format inline:

```yaml
data:
  format:
    type: linear11
    fixed_exponent: -3
```

A command must not provide both `format_ref` and `format`.

The detailed encoding vocabulary belongs to the PMBus IR Data Model rather
than the Command Model.

## `default`

Defaults use a single structured field.

Scalar example:

```yaml
default:
  value: 12.0
  raw: "0xC000"
```

Raw values are strings because byte width and hexadecimal presentation are
part of the useful representation.

Bit-field example:

```yaml
default:
  raw: "0x88"
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

Do not use magic scalar values such as:

```yaml
default: not_specified
```

## `constraints`

`constraints` contains machine-readable constraints that are not captured by
a simple scalar range.

### Cross-command relation

```yaml
constraints:
  - kind: relation
    operator: gt
    other_command: VOUT_MARGIN_LOW
```

### Relation with an offset

For a requirement such as `VIN_ON >= VIN_OFF + 2 V`:

```yaml
constraints:
  - kind: relation
    operator: ge
    other_command: VIN_OFF
    offset: 2.0
    unit: V
```

v0.1 relation operators are:

```text
gt
ge
lt
le
eq
ne
```

Complex automatic limiting or clamping behavior that cannot be represented by
a simple relation belongs under `behavior`.

Do not store cross-command constraints only as free-form strings when a
structured relation can express them.

## `limitations`

`limitations` explains why a command is only partially implemented.

Example:

```yaml
limitations:
  - Margin Ignore Fault mode is not supported.
```

## `conditions`

`conditions` captures conditions that affect command availability or behavior.

Each condition requires a `kind` and may carry device-specific fields until a
cross-device condition vocabulary is established.

Example:

```yaml
conditions:
  - kind: write_protection_state
    command: MFR_DEVICE_TYPE
    field: WPE
```

## `persistence`

Persistence is explicit and structured.

### Volatile

```yaml
persistence:
  mode: volatile
```

### Nonvolatile through a commit command

```yaml
persistence:
  mode: nonvolatile_via_command
  commit_command: STORE_DEFAULT_ALL
  restore_command: RESTORE_DEFAULT_ALL
```

`commit_command` is required for `nonvolatile_via_command`.

If persistence is not documented, omit `persistence`. Do not infer volatility.

## `timing`

`timing` stores timing that is intrinsic to executing or using the command.

Example:

```yaml
timing:
  execution_time_ms:
    max: 500
  block_further_commands_until_complete: true
```

The internal shape of `timing` remains extensible in v0.1.

## `behavior`

`behavior` stores product-specific command semantics that do not fit a simpler
common field.

Examples include:

- side effects;
- automatic clamping;
- retry behavior;
- dependency on hardware pins;
- sensor interpretation;
- calibration behavior.

The internal shape remains extensible in v0.1. Common patterns should move into
structured fields in later model versions only after multiple reference devices
show that they are reusable.

## `source`

`source` preserves source-specific metadata, ambiguity, or conflicts relevant
to one command.

Example:

```yaml
source:
  conflict: >-
    Detailed description defines a two-byte payload while the quick-reference
    table labels the transfer as Read Byte.
```

Document-wide conflicts belong under the document-level `source_conflicts`.

## `notes`

`notes` is for concise human-readable information that does not yet justify a
new structured semantic field.

It must not be used as a substitute for fields already defined by this model.

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
    range:
      min: 9.5
      max: 12.5
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
    range:
      min: 0
      max: 127.875
    resolution: 0.125
```

### Partial fault-response command

```yaml
VOUT_OV_FAULT_RESPONSE:
  code: 0x41
  origin: standard
  support: partial
  roles: [configuration, protection_response]
  access: read_write
  transaction:
    read: read_byte
    write: write_byte
  data:
    kind: bit_field
    bytes: 1
  default:
    raw: "0xB8"
  limitations:
    - Only shutdown-and-retry response mode is supported.
    - Only no-retry and continuous-retry selections are supported.
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

The companion JSON Schema enforces the structural rules that are stable enough
to validate now.

Important rules include:

1. `code`, `origin`, `support`, `access`, `transaction`, and `data` are required.
2. `code` is an integer from 0 through 255.
3. `origin`, `support`, `access`, transaction names, roles, and `data.kind` use
   closed v0.1 enumerations.
4. `read_only` commands require a read transaction and cannot define a write
   transaction.
5. `write_only` and `execute` commands require a write transaction and cannot
   define a read transaction.
6. `read_write` commands require both read and write transactions.
7. `conditional` support requires `conditions`.
8. `nonvolatile_via_command` persistence requires `commit_command`.
9. `data` may use either `format_ref` or inline `format`, but not both.
10. Command objects reject unknown top-level fields. Device-specific details
    belong under the defined extensibility fields such as `behavior`, `source`,
    `notes`, or structured `conditions`.

## Semantic validation beyond JSON Schema

Some important checks are intentionally left to semantic validation rather than
JSON Schema:

- duplicate command codes in one device document;
- `other_command` references that do not exist;
- `format_ref` references that do not exist;
- persistence commands that do not exist;
- range consistency such as `min <= max`;
- cross-command inequalities;
- command-code/name consistency with a future command registry;
- transaction compatibility with the referenced PMBus standard command;
- variant-condition vocabulary.

These checks should be implemented by `pmbus-ir validate` after the structural
model is stable.

## QODN217A0B migration result

The QODN217A0B reference implementation has been migrated to this v0.1 command
shape. The migration establishes the following normalization rules in practice:

- command codes are YAML integers (decimal or hexadecimal authoring are equivalent);
- legacy support values such as `supported`, `full_read`, and `read_support` are removed;
- synthetic transactions such as `read_write_word` are split into `read` and `write`;
- engineering `value` and payload `data` are merged into one `data` object;
- command defaults are represented only under `default`;
- status bit reset semantics move to `behavior` rather than a custom access enum;
- `READ_TEMPERATURE_1` is the canonical identifier and `READ_TEMP1` is retained as an alias;
- source conflicts remain explicit rather than being normalized away.

The current QODN217A0B reference contains 48 commands from the datasheet quick-reference inventory and each command validates against `schema/command.schema.json`.
