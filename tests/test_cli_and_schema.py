from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from validate import _structure_issues  # noqa: E402
from semantic_validator import validate_semantics  # noqa: E402


def check_schema(document: dict):
    return _structure_issues(
        document,
        REPO_ROOT / "schema" / "pmbus-ir.schema.json",
        REPO_ROOT / "schema" / "command.schema.json",
        REPO_ROOT / "schema" / "data-format.schema.json",
    )


class RootSchemaAndCliTests(unittest.TestCase):
    def test_both_reference_documents_pass_root_schema(self) -> None:
        for device in ("qodn217a0b", "ebdw025a0b"):
            with self.subTest(device=device):
                path = REPO_ROOT / "examples" / "reference" / f"{device}.pmbus.yaml"
                document = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertEqual(check_schema(document), [])

    def test_invalid_ir_version_rejected(self) -> None:
        document = {"ir_version": "invalid", "device": {"manufacturer": "Example", "model": "TEST"}}
        self.assertTrue(check_schema(document))

    def test_empty_device_identity_rejected(self) -> None:
        document = {"ir_version": "0.1", "device": {"manufacturer": "", "model": ""}}
        self.assertTrue(check_schema(document))

    def test_reference_requires_source_and_commands(self) -> None:
        document = {
            "ir_version": "0.1",
            "device": {"manufacturer": "Example", "model": "TEST"},
            "document": {"kind": "reference_implementation"},
        }
        self.assertTrue(check_schema(document))

    def test_invalid_address_table_rejected(self) -> None:
        document = {
            "ir_version": "0.1",
            "device": {"manufacturer": "Example", "model": "TEST"},
            "addressing": {"reserved_addresses_decimal": [7, 7]},
        }
        self.assertTrue(check_schema(document))

    def test_cli_returns_parse_error_for_invalid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "invalid.pmbus.yaml"
            path.write_text("ir_version: [\n", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(TOOLS_DIR / "validate.py"), "validate", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("invalid_yaml", completed.stderr)

    def test_cli_rejects_semantic_duplicate_codes(self) -> None:
        document = {
            "ir_version": "0.1",
            "device": {"manufacturer": "Example", "model": "TEST"},
            "commands": {
                "A": {"code": 1, "origin": "standard", "support": "full", "access": "execute", "transaction": {"write": "send_byte"}, "data": {"kind": "none", "bytes": 0}},
                "B": {"code": 1, "origin": "standard", "support": "full", "access": "execute", "transaction": {"write": "send_byte"}, "data": {"kind": "none", "bytes": 0}},
            },
        }
        self.assertIn("duplicate_command_code", {issue.code for issue in validate_semantics(document)})


if __name__ == "__main__":
    unittest.main()
