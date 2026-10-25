# Tools

Tooling will be added after the IR model has enough stability.

Initial planned commands:

```text
pmbus-ir validate <document>
pmbus-ir diff <document-a> <document-b>
pmbus-ir render <document>
```

The tools must consume the IR rather than embed device-specific knowledge outside the IR model.
