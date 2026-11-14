# PMBus IR Document Model v0.1

## Purpose and boundary

A PMBus IR Document describes the **PMBus interface actually implemented by one device or device family variant**. It is the normalized, source-traceable layer between engineering evidence (datasheets, requirements, firmware and tests) and generated TRDs, command tables, validation reports, compatibility comparisons, and integration tests.

PMBus IR is **not** a PMBus controller, firmware stack, universal register map, or substitute for the normative PMBus specification. It does not imply that commands missing from a published quick-reference list are necessarily unsupported.

## Canonical format

**YAML is the sole canonical PMBus IR document format. JSON is not a supported PMBus IR document format.**

Name device instances `<device>.pmbus.yaml`. JSON Schema files are validation artifacts, not alternative device document formats.

Use unambiguous plain YAML mappings, sequences, scalars, and integer command codes (hexadecimal YAML integer notation is recommended). Avoid custom tags, merge keys, aliases, and source-layout-dependent structures.

## Source-driven reference implementations

The first two source-based references are:

| Instance | Product | Command inventory | Notable evidence |
| --- | --- | ---: | --- |
| `examples/reference/qodn217a0b.pmbus.yaml` | QODN217A0B, non-isolated Osprey | 48 | PMBus revision statements differ; one-address-resistor selection; vendor block strings |
| `examples/reference/ebdw025a0b.pmbus.yaml` | EBDW025A0B, isolated Barracuda | 50 | PMBus Rev. 1.2; ADDR0/ADDR1 octal address; configurable pins, calibration commands, read-only IOUT limit conflict |

Command counts refer to **published supported-command quick-reference inventories**, not a complete support/unsupported matrix across the PMBus standard.

Each reference contains a `document.completeness` declaration; the semantic validator checks `supported_command_count` against the actual number of command entries. An IR author must preserve unresolved contradictions under `source_conflicts`, with provenance in `source` or command-level `source`. Do not invent codes, format details, defaults, or firmware behavior where the source is silent.

## Root domains and semantic ownership

```yaml
ir_version: "0.1"
document: {}
source: {}
device: {}
standards: {}
transport: {}
addressing: {}
data_formats: {}
commands: {}
telemetry: {}
configuration: {}
status: {}
faults: {}
persistence: {}
behavior: {}
extensions: {}
source_conflicts: {}
```

| Domain | Responsibility |
| --- | --- |
| `ir_version` | Version of the IR representation, distinct from the device PMBus revision |
| `document` | Reference status, completeness/coverage claim, and editorial maturity |
| `source` | Datasheet/engineering evidence, revision, source basis, page references, and interpretation policy |
| `device` | Product identity, family, topology, electrical envelope, and variant scope |
| `standards` | Claimed protocol versions and source-based compliance/revision statements; may be a structured object if sources conflict |
| `transport` | Shared SMBus/PMBus framing, PEC, clock timing, SMBALERT/ARA and bus-level behavior |
| `addressing` | Address programming, reserved addresses, logical outputs and page-model evidence |
| `data_formats` | Reusable descriptions of device-level wire encodings and scale parameters |
| `commands` | **Authoritative command-specific interface representation**: code, access, transaction, support, data, defaults, conditions and effects |
| `telemetry`, `configuration`, `status`, `faults` | Semantic **views and relationships** referencing command IDs; do not duplicate independent command definitions |
| `persistence` | Device-level NVM strategy, commit/restore semantics; per-command applicability remains with the command |
| `behavior` | Device-level cross-command and pin-dependent behavior not owned by one command |
| `extensions` | Clearly delimited, source-backed device-specific details not yet standardized as core IR semantics |
| `source_conflicts` | Unresolved contradictory evidence; no silent reconciliation or promotion to a normative fact |

Only `ir_version` and `device.manufacturer` / `device.model` are globally mandatory for minimal documents in the current root schema. A document declaring `document.kind: reference_implementation` must also provide `source` and `commands`. Other domains are optional because source coverage varies by device. Requiredness should increase only when supported by multiple real references.

## Command identity and references

`commands` is a map keyed by canonical uppercase identifiers, for example `READ_VOUT` or `MFR_C1_C2_ARA_CONFIG`. Standard command names are used where known; manufacturer-specific names follow the published device naming. A source spelling variant is not an independently supported command without its own code.

Command codes are one-byte YAML integers. Two canonical command entries in the same document must not share a code. Aliases must not collide with other command names. References such as `exponent_source`, `commit_command`, `restore_command`, `other_command`, or `*_command` must resolve to documented commands, subject to explicitly delimited source-only areas.

`extensions` and `source_conflicts` may mention undocumented names **without** implying that those names exist in the implemented command map.

## Data and transport boundaries

A command's `data.bytes` is the number of **semantic content bytes**, independent of SMBus transaction framing.

```yaml
data:
  kind: string
  bytes: 12
  encoding: "8_bit_character"
  block:
    content_bytes: 12
    count_prefix_bytes: 1
    transaction_payload_bytes: 13
```

The block payload includes its one-byte SMBus count prefix but excludes address, command, ACK/NACK and PEC. Use `encoding_resolution` for mathematical encoding LSB and `published_resolution` for a source-stated device or measurement resolution. The detailed numeric model is in `spec/data-model.md`.

`transaction.read` and `transaction.write` represent on-wire operation separately from `access`. Mark unsupported/unknown directions accurately rather than fabricating a compatible transaction.

## Source conflicts and implementation decisions

A reference may need to pick a practical representation for validation while keeping unresolved source contradictions visible. For example:

- The EBDW025A0B feature narrative describes adjustable IOUT overcurrent limits, but its detailed command descriptions and quick-reference rows specify read-only transfers. The Reference IR models the latter as the published transfer and preserves the conflict.
- EBDW025A0B firmware revision uses two-byte packed BCD in detail while the quick-reference table says Read byte. Its read transaction remains `unknown` pending verification.
- QODN217A0B and EBDW025A0B report different addressing methods and different manufacturer command inventories. Do not normalize these away.

No formal PMBus compliance determination follows from a passing IR validation.

## Validation layers

1. YAML parser: valid, unambiguous canonical document syntax.
2. Root/command/data-format JSON Schemas: documented types, required fields, enums, and local shape constraints.
3. Semantic validator: uniqueness, references, declared command count, range/default/constraint consistency, numeric encoding, and block length invariants.
4. Source review: source-to-IR traceability and any unresolved device ambiguities. This step remains human-reviewed in v0.1.

The supported CLI is `pmbus-ir validate <document>`. Warning-free structural/semantic validation means **internal consistency**, not independently verified firmware behavior.

## Deferred v0.1 topics

Multi-rail PAGE/PHASE scope, variant-conditional default evaluation, host compatibility severity, dynamic protection limits, state-machine proofs, on-device command testing, and Semantic Diff are future work. These should be developed from additional real-device references instead of being inferred from one product.
