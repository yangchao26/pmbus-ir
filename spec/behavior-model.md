# Behavior Model

A complete PMBus interface cannot always be described by a static command table.

The behavior model is intended to capture product-specific semantics such as:

- command dependencies;
- side effects;
- sequencing constraints;
- state-dependent access;
- fault and warning responses;
- clear/reset behavior;
- STORE/RESTORE behavior;
- volatile versus non-volatile configuration;
- telemetry update periods;
- command response latency;
- startup and shutdown interactions;
- PAGE/PHASE effects;
- WRITE_PROTECT behavior.

The first version should keep behavior representation structured where common patterns exist and allow explicit extensions where the common model is insufficient.
