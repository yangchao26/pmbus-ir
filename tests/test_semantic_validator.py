from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_validator import validate_semantics  # noqa: E402


def _minimal_document() -> dict:
    return {
        "data_formats": {"vout_linear": {}},
        "commands": {
            "STORE_DEFAULT_ALL": {
                "code": 0x11,
                "origin": "standard",
                "support": "full",
                "access": "execute",
                "transaction": {"write": "send_byte"},
                "data": {"kind": "none", "bytes": 0},
            },
            "VOUT_COMMAND": {
                "code": 0x21,
                "origin": "standard",
                "support": "full",
                "access": "read_write",
                "transaction": {"read": "read_word", "write": "write_word"},
                "data": {
                    "kind": "scalar",
                    "bytes": 2,
                    "format_ref": "vout_linear",
                    "quantity": "voltage",
                    "unit": "V",
                    "range": {"min": 9.5, "max": 12.5},
                },
                "default": {"value": 12.0},
                "persistence": {
                    "mode": "nonvolatile_via_command",
                    "commit_command": "STORE_DEFAULT_ALL",
                },
            },
        },
        "telemetry": {"output_voltage": {"command": "VOUT_COMMAND"}},
    }


class SemanticValidationTests(unittest.TestCase):
    def assert_issue(self, document: dict, code: str) -> None:
        issues = validate_semantics(document)
        self.assertIn(code, {issue.code for issue in issues}, issues)

    def test_minimal_document_is_semantically_valid(self) -> None:
        self.assertEqual(validate_semantics(_minimal_document()), [])

    def test_duplicate_command_code(self) -> None:
        document = _minimal_document()
        document["commands"]["OTHER"] = {
            "code": 0x21,
            "origin": "standard",
            "support": "full",
            "access": "read_only",
            "transaction": {"read": "read_byte"},
            "data": {"kind": "scalar", "bytes": 1},
        }
        self.assert_issue(document, "duplicate_command_code")

    def test_unknown_command_reference(self) -> None:
        document = _minimal_document()
        document["telemetry"]["output_voltage"]["command"] = "READ_VOUT"
        self.assert_issue(document, "unknown_command_ref")

    def test_unknown_format_reference(self) -> None:
        document = _minimal_document()
        document["commands"]["VOUT_COMMAND"]["data"]["format_ref"] = "missing_format"
        self.assert_issue(document, "unknown_format_ref")

    def test_invalid_range(self) -> None:
        document = _minimal_document()
        document["commands"]["VOUT_COMMAND"]["data"]["range"] = {
            "min": 13.0,
            "max": 12.0,
        }
        self.assert_issue(document, "invalid_range")

    def test_default_outside_range(self) -> None:
        document = _minimal_document()
        document["commands"]["VOUT_COMMAND"]["default"]["value"] = 13.0
        self.assert_issue(document, "default_outside_range")

    def test_default_relation_violation(self) -> None:
        document = _minimal_document()
        document["commands"]["VOUT_MARGIN_LOW"] = {
            "code": 0x26,
            "origin": "standard",
            "support": "full",
            "access": "read_write",
            "transaction": {"read": "read_word", "write": "write_word"},
            "data": {
                "kind": "scalar",
                "bytes": 2,
                "format_ref": "vout_linear",
                "quantity": "voltage",
                "unit": "V",
                "range": {"min": 8.1, "max": 13.2},
            },
            "default": {"value": 12.1},
        }
        document["commands"]["VOUT_COMMAND"]["constraints"] = [
            {
                "kind": "relation",
                "operator": "gt",
                "other_command": "VOUT_MARGIN_LOW",
            }
        ]
        self.assert_issue(document, "default_violates_constraint")

    def test_qodn217_reference_is_semantically_valid(self) -> None:
        reference_path = (
            REPO_ROOT / "examples" / "reference" / "qodn217a0b.pmbus.yaml"
        )
        with reference_path.open("r", encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
        self.assertEqual(validate_semantics(document), [])


if __name__ == "__main__":
    unittest.main()
