from __future__ import annotations

from dataclasses import dataclass
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

    # 3. Data-format references and local scalar invariants.
    data_formats = document.get("data_formats", {})
    if not isinstance(data_formats, Mapping):
        data_formats = {}
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

    # 4. Command-internal references and relation constraints.
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

    # 5. Document-level command references. Extensions and source_conflicts are
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

    return sorted(issues, key=lambda issue: (issue.path, issue.code, issue.message))
