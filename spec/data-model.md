# Data Model

The data model represents the meaning and encoding of values transferred through PMBus commands.

Initial concepts include:

- scalar, bit field, enumeration, string, block, and structured values;
- PMBus numeric encodings such as Linear and Direct where applicable;
- engineering quantity;
- engineering unit;
- scaling and exponent source;
- valid range;
- resolution;
- accuracy;
- sentinel/reserved values;
- enumerated meanings;
- bit-level meanings.

The IR should distinguish transport encoding from engineering semantics. Two devices may implement the same logical quantity using different encodings and therefore require different host handling.
