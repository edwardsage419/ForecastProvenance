#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from forecast_trust_core.canonical import parse_json_strict, require_utc_timestamp, seal_object
from forecast_trust_core.genesis_sources import (
    adapt_bea_real_gdp_advance_html,
    adapt_bls_cpi_html,
    adapt_bls_u3_html,
    parse_cpi_first_release,
    parse_real_gdp_advance,
    parse_u3_first_release,
    validate_official_artifact,
)


ROOT = Path(__file__).resolve().parents[2]
FROZEN_MANIFEST = ROOT / "genesis" / "fixtures" / "retrospective" / "source_fixture_manifest_v0_1.json"

_MANIFEST_BOUND_FIELDS = (
    "url",
    "allowed_host",
    "target_id",
    "reference_period",
    "release_stage",
    "expected_semantics",
    "expected_display_value",
    "expected_canonical_decimal",
    "expected_display_scale",
    "scientific_role",
)

_METADATA_FIELD_MAP = {
    "url": "source_url",
    "allowed_host": "allowed_host",
    "target_id": "expected_target_id",
    "reference_period": "reference_period",
    "release_stage": "release_stage",
    "expected_semantics": "expected_semantics",
    "expected_display_value": "expected_display_value",
    "expected_canonical_decimal": "expected_canonical_decimal",
    "expected_display_scale": "expected_display_scale",
    "scientific_role": "scientific_role",
}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = parse_json_strict(path.read_bytes())
    except (OSError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not valid strict JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _load_frozen_fixture(fixture_id: str) -> Mapping[str, Any]:
    manifest = _load_json_object(FROZEN_MANIFEST, label="frozen retrospective source manifest")
    if manifest.get("classification") != "RETROSPECTIVE_FIXTURE_MANIFEST":
        raise ValueError("frozen retrospective source manifest classification mismatch")
    if manifest.get("prospective_eligible") is not False:
        raise ValueError("frozen retrospective source manifest must remain non-prospective")
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError("frozen retrospective source manifest fixtures must be an array")
    matches = [
        fixture
        for fixture in fixtures
        if isinstance(fixture, dict) and fixture.get("fixture_id") == fixture_id
    ]
    if len(matches) != 1:
        raise ValueError("fixture_id must match exactly one frozen retrospective fixture")
    return matches[0]


def _validate_manifest_binding(
    metadata: Mapping[str, Any],
    frozen_fixture: Mapping[str, Any],
) -> None:
    for manifest_field in _MANIFEST_BOUND_FIELDS:
        metadata_field = _METADATA_FIELD_MAP[manifest_field]
        if metadata.get(metadata_field) != frozen_fixture.get(manifest_field):
            raise ValueError(
                f"fixture metadata {metadata_field} differs from frozen retrospective manifest"
            )


def validate_fixture(fixture_dir: Path) -> dict:
    metadata_path = fixture_dir / "metadata.json"
    artifact_path = fixture_dir / "artifact.html"
    if not metadata_path.is_file() or not artifact_path.is_file():
        raise ValueError("fixture directory must contain metadata.json and artifact.html")

    metadata = _load_json_object(metadata_path, label="fixture metadata")
    raw = artifact_path.read_bytes()
    raw_sha = sha256_hex(raw)

    if metadata.get("schema_version") != "1.0":
        raise ValueError("fixture metadata schema_version mismatch")
    if metadata.get("classification") != "RETROSPECTIVE_SOURCE_ADAPTER_REHEARSAL":
        raise ValueError("fixture metadata classification is not retrospective rehearsal")
    if metadata.get("prospective_eligible") is not False:
        raise ValueError("fixture metadata must remain non-prospective")
    if metadata.get("raw_filename") != "artifact.html":
        raise ValueError("fixture metadata raw_filename must identify artifact.html")
    if metadata.get("raw_byte_length") != len(raw):
        raise ValueError("raw artifact byte length differs from metadata")
    retrieved_at = metadata.get("retrieved_at")
    try:
        require_utc_timestamp(retrieved_at)
    except Exception as exc:
        raise ValueError("fixture metadata retrieved_at must be canonical UTC") from exc
    content_type = metadata.get("content_type")
    if not isinstance(content_type, str) or not content_type.strip():
        raise ValueError("fixture metadata content_type missing")
    if metadata.get("raw_sha256") != raw_sha:
        raise ValueError("raw artifact SHA256 differs from metadata")

    fixture_id = metadata.get("fixture_id")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise ValueError("fixture_id missing")
    if fixture_dir.name != fixture_id:
        raise ValueError("fixture directory name differs from fixture_id")
    frozen_fixture = _load_frozen_fixture(fixture_id)
    _validate_manifest_binding(metadata, frozen_fixture)

    allowed_host = frozen_fixture["allowed_host"]
    validate_official_artifact(
        {
            "resolved_url": metadata.get("resolved_url"),
            "raw_sha256": raw_sha,
            "http_status": metadata.get("http_status"),
        },
        allowed_hosts=[allowed_host],
        expected_sha256=metadata.get("raw_sha256"),
    )

    reference_period = frozen_fixture["reference_period"]
    if fixture_id == "bls_cpi_2026_07_first_release":
        records = adapt_bls_cpi_html(raw, reference_month=reference_period)
        released = parse_cpi_first_release(records, reference_month=reference_period)
    elif fixture_id == "bls_u3_2026_08_first_release":
        records = adapt_bls_u3_html(raw, reference_month=reference_period)
        released = parse_u3_first_release(records, reference_month=reference_period)
    elif fixture_id == "bea_gdp_2026_q2_advance":
        records = adapt_bea_real_gdp_advance_html(raw, reference_quarter=reference_period)
        released = parse_real_gdp_advance(records, reference_quarter=reference_period)
    else:
        raise ValueError(f"unrecognized fixture_id: {fixture_id}")

    if released.display_value != frozen_fixture["expected_display_value"]:
        raise ValueError("adapter display value differs from frozen fixture expectation")
    if released.canonical_decimal != frozen_fixture["expected_canonical_decimal"]:
        raise ValueError("adapter canonical decimal differs from frozen fixture expectation")
    if released.display_scale != frozen_fixture["expected_display_scale"]:
        raise ValueError("adapter display scale differs from frozen fixture expectation")

    payload = {
        "schema_version": "1.0",
        "classification": "RETROSPECTIVE_SOURCE_ADAPTER_REPORT",
        "prospective_eligible": False,
        "fixture_id": fixture_id,
        "target_id": frozen_fixture["target_id"],
        "reference_period": reference_period,
        "source_url": frozen_fixture["url"],
        "resolved_url": metadata.get("resolved_url"),
        "raw_artifact_sha256": raw_sha,
        "raw_artifact_byte_length": len(raw),
        "semantic_record_count": len(records),
        "released_display_value": released.display_value,
        "released_canonical_decimal": released.canonical_decimal,
        "released_display_scale": released.display_scale,
        "expected_semantics": frozen_fixture["expected_semantics"],
        "validation_result": "VALID_RETROSPECTIVE_FIXTURE",
    }
    return seal_object(
        payload,
        object_type="SourceAdapterReport",
        stable_context=fixture_id,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a retained retrospective official source fixture.")
    parser.add_argument("fixture_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        report = validate_fixture(args.fixture_dir)
    except Exception as exc:
        print(f"source fixture validation failed: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
