from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from data_semantics import validate_data_model_semantics  # noqa: E402


def _block_document() -> dict:
    return {
        "commands": {
            "MFR_ID": {
                "code": 0x99,
                "origin": "standard",
                "support": "full",
                "access": "read_only",
                "transaction": {"read": "read_block"},
                "data": {
                    "kind": "string",
                    "bytes": 4,
                    "encoding": "8_bit_character",
                    "block": {
                        "content_bytes": 4,
                        "count_prefix_bytes": 1,
                        "transaction_payload_bytes": 5,
                    },
                },
                "default": {"value": "OMPW"},
            }
        }
    }


class DataSemanticsTests(unittest.TestCase):
    def assert_issue(self, document: dict, code: str) -> None:
        issues = validate_data_model_semantics(document)
        self.assertIn(code, {issue.code for issue in issues}, issues)

    def test_canonical_block_is_valid(self) -> None:
        self.assertEqual(validate_data_model_semantics(_block_document()), [])

    def test_block_requires_metadata(self) -> None:
        document = _block_document()
        del document["commands"]["MFR_ID"]["data"]["block"]
        self.assert_issue(document, "missing_block_metadata")

    def test_content_bytes_match_data_bytes(self) -> None:
        document = _block_document()
        document["commands"]["MFR_ID"]["data"]["block"]["content_bytes"] = 5
        self.assert_issue(document, "block_content_length_mismatch")

    def test_count_prefix_is_one_byte(self) -> None:
        document = _block_document()
        document["commands"]["MFR_ID"]["data"]["block"]["count_prefix_bytes"] = 2
        self.assert_issue(document, "invalid_block_count_prefix")

    def test_payload_length_math(self) -> None:
        document = _block_document()
        document["commands"]["MFR_ID"]["data"]["block"]["transaction_payload_bytes"] = 4
        self.assert_issue(document, "block_transaction_payload_length_mismatch")

    def test_block_metadata_requires_block_transaction(self) -> None:
        document = _block_document()
        document["commands"]["MFR_ID"]["transaction"] = {"read": "read_byte"}
        self.assert_issue(document, "block_metadata_without_block_transaction")

    def test_legacy_resolution_warns(self) -> None:
        document = {
            "commands": {
                "READ_VIN": {
                    "code": 0x88,
                    "origin": "standard",
                    "support": "full",
                    "access": "read_only",
                    "transaction": {"read": "read_word"},
                    "data": {
                        "kind": "scalar",
                        "bytes": 2,
                        "format": {"type": "linear11", "fixed_exponent": -3},
                        "resolution": 0.125,
                    },
                }
            }
        }
        issues = validate_data_model_semantics(document)
        warnings = [issue for issue in issues if issue.severity == "warning"]
        self.assertIn("legacy_resolution_field", {issue.code for issue in warnings})

    def test_qodn217_reference_is_canonical_data_ir(self) -> None:
        reference_path = REPO_ROOT / "examples" / "reference" / "qodn217a0b.pmbus.yaml"
        with reference_path.open("r", encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
        self.assertEqual(validate_data_model_semantics(document), [])


if __name__ == "__main__":
    unittest.main()
