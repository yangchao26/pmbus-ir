from __future__ import annotations

from math import isclose
from typing import Any, Mapping

from semantic_validator import ValidationIssue


def _path(*parts: object) -> str:
    out = "$"
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        elif isinstance(part, str) and part:
            if part.replace("_", "").isalnum() and not part[0].isdigit():
                out += f".{part}"
            else:
                out += f"[{part!r}]"
    return out


def _fixed_exponent(descriptor: Mapping[str, Any]) -> int | None:
    value = descriptor.get("fixed_exponent")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    exponent = descriptor.get("exponent")
    if isinstance(exponent, Mapping):
        value = exponent.get("fixed")
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _resolved_format(
    data: Mapping[str, Any], data_formats: Mapping[str, Any]
) -> Mapping[str, Any] | None:
    inline = data.get("format")
    if isinstance(inline, Mapping):
        return inline
    format_ref = data.get("format_ref")
    if isinstance(format_ref, str):
        value = data_formats.get(format_ref)
        if isinstance(value, Mapping):
            return value
    return None


def validate_data_model_semantics(
    document: Mapping[str, Any],
) -> list[ValidationIssue]:
    """Validate canonical Data IR v0.1 fields and block-length semantics.

    `data.bytes` always means semantic content bytes. For SMBus block
    transactions, the one-byte count prefix and any PEC/framing bytes are not
    included in `data.bytes`.
    """

    issues: list[ValidationIssue] = []
    commands_raw = document.get("commands", {})
    data_formats_raw = document.get("data_formats", {})
    commands = commands_raw if isinstance(commands_raw, Mapping) else {}
    data_formats = data_formats_raw if isinstance(data_formats_raw, Mapping) else {}

    for format_id, descriptor in data_formats.items():
        if not isinstance(descriptor, Mapping):
            continue
        legacy = descriptor.get("resolution_v")
        if isinstance(legacy, (int, float)) and not isinstance(legacy, bool):
            issues.append(
                ValidationIssue(
                    "legacy_resolution_field",
                    _path("data_formats", format_id, "resolution_v"),
                    "resolution_v is a legacy experimental field; use encoding_resolution.",
                    severity="warning",
                )
            )
        fixed = _fixed_exponent(descriptor)
        encoding_resolution = descriptor.get("encoding_resolution")
        if (
            fixed is not None
            and isinstance(encoding_resolution, (int, float))
            and not isinstance(encoding_resolution, bool)
        ):
            expected = 2.0**fixed
            if not isclose(
                float(encoding_resolution), expected, rel_tol=1e-9, abs_tol=1e-12
            ):
                issues.append(
                    ValidationIssue(
                        "encoding_resolution_mismatch",
                        _path("data_formats", format_id, "encoding_resolution"),
                        f"encoding_resolution {encoding_resolution} does not equal 2^{fixed} = {expected}.",
                    )
                )

    for command_id, command in commands.items():
        if not isinstance(command, Mapping):
            continue
        data = command.get("data")
        transaction = command.get("transaction")
        if not isinstance(data, Mapping):
            continue
        if not isinstance(transaction, Mapping):
            transaction = {}

        base_path = _path("commands", command_id, "data")
        byte_count = data.get("bytes")
        legacy = data.get("resolution")
        if isinstance(legacy, (int, float)) and not isinstance(legacy, bool):
            issues.append(
                ValidationIssue(
                    "legacy_resolution_field",
                    base_path + ".resolution",
                    "resolution is ambiguous; use encoding_resolution and/or published_resolution.",
                    severity="warning",
                )
            )

        descriptor = _resolved_format(data, data_formats)
        if descriptor is not None:
            fixed = _fixed_exponent(descriptor)
            encoding_resolution = data.get("encoding_resolution")
            if (
                fixed is not None
                and isinstance(encoding_resolution, (int, float))
                and not isinstance(encoding_resolution, bool)
            ):
                expected = 2.0**fixed
                if not isclose(
                    float(encoding_resolution), expected, rel_tol=1e-9, abs_tol=1e-12
                ):
                    issues.append(
                        ValidationIssue(
                            "encoding_resolution_mismatch",
                            base_path + ".encoding_resolution",
                            f"encoding_resolution {encoding_resolution} does not equal 2^{fixed} = {expected}.",
                        )
                    )

        is_block = (
            transaction.get("read") == "read_block"
            or transaction.get("write") == "write_block"
        )
        block = data.get("block")

        if is_block and not isinstance(block, Mapping):
            issues.append(
                ValidationIssue(
                    "missing_block_metadata",
                    base_path + ".block",
                    "Block transactions must declare content/count/payload length metadata.",
                )
            )
            continue

        if not is_block and isinstance(block, Mapping):
            issues.append(
                ValidationIssue(
                    "block_metadata_without_block_transaction",
                    base_path + ".block",
                    "data.block is only valid with read_block or write_block transactions.",
                )
            )
            continue

        if not isinstance(block, Mapping):
            continue

        content_bytes = block.get("content_bytes")
        count_prefix_bytes = block.get("count_prefix_bytes")
        payload_bytes = block.get("transaction_payload_bytes")

        if (
            isinstance(byte_count, int)
            and not isinstance(byte_count, bool)
            and isinstance(content_bytes, int)
            and not isinstance(content_bytes, bool)
            and byte_count != content_bytes
        ):
            issues.append(
                ValidationIssue(
                    "block_content_length_mismatch",
                    base_path + ".block.content_bytes",
                    f"data.bytes={byte_count} must equal block.content_bytes={content_bytes}.",
                )
            )

        if count_prefix_bytes != 1:
            issues.append(
                ValidationIssue(
                    "invalid_block_count_prefix",
                    base_path + ".block.count_prefix_bytes",
                    "SMBus block metadata requires exactly one count-prefix byte.",
                )
            )

        if (
            isinstance(content_bytes, int)
            and not isinstance(content_bytes, bool)
            and isinstance(count_prefix_bytes, int)
            and not isinstance(count_prefix_bytes, bool)
            and isinstance(payload_bytes, int)
            and not isinstance(payload_bytes, bool)
            and payload_bytes != content_bytes + count_prefix_bytes
        ):
            issues.append(
                ValidationIssue(
                    "block_transaction_payload_length_mismatch",
                    base_path + ".block.transaction_payload_bytes",
                    "transaction_payload_bytes must equal content_bytes + count_prefix_bytes.",
                )
            )

        default = command.get("default")
        default_value = default.get("value") if isinstance(default, Mapping) else None
        if (
            data.get("kind") == "string"
            and isinstance(default_value, str)
            and isinstance(content_bytes, int)
            and len(default_value) > content_bytes
        ):
            issues.append(
                ValidationIssue(
                    "string_default_too_long",
                    _path("commands", command_id, "default", "value"),
                    f"Default string length {len(default_value)} exceeds block content length {content_bytes}.",
                )
            )

    return sorted(
        issues,
        key=lambda issue: (issue.severity != "error", issue.path, issue.code, issue.message),
    )
