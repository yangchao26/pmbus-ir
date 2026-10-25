from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str
    severity: str = "error"


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


def _iter_named_command_refs(
    node: Any,
    path_parts: tuple[object, ...],
) -> Iterable[tuple[str, str]]:
    if isinstance(node, Mapping):
        for key, value in node.items():
            current = path_parts + (key,)
            if (
                isinstance(key, str)
                and isinstance(value, str)
                and (key == "command" or key.endswith("_command"))
            ):
                yield _path(*current), value
            else:
                yield from _iter_named_command_refs(value, current)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_named_command_refs(value, path_parts + (index,))


def _numeric_default(command: Mapping[str, Any]) -> float | int | None:
    default = command.get("default")
    if not isinstance(default, Mapping):
        return None
    value = default.get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


def _data_unit(command: Mapping[str, Any]) -> str | None:
    data = command.get("data")
    if isinstance(data, Mapping):
        unit = data.get("unit")
        if isinstance(unit, str):
            return unit
    return None


def _compare(lhs: float, operator: str, rhs: float) -> bool:
    return {
        "gt": lhs > rhs,
        "ge": lhs >= rhs,
        "lt": lhs < rhs,
        "le": lhs <= rhs,
        "eq": lhs == rhs,
        "ne": lhs != rhs,
    }[operator]


def _format_type(descriptor: Mapping[str, Any]) -> str | None:
    explicit = descriptor.get("type")
    if explicit in {"linear11", "vout_linear"}:
        return str(explicit)

    # Expanded descriptors used by the first QODN217A0B reference document.
    mantissa = descriptor.get("mantissa")
    exponent = descriptor.get("exponent")
    if mantissa == "unsigned_16_bit" and isinstance(exponent, Mapping):
        return "vout_linear"
    if (
        mantissa == "signed_11_bit_twos_complement"
        and exponent == "signed_5_bit_twos_complement"
    ):
        return "linear11"
    return None


def _fixed_exponent(descriptor: Mapping[str, Any]) -> int | None:
    fixed = descriptor.get("fixed_exponent")
    if isinstance(fixed, int) and not isinstance(fixed, bool):
        return fixed
    exponent = descriptor.get("exponent")
    if isinstance(exponent, Mapping):
        fixed = exponent.get("fixed")
        if isinstance(fixed, int) and not isinstance(fixed, bool):
            return fixed
    return None


def _exponent_source(descriptor: Mapping[str, Any]) -> str | None:
    source = descriptor.get("exponent_source")
    if isinstance(source, str):
        return source
    exponent = descriptor.get("exponent")
    if isinstance(exponent, Mapping):
        source = exponent.get("source")
        if isinstance(source, str):
            return source
    return None


def _wire_bytes(descriptor: Mapping[str, Any]) -> int | None:
    value = descriptor.get("wire_bytes")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _resolved_format(
    data: Mapping[str, Any],
    data_formats: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, str | None]:
    inline = data.get("format")
    if isinstance(inline, Mapping):
        return inline, "inline"
    format_ref = data.get("format_ref")
    if isinstance(format_ref, str):
        descriptor = data_formats.get(format_ref)
        if isinstance(descriptor, Mapping):
            return descriptor, format_ref
    return None, None


def _encoding_lsb(descriptor: Mapping[str, Any]) -> float | None:
    fixed = _fixed_exponent(descriptor)
    if fixed is None:
        return None
    return 2.0**fixed


def _validate_data_format_descriptor(
    descriptor: Mapping[str, Any],
    path: str,
    commands: Mapping[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    format_type = _format_type(descriptor)
    wire_bytes = _wire_bytes(descriptor)

    if format_type in {"linear11", "vout_linear"} and wire_bytes is not None and wire_bytes != 2:
        issues.append(
            ValidationIssue(
                "format_wire_width_mismatch",
                path + ".wire_bytes",
                f"{format_type} uses a 2-byte wire representation, not {wire_bytes} bytes.",
            )
        )

    fixed = _fixed_exponent(descriptor)
    if fixed is not None and not (-16 <= fixed <= 15):
        issues.append(
            ValidationIssue(
                "invalid_fixed_exponent",
                path + ".fixed_exponent",
                f"Fixed exponent {fixed} is outside the signed 5-bit range [-16, 15].",
            )
        )

    source = _exponent_source(descriptor)
    if source is not None and source not in commands:
        issues.append(
            ValidationIssue(
                "unknown_command_ref",
                path + ".exponent_source",
                f"Exponent source command {source!r} does not exist.",
            )
        )

    # If expanded representation fields are present, validate that they match
    # the selected PMBus IR format type. The compact canonical form may omit
    # them because the type itself carries these representation semantics.
    mantissa = descriptor.get("mantissa")
    exponent = descriptor.get("exponent")
    if format_type == "linear11":
        if mantissa is not None and mantissa != "signed_11_bit_twos_complement":
            issues.append(
                ValidationIssue(
                    "linear11_representation_mismatch",
                    path + ".mantissa",
                    "LINEAR11 mantissa must be signed 11-bit two's-complement when represented explicitly.",
                )
            )
        if isinstance(exponent, str) and exponent != "signed_5_bit_twos_complement":
            issues.append(
                ValidationIssue(
                    "linear11_representation_mismatch",
                    path + ".exponent",
                    "LINEAR11 exponent must be signed 5-bit two's-complement when represented explicitly.",
                )
            )
    elif format_type == "vout_linear":
        if mantissa is not None and mantissa != "unsigned_16_bit":
            issues.append(
                ValidationIssue(
                    "vout_linear_representation_mismatch",
                    path + ".mantissa",
                    "VOUT Linear mantissa must be unsigned 16-bit when represented explicitly.",
                )
            )

    descriptor_resolution = descriptor.get("resolution_v")
    lsb = _encoding_lsb(descriptor)
    if (
        lsb is not None
        and isinstance(descriptor_resolution, (int, float))
        and not isinstance(descriptor_resolution, bool)
        and not isclose(float(descriptor_resolution), lsb, rel_tol=1e-9, abs_tol=1e-12)
    ):
        issues.append(
            ValidationIssue(
                "encoding_resolution_mismatch",
                path + ".resolution_v",
                f"Declared encoding resolution {descriptor_resolution} does not equal 2^{_fixed_exponent(descriptor)} = {lsb}.",
            )
        )

    return issues


def _validate_command_data_semantics(
    command_id: str,
    command: Mapping[str, Any],
    data_formats: Mapping[str, Any],
    commands: Mapping[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    data = command.get("data")
    if not isinstance(data, Mapping):
        return issues

    base_path = _path("commands", command_id, "data")
    kind = data.get("kind")
    byte_count = data.get("bytes")
    transaction = command.get("transaction")
    if not isinstance(transaction, Mapping):
        transaction = {}

    descriptor, descriptor_name = _resolved_format(data, data_formats)
    if descriptor is not None:
        format_path = (
            _path("data_formats", descriptor_name)
            if descriptor_name not in {None, "inline"}
            else base_path + ".format"
        )
        format_type = _format_type(descriptor)
        expected_bytes = _wire_bytes(descriptor)
        if expected_bytes is None and format_type in {"linear11", "vout_linear"}:
            expected_bytes = 2
        if (
            expected_bytes is not None
            and isinstance(byte_count, int)
            and not isinstance(byte_count, bool)
            and byte_count != expected_bytes
        ):
            issues.append(
                ValidationIssue(
                    "format_payload_width_mismatch",
                    base_path + ".bytes",
                    f"Command declares {byte_count} data bytes but format requires {expected_bytes}.",
                )
            )
        if format_type in {"linear11", "vout_linear"} and kind != "scalar":
            issues.append(
                ValidationIssue(
                    "format_kind_mismatch",
                    base_path + ".kind",
                    f"{format_type} is a scalar numeric format but data.kind is {kind!r}.",
                )
            )

        fixed = _fixed_exponent(descriptor)
        lsb = _encoding_lsb(descriptor)
        encoding_resolution = data.get("encoding_resolution")
        if (
            lsb is not None
            and isinstance(encoding_resolution, (int, float))
            and not isinstance(encoding_resolution, bool)
            and not isclose(float(encoding_resolution), lsb, rel_tol=1e-9, abs_tol=1e-12)
        ):
            issues.append(
                ValidationIssue(
                    "encoding_resolution_mismatch",
                    base_path + ".encoding_resolution",
                    f"encoding_resolution {encoding_resolution} does not equal 2^{fixed} = {lsb}.",
                )
            )

        # `resolution` predates the explicit split between encoding LSB and
        # published device/measurement resolution. Treat a material mismatch
        # as a warning so source facts such as QODN217A0B READ_IOUT=0.146 A are
        # preserved rather than rewritten to match the numeric encoding.
        legacy_resolution = data.get("resolution")
        if (
            lsb is not None
            and isinstance(legacy_resolution, (int, float))
            and not isinstance(legacy_resolution, bool)
            and not isclose(float(legacy_resolution), lsb, rel_tol=0.01, abs_tol=1e-12)
        ):
            issues.append(
                ValidationIssue(
                    "ambiguous_resolution_semantics",
                    base_path + ".resolution",
                    f"resolution {legacy_resolution} differs from encoding LSB {lsb}; use encoding_resolution for the encoding LSB and published_resolution for a source-published device resolution.",
                    severity="warning",
                )
            )

        step = data.get("step")
        if (
            lsb is not None
            and isinstance(step, (int, float))
            and not isinstance(step, bool)
            and step > 0
        ):
            ratio = float(step) / lsb
            if not isclose(ratio, round(ratio), rel_tol=1e-9, abs_tol=1e-9):
                issues.append(
                    ValidationIssue(
                        "step_not_encoding_multiple",
                        base_path + ".step",
                        f"Step {step} is not an integer multiple of encoding LSB {lsb}.",
                    )
                )

    if kind == "bit_field" and isinstance(byte_count, int) and not isinstance(byte_count, bool):
        if byte_count <= 0:
            issues.append(
                ValidationIssue(
                    "invalid_bit_field_width",
                    base_path + ".bytes",
                    "bit_field data must contain at least one byte.",
                )
            )
        bits = data.get("bits")
        if isinstance(bits, Mapping):
            max_bit = byte_count * 8 - 1
            for bit_key in bits:
                try:
                    bit_index = int(bit_key)
                except (TypeError, ValueError):
                    issues.append(
                        ValidationIssue(
                            "invalid_bit_index",
                            base_path + f".bits[{bit_key!r}]",
                            "Bit-field keys must be non-negative integer bit positions.",
                        )
                    )
                    continue
                if bit_index < 0 or bit_index > max_bit:
                    issues.append(
                        ValidationIssue(
                            "bit_out_of_range",
                            base_path + f".bits[{bit_key!r}]",
                            f"Bit {bit_index} does not fit in {byte_count} byte(s); valid range is 0..{max_bit}.",
                        )
                    )

    is_block = transaction.get("read") == "read_block" or transaction.get("write") == "write_block"
    if is_block and isinstance(byte_count, int) and byte_count <= 0:
        issues.append(
            ValidationIssue(
                "invalid_block_length",
                base_path + ".bytes",
                "Block transactions must declare a positive data byte count.",
            )
        )

    if kind == "string":
        if not isinstance(byte_count, int) or byte_count <= 0:
            issues.append(
                ValidationIssue(
                    "invalid_string_length",
                    base_path + ".bytes",
                    "String data must declare a positive byte count.",
                )
            )
        if not is_block:
            issues.append(
                ValidationIssue(
                    "string_requires_block_transaction",
                    base_path,
                    "String data requires read_block or write_block transaction semantics in Data IR v0.1.",
                )
            )
        encoding = data.get("encoding")
        if not isinstance(encoding, str):
            issues.append(
                ValidationIssue(
                    "missing_string_encoding",
                    base_path + ".encoding",
                    "String data must declare an encoding.",
                )
            )
        default = command.get("default")
        default_value = default.get("value") if isinstance(default, Mapping) else None
        if isinstance(default_value, str) and isinstance(byte_count, int):
            encoded_length = len(default_value)
            if encoded_length > byte_count:
                issues.append(
                    ValidationIssue(
                        "string_default_too_long",
                        _path("commands", command_id, "default", "value"),
                        f"Default string length {encoded_length} exceeds declared data length {byte_count}.",
                    )
                )

    if kind == "none" and byte_count != 0:
        issues.append(
            ValidationIssue(
                "none_data_has_payload",
                base_path + ".bytes",
                "data.kind=none requires bytes=0.",
            )
        )

    return issues


def validate_semantics(document: Mapping[str, Any]) -> list[ValidationIssue]:
    """Validate cross-object and document-level PMBus IR invariants.

    This validator checks internal consistency only. It does not embed or
    reproduce normative PMBus command definitions.
    """

    issues: list[ValidationIssue] = []

    commands_raw = document.get("commands", {})
    if not isinstance(commands_raw, Mapping):
        return issues
    commands: Mapping[str, Any] = commands_raw

    data_formats_raw = document.get("data_formats", {})
    data_formats: Mapping[str, Any]
    if isinstance(data_formats_raw, Mapping):
        data_formats = data_formats_raw
    else:
        data_formats = {}

    # 1. Command-code uniqueness.
    by_code: dict[int, list[str]] = {}
    for command_id, command in commands.items():
        if not isinstance(command, Mapping):
            continue
        code = command.get("code")
        if isinstance(code, int) and not isinstance(code, bool):
            by_code.setdefault(code, []).append(command_id)
    for code, ids in sorted(by_code.items()):
        if len(ids) > 1:
            rendered = ", ".join(ids)
            for command_id in ids:
                issues.append(
                    ValidationIssue(
                        "duplicate_command_code",
                        _path("commands", command_id, "code"),
                        f"Command code 0x{code:02X} is used by multiple commands: {rendered}.",
                    )
                )

    # 2. Canonical names and aliases must not collide.
    aliases: dict[str, str] = {}
    canonical_ids = set(commands.keys())
    for command_id, command in commands.items():
        if not isinstance(command, Mapping):
            continue
        raw_aliases = command.get("aliases", [])
        if not isinstance(raw_aliases, list):
            continue
        for index, alias in enumerate(raw_aliases):
            if not isinstance(alias, str):
                continue
            alias_path = _path("commands", command_id, "aliases", index)
            if alias in canonical_ids and alias != command_id:
                issues.append(
                    ValidationIssue(
                        "alias_collides_with_command",
                        alias_path,
                        f"Alias {alias!r} collides with canonical command {alias!r}.",
                    )
                )
            previous = aliases.get(alias)
            if previous is not None and previous != command_id:
                issues.append(
                    ValidationIssue(
                        "duplicate_alias",
                        alias_path,
                        f"Alias {alias!r} is declared by both {previous} and {command_id}.",
                    )
                )
            else:
                aliases[alias] = command_id

    # 3. Reusable data-format descriptors.
    for format_id, descriptor in data_formats.items():
        if isinstance(descriptor, Mapping):
            issues.extend(
                _validate_data_format_descriptor(
                    descriptor,
                    _path("data_formats", format_id),
                    commands,
                )
            )

    # 4. Data-format references and command-local data semantics.
    for command_id, command in commands.items():
        if not isinstance(command, Mapping):
            continue
        data = command.get("data")
        if not isinstance(data, Mapping):
            continue

        format_ref = data.get("format_ref")
        if isinstance(format_ref, str) and format_ref not in data_formats:
            issues.append(
                ValidationIssue(
                    "unknown_format_ref",
                    _path("commands", command_id, "data", "format_ref"),
                    f"format_ref {format_ref!r} is not defined under data_formats.",
                )
            )

        inline_format = data.get("format")
        if isinstance(inline_format, Mapping):
            issues.extend(
                _validate_data_format_descriptor(
                    inline_format,
                    _path("commands", command_id, "data", "format"),
                    commands,
                )
            )

        issues.extend(
            _validate_command_data_semantics(
                command_id,
                command,
                data_formats,
                commands,
            )
        )

        value_range = data.get("range")
        if isinstance(value_range, Mapping):
            minimum = value_range.get("min")
            maximum = value_range.get("max")
            if (
                isinstance(minimum, (int, float))
                and not isinstance(minimum, bool)
                and isinstance(maximum, (int, float))
                and not isinstance(maximum, bool)
                and minimum > maximum
            ):
                issues.append(
                    ValidationIssue(
                        "invalid_range",
                        _path("commands", command_id, "data", "range"),
                        f"Range minimum {minimum} is greater than maximum {maximum}.",
                    )
                )
            default_value = _numeric_default(command)
            if (
                default_value is not None
                and isinstance(minimum, (int, float))
                and not isinstance(minimum, bool)
                and isinstance(maximum, (int, float))
                and not isinstance(maximum, bool)
                and not (minimum <= default_value <= maximum)
            ):
                issues.append(
                    ValidationIssue(
                        "default_outside_range",
                        _path("commands", command_id, "default", "value"),
                        f"Default {default_value} lies outside [{minimum}, {maximum}].",
                    )
                )

    # 5. Command-internal references and relation constraints.
    for command_id, command in commands.items():
        if not isinstance(command, Mapping):
            continue

        persistence = command.get("persistence")
        if isinstance(persistence, Mapping):
            for key in ("commit_command", "restore_command"):
                ref = persistence.get(key)
                if isinstance(ref, str) and ref not in commands:
                    issues.append(
                        ValidationIssue(
                            "unknown_command_ref",
                            _path("commands", command_id, "persistence", key),
                            f"Referenced command {ref!r} does not exist.",
                        )
                    )

        constraints = command.get("constraints")
        if not isinstance(constraints, list):
            continue
        for index, constraint in enumerate(constraints):
            if not isinstance(constraint, Mapping):
                continue
            if constraint.get("kind") != "relation":
                continue
            other_id = constraint.get("other_command")
            if not isinstance(other_id, str):
                continue
            constraint_path = _path("commands", command_id, "constraints", index)
            other = commands.get(other_id)
            if not isinstance(other, Mapping):
                issues.append(
                    ValidationIssue(
                        "unknown_command_ref",
                        constraint_path + ".other_command",
                        f"Referenced command {other_id!r} does not exist.",
                    )
                )
                continue

            current_unit = _data_unit(command)
            other_unit = _data_unit(other)
            constraint_unit = constraint.get("unit")
            if current_unit and other_unit and current_unit != other_unit and not constraint_unit:
                issues.append(
                    ValidationIssue(
                        "constraint_unit_mismatch",
                        constraint_path,
                        f"Relation compares {current_unit!r} with {other_unit!r} without an explicit conversion unit.",
                    )
                )

            lhs = _numeric_default(command)
            rhs = _numeric_default(other)
            operator = constraint.get("operator")
            offset = constraint.get("offset", 0)
            if (
                lhs is not None
                and rhs is not None
                and operator in {"gt", "ge", "lt", "le", "eq", "ne"}
                and isinstance(offset, (int, float))
                and not isinstance(offset, bool)
            ):
                rhs_adjusted = rhs + offset
                if not _compare(float(lhs), operator, float(rhs_adjusted)):
                    issues.append(
                        ValidationIssue(
                            "default_violates_constraint",
                            constraint_path,
                            f"Defaults violate relation: {command_id}={lhs} {operator} {other_id}={rhs} + {offset}.",
                        )
                    )

    # 6. Document-level command references. Extensions and source_conflicts are
    # deliberately excluded because they may mention commands that are not part
    # of the normative implemented command map.
    for domain in (
        "standards",
        "addressing",
        "telemetry",
        "configuration",
        "status",
        "faults",
        "persistence",
        "behavior",
    ):
        node = document.get(domain)
        if node is None:
            continue
        for ref_path, ref in _iter_named_command_refs(node, (domain,)):
            if ref not in commands and ref not in aliases:
                issues.append(
                    ValidationIssue(
                        "unknown_command_ref",
                        ref_path,
                        f"Referenced command {ref!r} does not exist and is not a declared alias.",
                    )
                )

    return sorted(
        issues,
        key=lambda issue: (issue.severity != "error", issue.path, issue.code, issue.message),
    )
