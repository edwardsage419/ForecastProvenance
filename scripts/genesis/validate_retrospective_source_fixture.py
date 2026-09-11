#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from forecast_trust_core.canonical import seal_object
from forecast_trust_core.genesis_sources import (
    adapt_bea_real_gdp_advance_html,
    adapt_bls_cpi_html,
    adapt_bls_u3_html,
    parse_cpi_first_release,
    parse_real_gdp_advance,
    parse_u3_first_release,
    validate_official_artifact,
)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_fixture(fixture_dir: Path) -> dict:
    metadata_path = fixture_dir / "metadata.json"
    artifact_path = fixture_dir / "artifact.html"
    if not metadata_path.is_file() or not artifact_path.is_file():
        raise ValueError("fixture directory must contain metadata.json and artifact.html")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    raw = artifact_path.read_bytes()
    raw_sha = sha256_hex(raw)

    if metadata.get("classification") != "RETROSPECTIVE_SOURCE_ADAPTER_REHEARSAL":
        raise ValueError("fixture metadata classification is not retrospective rehearsal")
    if metadata.get("prospective_eligible") is not False:
        raise ValueError("fixture metadata must remain non-prospective")
    if metadata.get("raw_sha256") != raw_sha:
        raise ValueError("raw artifact SHA256 differs from metadata")

    allowed_host = metadata.get("allowed_host")
    if not isinstance(allowed_host, str):
        raise ValueError("allowed_host missing")
    validate_official_artifact(
        {
            "resolved_url": metadata.get("resolved_url"),
            "raw_sha256": raw_sha,
            "http_status": metadata.get("http_status"),
        },
        allowed_hosts=[allowed_host],
        expected_sha256=metadata.get("raw_sha256"),
    )

    fixture_id = metadata.get("fixture_id")
    reference_period = metadata.get("reference_period")
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

    expected_display = metadata.get("expected_display_value")
    expected_canonical = metadata.get("expected_canonical_decimal")
    expected_scale = metadata.get("expected_display_scale")
    if released.display_value != expected_display:
        raise ValueError("adapter display value differs from frozen fixture expectation")
    if released.canonical_decimal != expected_canonical:
        raise ValueError("adapter canonical decimal differs from frozen fixture expectation")
    if released.display_scale != expected_scale:
        raise ValueError("adapter display scale differs from frozen fixture expectation")

    payload = {
        "schema_version": "1.0",
        "classification": "RETROSPECTIVE_SOURCE_ADAPTER_REPORT",
        "prospective_eligible": False,
        "fixture_id": fixture_id,
        "target_id": metadata.get("expected_target_id"),
        "reference_period": reference_period,
        "source_url": metadata.get("source_url"),
        "resolved_url": metadata.get("resolved_url"),
        "raw_artifact_sha256": raw_sha,
        "raw_artifact_byte_length": len(raw),
        "semantic_record_count": len(records),
        "released_display_value": released.display_value,
        "released_canonical_decimal": released.canonical_decimal,
        "released_display_scale": released.display_scale,
        "expected_semantics": metadata.get("expected_semantics"),
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
