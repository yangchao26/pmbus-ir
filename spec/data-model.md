# Data IR Model v0.1

## Status

This document defines the first concrete **PMBus IR Data Model v0.1**.

The model is driven by the QODN217A0B reference implementation and focuses on
the data representations needed by the first real PMBus IR document. It does
not attempt to reproduce the normative PMBus specification.

The companion machine-readable format schema is:

```text
schema/data-format.schema.json
```

Semantic checks are implemented in:

```text
tools/semantic_validator.py
tools/data_semantics.py
```

## Design boundary

The Data Model separates five concepts that are frequently mixed together in
datasheets and hand-written command tables:

1. **content width** — how many bytes belong to the semantic command value;
2. **transport framing** — transaction-specific bytes such as an SMBus block count prefix;
3. **numeric representation** — how bits encode a numeric value;
4. **engineering semantics** — quantity, unit, range, accuracy, and device behavior;
5. **source-published resolution** — a device/measurement resolution stated by a source and not necessarily equal to the mathematical encoding LSB.

A host may need different handling even when two commands represent the same
engineering quantity. Conversely, a device may publish a measurement
resolution that is coarser than the underlying wire encoding.

## Canonical meaning of `data.bytes`

`data.bytes` always means **semantic content bytes**.

It excludes protocol framing and transport metadata, including:

- SMBus block count prefix;
- PEC;
- slave address;
- command code;
- ACK/NACK signaling.

This rule is independent of transaction type. A one-byte command, a word
command, and a block command therefore use `data.bytes` with the same semantic
meaning.

## Data kinds

Command `data.kind` values in v0.1 are:

```text
none
scalar
bit_field
string
structured
```

### `none`

```yaml
data:
  kind: none
  bytes: 0
```

### `scalar`

```yaml
data:
  kind: scalar
  bytes: 2
  format:
    type: linear11
    fixed_exponent: -3
  quantity: voltage
  unit: V
  encoding_resolution: 0.125
```

### `bit_field`

```yaml
data:
  kind: bit_field
  bytes: 1
  bits:
    "7":
      name: FAULT
```

In v0.1 each `bits` key identifies one bit position. Multi-bit structures
should use `structured` until an explicit bit-range model is defined.

### `string`

Character data transferred with block transaction semantics:

```yaml
data:
  kind: string
  bytes: 4
  encoding: 8_bit_character
  block:
    content_bytes: 4
    count_prefix_bytes: 1
    transaction_payload_bytes: 5
```

Here `bytes: 4` and `content_bytes: 4` describe the four characters. The
transaction payload contains one additional SMBus block count byte.

### `structured`

A fixed or block payload whose subfields do not fit the scalar, string, or
single-bit model:

```yaml
data:
  kind: structured
  bytes: 12
  block:
    content_bytes: 12
    count_prefix_bytes: 1
    transaction_payload_bytes: 13
```

## Reusable and inline formats

A command may reference a reusable document-level format:

```yaml
data_formats:
  vout_linear:
    type: vout_linear
    wire_bytes: 2
    fixed_exponent: -12
    exponent_source: VOUT_MODE
    encoding_resolution: 0.000244140625

commands:
  READ_VOUT:
    data:
      kind: scalar
      bytes: 2
      format_ref: vout_linear
```

or define command-local encoding information:

```yaml
data:
  kind: scalar
  bytes: 2
  format:
    type: linear11
    fixed_exponent: -3
```

A command must not provide both `format_ref` and `format`.

## LINEAR11

PMBus IR represents LINEAR11 with:

```yaml
format:
  type: linear11
```

The format type carries the representation semantics used by the validator:

- total wire width: 16 bits / 2 bytes;
- mantissa: signed 11-bit two's-complement value;
- exponent: signed 5-bit two's-complement value stored in the same word.

A device implementation may use a fixed exponent for a particular command:

```yaml
format:
  type: linear11
  fixed_exponent: -3
```

When `fixed_exponent` is declared it must fit the signed 5-bit range:

```text
-16 <= fixed_exponent <= 15
```

The mathematical encoding LSB is:

```text
encoding_lsb = 2 ^ fixed_exponent
```

For example, `fixed_exponent: -3` gives an encoding LSB of `0.125` engineering
units.

## VOUT Linear

PMBus IR uses `vout_linear` for the VOUT-style linear representation used by
the QODN217A0B reference implementation:

```yaml
data_formats:
  vout_linear:
    type: vout_linear
    wire_bytes: 2
    fixed_exponent: -12
    exponent_source: VOUT_MODE
    encoding_resolution: 0.000244140625
```

The format type carries these representation semantics:

- command data width: 16 bits / 2 bytes;
- mantissa: unsigned 16-bit value;
- exponent: supplied separately rather than stored in the 16-bit command data word.

## Encoding resolution versus published resolution

These are deliberately separate fields.

### `encoding_resolution`

The mathematical LSB implied by the numeric encoding:

```yaml
encoding_resolution: 0.125
```

If a fixed exponent is available, the semantic validator requires:

```text
encoding_resolution == 2 ^ fixed_exponent
```

### `published_resolution`

A device or measurement resolution stated by a source document:

```yaml
published_resolution: 0.146
```

It is not required to equal the encoding LSB.

For QODN217A0B `READ_IOUT`, the fixed LINEAR11 exponent is `-3`, so the
encoding LSB is `0.125 A`, while the datasheet publishes a measurement
resolution of `0.146 A`. The reference IR records both values explicitly.

The earlier experimental command field:

```yaml
resolution:
```

and the earlier reusable-format field:

```yaml
resolution_v:
```

are legacy fields. New/reference documents should use the explicit canonical
fields. The validator reports legacy use as a warning.

## Programming step

`step` represents a permitted programming increment rather than the numeric
encoding itself:

```yaml
step: 0.125
```

When a fixed exponent is known, Semantic Validation v0.1 requires `step` to be
an integer multiple of the encoding LSB.

## Payload-width compatibility

When a reusable numeric format declares:

```yaml
wire_bytes: 2
```

and a command references it, the command must declare a matching `data.bytes`.

Known v0.1 numeric representations imply:

```text
linear11    -> 2 content bytes
vout_linear -> 2 content bytes
```

## Bit-field width

For:

```yaml
data:
  kind: bit_field
  bytes: N
```

valid bit positions are:

```text
0 .. (8 * N - 1)
```

## SMBus block length model

Block commands must explicitly represent three lengths:

```yaml
block:
  content_bytes: N
  count_prefix_bytes: 1
  transaction_payload_bytes: N + 1
```

The invariants are:

```text
data.bytes == block.content_bytes
block.count_prefix_bytes == 1
block.transaction_payload_bytes == block.content_bytes + block.count_prefix_bytes
```

`transaction_payload_bytes` deliberately excludes PEC and all address/command/
ACK framing.

This makes a vendor table's byte-count convention explicit instead of forcing
tools to guess whether a displayed "Data Bytes" value includes the SMBus block
count byte.

### QODN217A0B interpretation

The QODN217A0B quick-reference table lists `MFR_ID` as 5 data bytes while its
published default value is the four-character string `OMPW`. The reference IR
therefore records four semantic content bytes plus one count-prefix byte, and
applies the same table-counting convention to the adjacent standard MFR block
string rows.

`MFR_MOD_DATE_LOC_SN` is intentionally different: its detailed command text
states read support for a 12-byte block, while the quick-reference table also
shows `DATA BYTES = 12`. Because the standard MFR rows suggest that the table
count includes the count prefix, those two source statements create an
ambiguity. The reference IR treats the detailed 12-byte statement as the
semantic content length and preserves the table ambiguity under
`source_conflicts` rather than silently reducing it to 11 bytes.

## String and block validation

Data IR v0.1 requires:

- string data to declare a positive content length;
- string data to declare an `encoding`;
- string commands to use `read_block` or `write_block` transaction semantics;
- every block transaction to provide `data.block` metadata;
- `data.bytes` to equal `block.content_bytes`;
- one count-prefix byte;
- `transaction_payload_bytes = content_bytes + 1`;
- block metadata not to appear on non-block transactions;
- a literal default string not to exceed `content_bytes`.

## Validation versus PMBus normative semantics

The Data IR validator checks that the **document is internally consistent**.
It does not attempt to reproduce the PMBus command-definition database or to
infer undocumented vendor framing conventions. When a source's length
convention is ambiguous, the IR records the interpretation and preserves the
conflict explicitly.
