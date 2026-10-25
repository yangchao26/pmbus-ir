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
```

## Design boundary

The Data Model separates four concepts that are frequently mixed together in
datasheets and hand-written command tables:

1. **transport width** — how many command data bytes are transferred;
2. **numeric representation** — how bits encode a numeric value;
3. **engineering semantics** — quantity, unit, range, accuracy, and device behavior;
4. **device/source resolution** — a source-published measurement or programming resolution that may differ from the mathematical encoding LSB.

A host may need different handling even when two commands represent the same
engineering quantity. Conversely, a device may publish a measurement
resolution that is coarser than the underlying wire encoding.

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

No command data payload:

```yaml
data:
  kind: none
  bytes: 0
```

### `scalar`

A numeric engineering value:

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

A fixed-width collection of individually described bits:

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
  bytes: 5
  encoding: 8_bit_character
```

`bytes` is the command's declared data-byte count. Data IR v0.1 does not infer
whether a vendor table includes an SMBus block count byte unless the source or
the IR explicitly states that convention.

### `structured`

A fixed or block payload whose subfields do not fit the scalar, string, or
single-bit model:

```yaml
data:
  kind: structured
  bytes: 2
  fields:
    major: ...
    minor: ...
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

A document-level LINEAR11 descriptor may omit `fixed_exponent` when the source
only establishes the generic representation and does not publish a single
fixed exponent shared by all referencing commands.

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
```

The format type carries these representation semantics:

- command data width: 16 bits / 2 bytes;
- mantissa: unsigned 16-bit value;
- exponent: supplied separately rather than stored in the 16-bit command data word.

When the implemented device fixes that exponent, `fixed_exponent` records the
actual implemented value. `exponent_source` records the command that exposes
or controls the exponent when the source material identifies one.

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

This distinction is necessary for the QODN217A0B reference implementation:
its `READ_IOUT` representation records `fixed_exponent: -3`, whose encoding
LSB is `0.125 A`, while the public datasheet-derived reference information
also records a published current resolution of `0.146 A`. PMBus IR preserves
both facts rather than rewriting one to match the other.

The earlier experimental field:

```yaml
resolution:
```

is considered ambiguous. Semantic Validation v0.1 emits a warning when that
field materially differs from a fixed-exponent encoding LSB. New documents
should use `encoding_resolution` or `published_resolution` explicitly.

## Programming step

`step` represents a permitted programming increment rather than the numeric
encoding itself:

```yaml
step: 0.125
```

When a fixed exponent is known, Semantic Validation v0.1 requires `step` to be
an integer multiple of the encoding LSB.

## Payload-width compatibility

When a reusable format declares:

```yaml
wire_bytes: 2
```

and a command references it, the command must declare a matching `data.bytes`.

The same rule is implied for known v0.1 numeric format types:

```text
linear11   -> 2 bytes
vout_linear -> 2 bytes
```

This catches interfaces that use the correct semantic format name but an
incompatible SMBus data width.

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

For example, bit `8` is invalid when `bytes: 1`.

## String and block length

Data IR v0.1 requires:

- string data to declare a positive `bytes` count;
- string data to declare an `encoding`;
- string commands to use `read_block` or `write_block` transaction semantics;
- all block transactions to declare a positive data-byte count;
- a literal default string not to exceed the declared byte count.

The validator deliberately does not infer vendor-specific padding, terminator,
or block-count-byte conventions that are not explicitly represented in the IR.

## Validation versus PMBus normative semantics

The Data IR validator checks that the **document is internally consistent**.
It does not attempt to prove that a command follows every normative rule in
the PMBus specification, and it does not embed a copied command-definition
database.

For example, the validator can determine that a LINEAR11 command declares one
byte when its selected representation requires two. It does not infer that an
unlisted device command is unsupported or replace source-specific behavior
with normative PMBus defaults.
