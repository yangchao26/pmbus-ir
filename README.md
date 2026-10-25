# PMBus IR

PMBus IR is an open, vendor-neutral intermediate representation for precisely describing the implemented PMBus interface of a power device.

The project defines a canonical, machine-readable representation that can serve as a single source of truth for PMBus interface requirements and tooling.

## Why PMBus IR?

PMBus specifications define protocol and command semantics, while product datasheets and engineering documents describe product-specific implementations in inconsistent forms. PMBus IR provides a normalized semantic layer between those sources and downstream engineering artifacts.

```text
PMBus specification
Product requirements
Datasheets
Firmware implementation
        |
        v
     PMBus IR
        |
        +--> TRD generation
        +--> Interface documentation
        +--> Validation
        +--> Semantic comparison
        +--> Test generation
        +--> Code generation
```

PMBus IR is not a PMBus communication stack and is not intended to reproduce the PMBus specification. Normative PMBus definitions remain with the official specification. The IR records how a particular device implements its PMBus interface.

## Core concepts

### PMBus IR Specification

The semantic model and rules that define how PMBus interfaces are represented.

### PMBus IR Schema

A machine-readable schema used to validate PMBus IR documents.

### PMBus IR Document

A concrete instance describing the implemented PMBus interface of a specific power device.

Example filename:

```text
example-module.pmbus.yaml
```

## Design principles

1. **Machine-readable first** — YAML/JSON is the source representation; human-readable documents are rendered views.
2. **Vendor-neutral** — the core model must not depend on one manufacturer's datasheet conventions.
3. **Semantic, not tabular** — describe meaning, constraints, state, and behavior rather than only command/register tables.
4. **Loss-minimizing** — the model should preserve enough information to reconstruct the intended interface behavior without hidden assumptions.
5. **Extensible** — manufacturer-specific commands and behaviors must be representable without weakening the common model.
6. **Diffable** — two device interfaces should be comparable semantically rather than by textual YAML differences.

## Initial semantic domains

A PMBus IR document is expected to cover these domains:

- device identity
- referenced standards
- transport and bus capabilities
- addressing, pages, and rails
- commands and transactions
- data representation and engineering units
- telemetry
- configuration and defaults
- status reporting
- faults and warnings
- persistence
- timing and behavior
- manufacturer-specific extensions

## Example

```yaml
ir_version: "0.1"

device:
  manufacturer: Example Power
  model: EXAMPLE-DC-DC
  class: dc_dc_power_module

standards:
  pmbus: "1.5"

transport:
  interface: pmbus
  pec: supported
  max_bus_frequency_khz: 400

addressing:
  pages:
    - id: 0
      name: main_output

commands:
  READ_VOUT:
    code: 0x8B
    supported: true
    access: read_only
    transaction: read_word
    value:
      quantity: voltage
      unit: V
      encoding:
        type: linear16
        exponent_source: VOUT_MODE
    scope:
      pages: [0]
```

This example is illustrative. The v0.1 schema is intentionally incomplete while the semantic model is being established from real device examples.

## Repository structure

```text
pmbus-ir/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── spec/
│   ├── ir-model.md
│   ├── command-model.md
│   ├── data-model.md
│   ├── behavior-model.md
│   └── diff-semantics.md
├── schema/
│   └── pmbus-ir.schema.json
├── examples/
│   ├── minimal.pmbus.yaml
│   └── dc-dc-module.pmbus.yaml
├── tools/
│   └── README.md
└── tests/
    └── README.md
```

## v0.1 scope

The first milestone is intentionally narrow:

- define the PMBus IR concept and boundaries;
- define the first semantic model;
- create an initial JSON Schema;
- build at least one realistic DC/DC reference document;
- define validation behavior;
- define semantic-diff behavior.

A GUI, PMBus master implementation, firmware stack, and device communication layer are out of scope for v0.1.

## Status

Early design / pre-v0.1. The model and schema are expected to change as reference devices are added.

## License

Apache License 2.0. See [LICENSE](LICENSE).
