# PMBus IR Model

## Purpose

PMBus IR is a canonical intermediate representation of the PMBus interface implemented by a specific device.

It sits between heterogeneous engineering sources and downstream artifacts:

```text
requirements / datasheet / firmware / test knowledge
                        |
                        v
                     PMBus IR
                        |
        +---------------+----------------+
        |               |                |
        v               v                v
       TRD          validation      semantic diff
```

The IR is intended to normalize product-specific PMBus semantics without copying the normative PMBus specification.

## Non-goals

PMBus IR is not:

- a PMBus protocol implementation;
- a replacement for the PMBus specification;
- a firmware driver library;
- a generic register-map format;
- a textual copy of a datasheet command table.

## Top-level domains

The initial model uses the following top-level domains:

```yaml
ir_version: "0.1"
device: {}
standards: {}
transport: {}
addressing: {}
commands: {}
telemetry: {}
configuration: {}
status: {}
faults: {}
persistence: {}
behavior: {}
extensions: {}
```

Not every domain must be populated by every device. Required and optional fields will be frozen only after reference implementations expose enough real-world variation.

## Canonical representation

YAML is the preferred authoring form for readability. JSON is an equivalent machine representation.

The IR should avoid encoding the layout of a specific vendor datasheet. Information should instead be grouped by semantic meaning.

## Normative direction

The long-term target is for a PMBus IR document to be the authoritative source for the implemented interface, with TRDs, command tables, test specifications, and other views generated from it where practical.
