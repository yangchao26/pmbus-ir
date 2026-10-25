# Semantic Diff

PMBus IR comparison is intended to compare interface meaning rather than YAML text.

A semantic diff should be able to identify differences such as:

- command supported on only one device;
- same command but different access rights;
- different transaction types;
- different numeric encoding;
- different units or scaling;
- different valid ranges;
- different page/rail applicability;
- different defaults;
- different accuracy or resolution;
- different persistence;
- different fault behavior;
- manufacturer-specific functionality.

A future diff engine may classify differences by impact, for example:

- documentation-only difference;
- host-software handling difference;
- configuration incompatibility;
- telemetry incompatibility;
- behavior incompatibility.

Compatibility classification is not yet normative in v0.1.
