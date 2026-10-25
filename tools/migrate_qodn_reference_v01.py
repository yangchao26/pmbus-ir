from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = REPO_ROOT / "examples" / "reference" / "qodn217a0b.pmbus.yaml"
SEMANTIC_TEST = REPO_ROOT / "tests" / "test_semantic_validator.py"


def replace_exact(text: str, old: str, new: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(
            f"Expected {expected} occurrence(s), found {count}: {old[:120]!r}"
        )
    return text.replace(old, new)


def migrate_reference() -> None:
    text = REFERENCE.read_text(encoding="utf-8")

    text = replace_exact(
        text,
        "vout_linear: {wire_bytes: 2, mantissa: unsigned_16_bit, exponent: {fixed: -12, source: VOUT_MODE}, resolution_v: 0.000244140625}",
        "vout_linear: {wire_bytes: 2, mantissa: unsigned_16_bit, exponent: {fixed: -12, source: VOUT_MODE}, encoding_resolution: 0.000244140625}",
    )

    replacements = {
        "resolution: 0.000244140625": "encoding_resolution: 0.000244140625, published_resolution: 0.000244",
        "resolution: 0.5": "encoding_resolution: 0.5, published_resolution: 0.5",
        "resolution: 0.125": "encoding_resolution: 0.125, published_resolution: 0.125",
        "resolution: 0.000244": "encoding_resolution: 0.000244140625, published_resolution: 0.000244",
        "resolution: 0.146": "encoding_resolution: 0.125, published_resolution: 0.146",
        "resolution: 0.25": "encoding_resolution: 0.25, published_resolution: 0.25",
    }
    expected_counts = {
        "resolution: 0.000244140625": 1,
        "resolution: 0.5": 2,
        "resolution: 0.125": 1,
        "resolution: 0.000244": 1,
        "resolution: 0.146": 1,
        "resolution: 0.25": 1,
    }
    for old, new in replacements.items():
        text = replace_exact(text, old, new, expected_counts[old])

    block_rows = {
        "MFR_ID": (5, 4),
        "MFR_MODEL": (18, 17),
        "MFR_REVISION": (8, 7),
        "MFR_LOCATION": (12, 11),
        "MFR_DATE": (6, 5),
        "MFR_SERIAL": (18, 17),
    }
    for command_id, (quick_bytes, content_bytes) in block_rows.items():
        old_fragment = (
            f"data: {{kind: string, bytes: {quick_bytes}, encoding: 8_bit_character}}"
        )
        basis = (
            "MFR_ID_default_OMPW_establishes_count_prefix_convention"
            if command_id == "MFR_ID"
            else "same_quick_reference_table_convention_as_MFR_ID"
        )
        new_fragment = (
            f"data: {{kind: string, bytes: {content_bytes}, encoding: 8_bit_character, "
            f"block: {{content_bytes: {content_bytes}, count_prefix_bytes: 1, "
            f"transaction_payload_bytes: {quick_bytes}}}}}, "
            f"source: {{quick_reference_data_bytes: {quick_bytes}, "
            f"quick_reference_data_bytes_interpretation: includes_count_prefix, "
            f"interpretation_basis: {basis}}}"
        )
        text = replace_exact(text, old_fragment, new_fragment)

    old_mod = (
        "data: {kind: structured, bytes: 12}, default: {value: MS}, conditions: "
        "[{kind: manufacturer_write_protect_gate, command: MFR_DEVICE_TYPE, field: WPE, "
        "source_wording: lockout per MFR_DEVICE_TYPE}], source: {conflict: Detailed "
        "description says read support for a 12-byte block; quick-reference table labels "
        "transfer type as Read byte.}, notes: [Detailed description is preferred for "
        "transaction shape.]"
    )
    new_mod = (
        "data: {kind: structured, bytes: 12, block: {content_bytes: 12, "
        "count_prefix_bytes: 1, transaction_payload_bytes: 13}}, default: {value: MS}, "
        "conditions: [{kind: manufacturer_write_protect_gate, command: MFR_DEVICE_TYPE, "
        "field: WPE, source_wording: lockout per MFR_DEVICE_TYPE}], source: {conflict: "
        "Detailed description says read support for a 12-byte block; quick-reference table "
        "labels transfer type as Read byte., detailed_description_content_bytes: 12, "
        "quick_reference_data_bytes: 12, quick_reference_data_bytes_interpretation: "
        "ambiguous}, notes: [Detailed description is preferred for transaction shape and "
        "content length.]"
    )
    text = replace_exact(text, old_mod, new_mod)

    text = replace_exact(text, "resolution_v: 0.000244", "published_resolution_v: 0.000244")
    text = replace_exact(text, "resolution_v: 0.125", "published_resolution_v: 0.125")
    text = replace_exact(text, "resolution_degC: 0.25", "published_resolution_degC: 0.25")

    final_conflict = (
        "  mfr_mod_date_loc_sn_transfer: {statements: [Detailed description says read "
        "support for a 12-byte block., Quick-reference table lists 12 data bytes but "
        "transfer type 'Read byte'.], resolution: detailed_description_preferred_for_transaction}"
    )
    added_conflict = final_conflict + (
        "\n  mfr_mod_date_loc_sn_block_length: {statements: [Detailed description says read "
        "support for a 12-byte block., Quick-reference table lists DATA BYTES = 12, while "
        "the standard MFR block-string rows appear to count the one-byte block count prefix "
        "in DATA BYTES; MFR_ID is 5 data bytes with the four-character default OMPW.], "
        "resolution: Treat the detailed 12-byte block statement as semantic content length; "
        "preserve the quick-reference counting ambiguity.}"
    )
    text = replace_exact(text, final_conflict, added_conflict)

    REFERENCE.write_text(text, encoding="utf-8")


def migrate_test_expectation() -> None:
    text = SEMANTIC_TEST.read_text(encoding="utf-8")
    old = (
        '        warning_codes = {issue.code for issue in issues if issue.severity == "warning"}\n'
        '        self.assertIn("ambiguous_resolution_semantics", warning_codes)'
    )
    new = (
        '        warnings = [issue for issue in issues if issue.severity == "warning"]\n'
        '        self.assertEqual(warnings, [], issues)'
    )
    text = replace_exact(text, old, new)
    SEMANTIC_TEST.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    migrate_reference()
    migrate_test_expectation()
