from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required. Install tools/requirements.txt.") from exc

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    raise SystemExit("jsonschema is required. Install tools/requirements.txt.") from exc

from semantic_validator import ValidationIssue, validate_semantics


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _inline_command_schema(
    root_schema: dict[str, Any],
    command_schema: dict[str, Any],
) -> dict[str, Any]:
    schema = copy.deepcopy(root_schema)
    commands = schema.get("properties", {}).get("commands", {})
    additional = commands.get("additionalProperties")
    if isinstance(additional, dict) and additional.get("$ref") == "command.schema.json":
        commands["additionalProperties"] = command_schema
    return schema


def _format_jsonschema_path(parts: list[Any]) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def _structure_issues(
    document: Any,
    root_schema_path: Path,
    command_schema_path: Path,
) -> list[ValidationIssue]:
    root_schema = _load_json(root_schema_path)
    command_schema = _load_json(command_schema_path)
    combined = _inline_command_schema(root_schema, command_schema)
    validator = Draft202012Validator(combined)

    issues: list[ValidationIssue] = []
    for error in sorted(
        validator.iter_errors(document),
        key=lambda item: list(item.absolute_path),
    ):
        issues.append(
            ValidationIssue(
                code="schema_error",
                path=_format_jsonschema_path(list(error.absolute_path)),
                message=error.message,
            )
        )
    return issues


def _print_issues(issues: list[ValidationIssue]) -> None:
    for issue in issues:
        print(f"{issue.severity.upper()} {issue.code} {issue.path}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pmbus-ir")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a PMBus IR YAML document.",
    )
    validate_parser.add_argument("document", type=Path)
    validate_parser.add_argument(
        "--semantic-only",
        action="store_true",
        help="Skip JSON Schema validation and run semantic validation only.",
    )

    args = parser.parse_args(argv)
    if args.command != "validate":
        parser.error("Unsupported command.")

    document_path: Path = args.document.resolve()
    repo_root = Path(__file__).resolve().parents[1]
    root_schema_path = repo_root / "schema" / "pmbus-ir.schema.json"
    command_schema_path = repo_root / "schema" / "command.schema.json"

    try:
        document = _load_yaml(document_path)
    except FileNotFoundError:
        print(f"ERROR file_not_found $: {document_path}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"ERROR invalid_yaml $: {exc}", file=sys.stderr)
        return 2

    if not isinstance(document, dict):
        print("ERROR invalid_document $: top-level YAML value must be a mapping.")
        return 1

    issues: list[ValidationIssue] = []
    if not args.semantic_only:
        issues.extend(
            _structure_issues(
                document,
                root_schema_path,
                command_schema_path,
            )
        )

    issues.extend(validate_semantics(document))
    issues.sort(key=lambda issue: (issue.path, issue.code, issue.message))

    if issues:
        _print_issues(issues)
        print(f"\nValidation failed with {len(issues)} error(s).")
        return 1

    if args.semantic_only:
        print("Valid PMBus IR document: semantic validation passed.")
    else:
        print("Valid PMBus IR document: schema and semantic validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
