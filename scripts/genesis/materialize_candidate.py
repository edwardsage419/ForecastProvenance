#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from forecast_trust_core.canonical import canonical_json, sha256_hex, verify_sealed_object


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = ROOT / "genesis" / "candidate"
DEFAULT_BASE = CANDIDATE_DIR / "objects" / "candidate_object_set_v0_2.json"
AUTHORITY_DECLARATION = CANDIDATE_DIR / "candidate_lineage_authority.json"
AUTHORITY_FIELDS = {
    "schema_version",
    "authority_scope",
    "effective_candidate_version",
    "base_file",
    "patch_file",
    "prospective_eligible",
}


def full_refs(value: Any):
    if isinstance(value, dict):
        if set(value) == {"object_id", "content_sha256"}:
            yield value
            return
        for member in value.values():
            yield from full_refs(member)
    elif isinstance(value, list):
        for member in value:
            yield from full_refs(member)


def _load_patch_chain(base_path: Path, patch_path: Path) -> list[tuple[Path, dict[str, Any]]]:
    expected_base = base_path.name
    seen: set[Path] = set()

    def load_one(path: Path) -> list[tuple[Path, dict[str, Any]]]:
        resolved = path.resolve()
        if resolved in seen:
            raise ValueError("candidate patch predecessor cycle or duplicate")
        seen.add(resolved)

        patch = json.loads(path.read_text(encoding="utf-8"))
        if patch.get("base_object_set") != expected_base:
            raise ValueError(f"patch base_object_set does not match selected base file: {path.name}")
        if patch.get("prospective_eligible") is not False:
            raise ValueError(f"candidate patch must remain non-prospective: {path.name}")

        chain: list[tuple[Path, dict[str, Any]]] = []
        predecessor = patch.get("predecessor_patch")
        if predecessor is not None:
            if not isinstance(predecessor, str) or not predecessor:
                raise ValueError("predecessor_patch must be a non-empty filename")
            predecessor_path = Path(predecessor)
            if predecessor_path.name != predecessor or predecessor_path.is_absolute():
                raise ValueError("predecessor_patch must be a sibling filename")
            chain.extend(load_one(path.parent / predecessor_path))
        chain.append((path, patch))
        return chain

    return load_one(patch_path)


def _resolve_authority_file(candidate_dir: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("authority file paths must be non-empty strings")
    relative = Path(value)
    if relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != "objects":
        raise ValueError(f"unsafe authority path: {value}")
    resolved = (candidate_dir / relative).resolve()
    try:
        resolved.relative_to(candidate_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"unsafe authority path: {value}") from exc
    if not resolved.is_file():
        raise ValueError(f"authority file missing: {value}")
    return resolved


def resolve_candidate_authority(authority_path: Path) -> tuple[Path, Path]:
    if not authority_path.is_file():
        raise ValueError(f"authority declaration missing: {authority_path}")
    try:
        declaration = json.loads(authority_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed authority declaration: {authority_path}") from exc
    if not isinstance(declaration, dict) or set(declaration) != AUTHORITY_FIELDS:
        raise ValueError("malformed authority declaration fields")
    if declaration["schema_version"] != "1.0":
        raise ValueError("unsupported authority declaration schema_version")
    if declaration["authority_scope"] != "PRE_GENESIS_CANDIDATE_SELECTION_ONLY":
        raise ValueError("invalid authority declaration scope")
    if declaration["prospective_eligible"] is not False:
        raise ValueError("authority declaration must remain non-prospective")
    version = declaration["effective_candidate_version"]
    if not isinstance(version, str) or not version:
        raise ValueError("effective_candidate_version must be a non-empty string")

    candidate_dir = authority_path.parent
    base_path = _resolve_authority_file(candidate_dir, declaration["base_file"])
    patch_path = _resolve_authority_file(candidate_dir, declaration["patch_file"])
    try:
        patch = json.loads(patch_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed authority patch: {patch_path.name}") from exc
    if not isinstance(patch, dict):
        raise ValueError(f"malformed authority patch: {patch_path.name}")
    if patch.get("candidate_version") != version:
        raise ValueError("authority candidate version mismatch")
    if patch.get("base_object_set") != base_path.name:
        raise ValueError("authority patch base mismatch")
    return base_path, patch_path


def materialize_candidate_inventory(
    base_path: Path,
    patch_path: Path,
    *,
    effective: bool = False,
) -> dict[str, Any]:
    base = json.loads(base_path.read_text(encoding="utf-8"))
    patch_chain = _load_patch_chain(base_path, patch_path)

    objects = base.get("objects")
    if not isinstance(objects, list):
        raise ValueError("base object set must contain an objects list")

    index: dict[str, dict[str, Any]] = {}
    for obj in objects:
        object_id = obj.get("object_id")
        if not isinstance(object_id, str) or object_id in index:
            raise ValueError("base object ids must be unique strings")
        if not verify_sealed_object(obj):
            raise ValueError(f"invalid sealed base object: {object_id}")
        index[object_id] = obj

    for current_patch_path, patch in patch_chain:
        for retirement in patch.get("retire_objects", []):
            if not isinstance(retirement, dict):
                raise ValueError(f"retire_objects entry must be an object: {current_patch_path.name}")
            object_id = retirement.get("object_id")
            expected_hash = retirement.get("retires_content_sha256")
            current = index.get(object_id)
            if current is None:
                raise ValueError(f"retirement target missing: {object_id}")
            if current.get("content_sha256") != expected_hash:
                raise ValueError(f"retirement predecessor hash mismatch: {object_id}")
            del index[object_id]

        for replacement in patch.get("replace_objects", []):
            object_id = replacement["object_id"]
            current = index.get(object_id)
            if current is None:
                raise ValueError(f"replacement target missing: {object_id}")
            if current.get("content_sha256") != replacement.get("replaces_content_sha256"):
                raise ValueError(f"replacement predecessor hash mismatch: {object_id}")
            new_object = replacement["replacement"]
            if new_object.get("object_id") != object_id:
                raise ValueError(f"replacement object id mismatch: {object_id}")
            if not verify_sealed_object(new_object):
                raise ValueError(f"invalid sealed replacement: {object_id}")
            index[object_id] = new_object

        for obj in patch.get("add_objects", []):
            object_id = obj.get("object_id")
            if not isinstance(object_id, str) or object_id in index:
                raise ValueError(f"candidate add collides or lacks id: {object_id}")
            if not verify_sealed_object(obj):
                raise ValueError(f"invalid sealed added object: {object_id}")
            index[object_id] = obj

        expected_count = patch.get("effective_object_count")
        if expected_count != len(index):
            raise ValueError(
                f"effective object count mismatch after {current_patch_path.name}: "
                f"expected {expected_count}, got {len(index)}"
            )

    for obj in index.values():
        for ref in full_refs(obj):
            target = index.get(ref["object_id"])
            if target is None:
                raise ValueError(f"unclosed dependency: {ref['object_id']}")
            if target.get("content_sha256") != ref["content_sha256"]:
                raise ValueError(f"dependency hash mismatch: {ref['object_id']}")

    final_patch_path, final_patch = patch_chain[-1]
    ordered = sorted(index.values(), key=lambda obj: obj["object_id"])
    inventory_core = {
        "schema_version": "1.0",
        "candidate_version": final_patch["candidate_version"],
        "base_file": base_path.name,
        "patch_file": final_patch_path.name,
        "patch_chain": [path.name for path, _ in patch_chain],
        "effective": effective,
        "prospective_eligible": False,
        "object_count": len(ordered),
        "objects": [
            {
                "object_id": obj["object_id"],
                "object_type": obj["object_type"],
                "content_sha256": obj["content_sha256"],
            }
            for obj in ordered
        ],
    }
    inventory = dict(inventory_core)
    inventory["inventory_sha256"] = sha256_hex(canonical_json(inventory_core))
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize a non-prospective Genesis candidate inventory."
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--effective",
        action="store_true",
        help="resolve the effective candidate from candidate_lineage_authority.json",
    )
    selection.add_argument("--patch", type=Path, help="materialize exactly this candidate patch")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        if args.effective:
            if args.base is not None:
                raise ValueError("--base cannot override --effective authority")
            base_path, patch_path = resolve_candidate_authority(AUTHORITY_DECLARATION)
            effective = True
        else:
            base_path = args.base or DEFAULT_BASE
            patch_path = args.patch
            effective = False
        inventory = materialize_candidate_inventory(
            base_path,
            patch_path,
            effective=effective,
        )
    except Exception as exc:
        print(f"candidate materialization failed: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
