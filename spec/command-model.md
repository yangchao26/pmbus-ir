# Command Model

A command entry describes how a specific device implements a PMBus command.

The command model should distinguish at least:

- command identity and code;
- standard versus manufacturer-specific origin;
- support state;
- access semantics;
- SMBus transaction type;
- data representation;
- engineering quantity and unit;
- page/rail/phase scope;
- writable or readable ranges;
- default/reset values where applicable;
- accuracy or resolution where applicable;
- timing constraints;
- dependencies and side effects;
- persistence behavior.

Illustrative form:

```yaml
commands:
  READ_VOUT:
    code: 0x8B
    supported: true
    origin: standard
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

The schema should not assume that command code alone is sufficient to describe compatibility.
