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

`code` is the one-byte command code.

It is stored as a YAML integer and should normally be authored in hexadecimal:

```yaml
code: 0x8B
```

Do not quote command codes:

```yaml
# Do not use
code: "0x8B"
```

The valid range is `0x00` through `0xFF`.

Using a numeric value makes command-code comparison independent of YAML text
formatting.

## `origin`

`origin` identifies the namespace of the command:

```yaml
origin: standard
```

or:

```yaml
origin: manufacturer_specific
```

v0.1 intentionally does not use values such as `standard_identification`.
Identification, telemetry, status, and similar concepts belong in `roles`,
not in `origin`.

## `support`

`support` describes the completeness of the device implementation:

```yaml
support: full
support: partial
support: conditional
```

### `full`

The device implements the command without a product-specific functional
restriction documented by the source.

Read-only commands can still have `support: full`; read-only versus read/write
is represented by `access`.

### `partial`

The command is implemented, but only a subset of its normal functionality is
available.

A partial command should include `limitations`.

Example:

```yaml
support: partial
limitations:
  - soft-off with sequencing is not supported
  - margin-ignore-fault behavior is not supported
```

### `conditional`

The command or part of its behavior is available only under a documented
condition.

A conditional command must include `conditions`.

### Absence is not `unsupported`

A command that is absent from the `commands` map is **not automatically
interpreted as unsupported**.

Absence means only that the IR document does not declare that command.

This distinction is required because a public datasheet may list supported
commands without providing an exhaustive matrix of every unsupported command.

## `roles`

`roles` is an optional semantic classification used by renderers, diff tools,
and validation.

v0.1 roles are:

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

A command may have more than one role.

Example:

```yaml
roles: [status, operation]
```

`roles` does not replace command identity and must not be used to infer PMBus
normative semantics.

## `access`

`access` describes command-level access:

```text
read_only
write_only
read_write
execute
```

### `execute`

Use `execute` for command-only actions with no payload, such as a Send Byte
operation:

```yaml
access: execute
transaction:
  write: send_byte
data:
  kind: none
  bytes: 0
```

Resettable status bits do not create a separate command access type.
For example, a status command remains:

```yaml
access: read_only
```

and its clear/reset behavior belongs under `behavior`.

## `transaction`

`transaction` describes the actual SMBus transfer operation independently for
read and write directions.

Example:

```yaml
transaction:
  read: read_word
  write: write_word
```

v0.1 read transaction values:

```text
read_byte
read_word
read_block
unknown
```

v0.1 write transaction values:

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
support: partial
limitations:
  - margin-ignore-fault behavior is not supported
```

Use `limitations` for implementation coverage, not for operating ranges.

## `conditions`

`conditions` captures state-, option-, or configuration-dependent
availability.

Example:

```yaml
support: conditional
conditions:
  - kind: write_protect_disabled
    via_command: MFR_DEVICE_TYPE
```

Conditions are intentionally extensible in v0.1 because the first reference
device already contains vendor-specific write-protection and variant behavior.

## `persistence`

A writable value is persistent only when the source explicitly establishes
that behavior.

Example:

```yaml
persistence:
  mode: nonvolatile_via_command
  commit_command: STORE_DEFAULT_ALL
  restore_command: RESTORE_DEFAULT_ALL
```

If persistence is not documented, omit `persistence`.

Do not infer persistence from the fact that a command is writable.

## `timing`

Command execution timing belongs under `timing`.

Example:

```yaml
timing:
  execution_time_ms:
    max: 500
  block_further_commands_until_complete: true
```

This keeps timing separate from functional behavior.

## `behavior`

`behavior` contains structured product-specific semantics that do not belong
to the generic wire/data model.

Examples include:

- side effects;
- fault response;
- clear/reset behavior;
- hardware-pin interaction;
- automatic clamping;
- retry behavior;
- command sequencing requirements.

Example:

```yaml
behavior:
  side_effects:
    - clear_supported_status_flags
    - retire_active_smbalert
```

The command model should prefer structured fields inside `behavior`, but v0.1
allows device-specific extensions there when no common representation has yet
been established.

## `source`

`source` is optional provenance for the command entry.

Example:

```yaml
source:
  document: QODN217A0B_PDS
  revision: "3.4"
  pages: [21]
```

A command entry may omit `source` when provenance is already unambiguous at the
document level.

## `notes`

`notes` is the last-resort location for source-supported information that is
important but not yet modeled structurally.

```yaml
notes:
  - Datasheet advises consulting the vendor before changing fault-limit values.
```

Do not use `notes` as a substitute for fields that already exist in the model.

## Complete examples

### Scalar read/write command

```yaml
commands:
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

### Partial bit-field command

```yaml
commands:
  OPERATION:
    code: 0x01
    origin: standard
    support: partial
    roles: [operation]
    access: read_write
    transaction:
      read: read_byte
      write: write_byte
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
    default:
      raw: "0x88"
    limitations:
      - soft-off with sequencing is not supported
      - margin-ignore-fault behavior is not supported
    behavior:
      hardware_enable_required: true
```

### Execute command

```yaml
commands:
  STORE_DEFAULT_ALL:
    code: 0x11
    origin: standard
    support: full
    roles: [persistence]
    access: execute
    transaction:
      write: send_byte
    data:
      kind: none
      bytes: 0
    timing:
      execution_time_ms:
        max: 500
      block_further_commands_until_complete: true
    behavior:
      stores_to: eeprom
```

### Status command

```yaml
commands:
  STATUS_CML:
    code: 0x7E
    origin: standard
    support: partial
    roles: [status]
    access: read_only
    transaction:
      read: read_byte
    data:
      kind: bit_field
      bytes: 1
      bits:
        "7":
          name: INVALID_OR_UNSUPPORTED_COMMAND
          access: read_only
        "6":
          name: INVALID_OR_UNSUPPORTED_DATA
          access: read_only
        "5":
          name: PEC_FAILED
          access: read_only
    limitations:
      - remaining status bits are not supported by this device
    behavior:
      reset_supported: true
      clear_command: CLEAR_FAULTS
```

### Manufacturer-specific structured command

```yaml
commands:
  MFR_DEVICE_TYPE:
    code: 0xD0
    origin: manufacturer_specific
    support: partial
    roles: [identification, manufacturer_control]
    access: read_write
    transaction:
      read: read_word
      write: write_word
    data:
      kind: structured
      bytes: 2
      fields:
        write_protect_enable:
          location: low_byte_bit_1
        module_name:
          location: high_byte_bit_0_and_low_byte_bits_7_2
    default:
      raw: "0x0152"
    behavior:
      controls_manufacturer_write_protect_gate: true
```

## v0.1 semantic validation rules

JSON Schema can validate the local shape of a command entry. Additional
semantic validation is required across the whole document.

A PMBus IR semantic validator should eventually enforce at least:

1. command-map keys follow the canonical identifier syntax;
2. command codes are unique within a device document unless an explicit
   aliasing mechanism is later defined;
3. `read_only` commands provide only a read transaction;
4. `write_only` and `execute` commands provide only a write transaction;
5. `read_write` commands provide both read and write transactions;
6. `conditional` commands declare at least one condition;
7. referenced commands in constraints, persistence, and behavior exist;
8. `format_ref` refers to a declared document-level data format;
9. scalar ranges have `min <= max`;
10. cross-command constraints are internally consistent where they can be
    evaluated.

## QODN217A0B migration decisions

The first reference implementation exposed several ad-hoc patterns that v0.1
removes.

| Current reference pattern | Command Model v0.1 |
| --- | --- |
| `support: supported`, `full_read`, `read_support` | normalize to `full`, `partial`, or `conditional` |
| `transaction: read_write_word` | `transaction.read` + `transaction.write` |
| separate `value:` and `data:` branches | one `data:` branch |
| top-level `bits:` / `supported_bits:` | `data.bits:` |
| `default_raw`, `default_raw_negative_logic`, scalar `default` | structured `default:` |
| free-text cross-command `constraints` | structured relation objects |
| `persistence: store_default_all` | structured `persistence:` object |
| `read_only_resettable` access | `read_only` + reset behavior |
| `supported_functions`, `side_effects`, `default_behavior` | structured `behavior:` |
| `safety_note` | `notes:` |
| `origin: standard_identification` | `origin: standard` + `roles: [identification]` |
| quoted command codes such as `"0x8B"` | numeric YAML code `0x8B` |

The QODN217A0B reference document should be migrated to this model before
`schema/command.schema.json` is wired into the top-level
`schema/pmbus-ir.schema.json`.

## Deliberately deferred from v0.1

The following are not frozen yet:

- a complete common vocabulary for every bit-field meaning;
- a universal expression language for complex dynamic limits;
- full PAGE/PHASE scope semantics;
- a common manufacturer-extension namespace;
- calibration-command modeling;
- confidence scoring;
- source-conflict resolution policy at individual field granularity.

These should be driven by additional real-device references rather than added
speculatively.
