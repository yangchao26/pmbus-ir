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
        "data_formats": {
            "vout_linear": {
                "type": "vout_linear",
                "wire_bytes": 2,
                "fixed_exponent": -12,
                "exponent_source": "VOUT_MODE",
            }
        },
        "commands": {
            "STORE_DEFAULT_ALL": {
                "code": 0x11,
                "origin": "standard",
                "support": "full",
                "access": "execute",
                "transaction": {"write": "send_byte"},
                "data": {"kind": "none", "bytes": 0},
            },
            "VOUT_MODE": {
                "code": 0x20,
                "origin": "standard",
                "support": "full",
                "access": "read_only",
                "transaction": {"read": "read_byte"},
                "data": {"kind": "structured", "bytes": 1},
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
                    "encoding_resolution": 2**-12,
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

    def test_format_ref_payload_width_mismatch(self) -> None:
        document = _minimal_document()
        document["commands"]["VOUT_COMMAND"]["data"]["bytes"] = 1
        self.assert_issue(document, "format_payload_width_mismatch")

    def test_linear11_fixed_exponent_range(self) -> None:
        document = _minimal_document()
        document["commands"]["READ_VIN"] = {
            "code": 0x88,
            "origin": "standard",
            "support": "full",
            "access": "read_only",
            "transaction": {"read": "read_word"},
            "data": {
                "kind": "scalar",
                "bytes": 2,
                "format": {"type": "linear11", "fixed_exponent": -17},
            },
        }
        self.assert_issue(document, "invalid_fixed_exponent")

    def test_encoding_resolution_matches_fixed_exponent(self) -> None:
        document = _minimal_document()
        document["commands"]["READ_VIN"] = {
            "code": 0x88,
            "origin": "standard",
            "support": "full",
            "access": "read_only",
            "transaction": {"read": "read_word"},
            "data": {
                "kind": "scalar",
                "bytes": 2,
                "format": {"type": "linear11", "fixed_exponent": -3},
                "encoding_resolution": 0.25,
            },
        }
        self.assert_issue(document, "encoding_resolution_mismatch")

    def test_step_must_be_encoding_multiple(self) -> None:
        document = _minimal_document()
        document["commands"]["READ_VIN"] = {
            "code": 0x88,
            "origin": "standard",
            "support": "full",
            "access": "read_only",
            "transaction": {"read": "read_word"},
            "data": {
                "kind": "scalar",
                "bytes": 2,
                "format": {"type": "linear11", "fixed_exponent": -3},
                "step": 0.2,
            },
        }
        self.assert_issue(document, "step_not_encoding_multiple")

    def test_bit_field_width(self) -> None:
        document = _minimal_document()
        document["commands"]["STATUS_BYTE"] = {
            "code": 0x78,
            "origin": "standard",
            "support": "full",
            "access": "read_only",
            "transaction": {"read": "read_byte"},
            "data": {
                "kind": "bit_field",
                "bytes": 1,
                "bits": {"8": {"name": "OUT_OF_RANGE"}},
            },
        }
        self.assert_issue(document, "bit_out_of_range")

    def test_string_requires_block_transaction(self) -> None:
        document = _minimal_document()
        document["commands"]["MFR_ID"] = {
            "code": 0x99,
            "origin": "standard",
            "support": "full",
            "access": "read_only",
            "transaction": {"read": "read_byte"},
            "data": {"kind": "string", "bytes": 5, "encoding": "8_bit_character"},
        }
        self.assert_issue(document, "string_requires_block_transaction")

    def test_string_default_length(self) -> None:
        document = _minimal_document()
        document["commands"]["MFR_ID"] = {
            "code": 0x99,
            "origin": "standard",
            "support": "full",
            "access": "read_only",
            "transaction": {"read": "read_block"},
            "data": {"kind": "string", "bytes": 3, "encoding": "8_bit_character"},
            "default": {"value": "OMPW"},
        }
        self.assert_issue(document, "string_default_too_long")

    def test_vout_linear_expanded_representation(self) -> None:
        document = _minimal_document()
        document["data_formats"]["vout_linear"]["mantissa"] = "signed_16_bit"
        self.assert_issue(document, "vout_linear_representation_mismatch")

    def test_qodn217_reference_has_no_semantic_errors(self) -> None:
        reference_path = (
            REPO_ROOT / "examples" / "reference" / "qodn217a0b.pmbus.yaml"
        )
        with reference_path.open("r", encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
        issues = validate_semantics(document)
        errors = [issue for issue in issues if issue.severity == "error"]
        self.assertEqual(errors, [], issues)
        warning_codes = {issue.code for issue in issues if issue.severity == "warning"}
        self.assertIn("ambiguous_resolution_semantics", warning_codes)


if __name__ == "__main__":
    unittest.main()
