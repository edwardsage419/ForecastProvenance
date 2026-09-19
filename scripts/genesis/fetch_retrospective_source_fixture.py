#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "genesis" / "fixtures" / "retrospective" / "source_fixture_manifest_v0_1.json"
USER_AGENT = "ForecastProvenance-GEN001-RetrospectiveFixture/1.0"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("classification") != "RETROSPECTIVE_FIXTURE_MANIFEST":
        raise ValueError("manifest classification is not retrospective")
    if manifest.get("prospective_eligible") is not False:
        raise ValueError("fixture manifest must be permanently non-prospective")
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("fixture manifest has no fixtures")
    return manifest


def select_fixture(manifest: dict, fixture_id: str) -> dict:
    matches = [fixture for fixture in manifest["fixtures"] if fixture.get("fixture_id") == fixture_id]
    if len(matches) != 1:
        raise ValueError(f"fixture_id must match exactly one fixture: {fixture_id}")
    return matches[0]


class _SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, expected_host: str) -> None:
        super().__init__()
        self.expected_host = expected_host.lower()

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != self.expected_host:
            raise ValueError("redirect left admitted official HTTPS host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_fixture(fixture: dict, out_root: Path) -> Path:
    url = fixture["url"]
    expected_host = fixture["allowed_host"].lower()
    parsed = urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != expected_host:
        raise ValueError("fixture URL must use HTTPS on its admitted official host")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        method="GET",
    )
    context = ssl.create_default_context()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context),
        _SameHostRedirectHandler(expected_host),
    )
    with opener.open(request, timeout=30) as response:
        status = getattr(response, "status", None)
        final_url = response.geturl()
        final_host = (urlparse(final_url).hostname or "").lower()
        if status != 200:
            raise ValueError(f"official source returned HTTP {status}")
        if final_host != expected_host:
            raise ValueError(f"redirect left admitted official host: {final_host}")
        raw = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}

    if not raw:
        raise ValueError("official source returned an empty body")

    fixture_dir = out_root / fixture["fixture_id"]
    fixture_dir.mkdir(parents=True, exist_ok=False)
    raw_path = fixture_dir / "artifact.html"
    raw_path.write_bytes(raw)

    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata = {
        "schema_version": "1.0",
        "classification": "RETROSPECTIVE_SOURCE_ADAPTER_REHEARSAL",
        "prospective_eligible": False,
        "fixture_id": fixture["fixture_id"],
        "source_url": url,
        "resolved_url": final_url,
        "allowed_host": expected_host,
        "http_status": 200,
        "retrieved_at": retrieved_at,
        "raw_filename": raw_path.name,
        "raw_sha256": sha256_hex(raw),
        "raw_byte_length": len(raw),
        "content_type": headers.get("content-type", "UNKNOWN"),
        "etag": headers.get("etag", "UNKNOWN"),
        "last_modified": headers.get("last-modified", "UNKNOWN"),
        "expected_target_id": fixture["target_id"],
        "reference_period": fixture["reference_period"],
        "release_stage": fixture["release_stage"],
        "expected_semantics": fixture["expected_semantics"],
        "expected_display_value": fixture["expected_display_value"],
        "expected_canonical_decimal": fixture["expected_canonical_decimal"],
        "expected_display_scale": fixture["expected_display_scale"],
        "scientific_role": fixture["scientific_role"],
    }
    metadata_path = fixture_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch an admitted historical official source page for GEN_001 adapter rehearsal.")
    parser.add_argument("fixture_id")
    parser.add_argument("outdir", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
        fixture = select_fixture(manifest, args.fixture_id)
        metadata_path = fetch_fixture(fixture, args.outdir)
    except Exception as exc:
        print(f"fixture retrieval failed: {exc}", file=sys.stderr)
        return 2

    print(metadata_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
