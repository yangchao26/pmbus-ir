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

`document` and `source` provide provenance for reference implementations. `data_formats` allows reusable device-level encoding definitions, while `source_conflicts` preserves contradictions in source material instead of silently normalizing them away.

Not every domain must be populated by every device. Required and optional fields will be frozen only after reference implementations expose enough real-world variation.

## Canonical representation

PMBus IR uses YAML as its sole canonical document format. JSON is not a supported PMBus IR document format.

The IR should avoid encoding the layout of a specific vendor datasheet. Information should instead be grouped by semantic meaning.

## Normative direction

The long-term target is for a PMBus IR document to be the authoritative source for the implemented interface, with TRDs, command tables, test specifications, and other views generated from it where practical.
