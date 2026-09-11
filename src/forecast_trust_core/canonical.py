from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

MAX_SAFE_INTEGER = 2**53 - 1
ASCII_TOKEN = re.compile(r"^[A-Za-z0-9._:/-]+$")
DECIMAL = re.compile(r"^(?:0|-?[1-9][0-9]*(?:\.[0-9]*[1-9])?|0\.[0-9]*[1-9]|-0\.[0-9]*[1-9])$")

class CanonicalizationError(ValueError):
    pass

def require_ascii_token(value: str, field: str = "token") -> str:
    if not value or not value.isascii() or not ASCII_TOKEN.fullmatch(value):
        raise CanonicalizationError(f"{field} must be a non-empty ASCII machine token")
    return value

def require_decimal_string(value: str, *, probability: bool = False) -> str:
    if not isinstance(value, str) or not DECIMAL.fullmatch(value) or value == "-0":
        raise CanonicalizationError("invalid canonical decimal string")
    if probability:
        if value.startswith("-"):
            raise CanonicalizationError("probability below zero")
        if value == "1" or value == "0" or value.startswith("0."):
            return value
        raise CanonicalizationError("probability above one")
    return value

def require_utc_timestamp(value: str) -> str:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise CanonicalizationError("timestamp must use YYYY-MM-DDTHH:MM:SSZ")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise CanonicalizationError("invalid UTC timestamp") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise CanonicalizationError("non-canonical UTC timestamp")
    return value

def timestamp_le(left: str, right: str) -> bool:
    require_utc_timestamp(left); require_utc_timestamp(right); return left <= right

def _validate_tree(value: Any, path: str = "$") -> None:
    if value is None:
        raise CanonicalizationError(f"null prohibited at {path}")
    if isinstance(value, bool): return
    if isinstance(value, int):
        if abs(value) > MAX_SAFE_INTEGER: raise CanonicalizationError(f"integer outside interoperable range at {path}")
        return
    if isinstance(value, float): raise CanonicalizationError(f"JSON floating point prohibited at {path}")
    if isinstance(value, str):
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value): raise CanonicalizationError(f"unpaired surrogate prohibited at {path}")
        return
    if isinstance(value, list):
        for idx, member in enumerate(value): _validate_tree(member, f"{path}[{idx}]")
        return
    if isinstance(value, dict):
        for key, member in value.items():
            if not isinstance(key, str) or not key.isascii(): raise CanonicalizationError(f"object keys must be ASCII at {path}")
            _validate_tree(member, f"{path}.{key}")
        return
    raise CanonicalizationError(f"unsupported type {type(value)!r} at {path}")

def canonical_json(value: Any) -> bytes:
    _validate_tree(value)
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_hex(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def content_hash(value: Any) -> str: return sha256_hex(canonical_json(value))

def sorted_refs(refs: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    normalized = [dict(ref) for ref in refs]
    for ref in normalized: validate_ref(ref)
    return sorted(normalized, key=lambda r: (r["object_id"], r["content_sha256"]))

def validate_ref(ref: Mapping[str, Any]) -> None:
    if set(ref) != {"object_id", "content_sha256"}: raise CanonicalizationError("reference must contain object_id and content_sha256 only")
    require_ascii_token(ref["object_id"], "object_id")
    digest = ref["content_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise CanonicalizationError("content_sha256 must be 64 lowercase hex characters")

def seal_object(payload: Mapping[str, Any], *, object_type: str, stable_context: str, semantic_id: str | None = None) -> dict[str, Any]:
    require_ascii_token(object_type, "object_type"); require_ascii_token(stable_context, "stable_context")
    forbidden = {"object_id", "payload_sha256", "content_sha256"} & set(payload)
    if forbidden: raise CanonicalizationError(f"payload contains derived fields: {sorted(forbidden)}")
    base = dict(payload); base["object_type"] = object_type
    payload_sha = content_hash(base)
    object_id = semantic_id or f"{object_type.lower()}:{stable_context}:{payload_sha[:12]}"
    require_ascii_token(object_id, "object_id")
    final_without_content = dict(base); final_without_content["object_id"] = object_id; final_without_content["payload_sha256"] = payload_sha
    final = dict(final_without_content); final["content_sha256"] = content_hash(final_without_content); return final

def verify_sealed_object(obj: Mapping[str, Any]) -> bool:
    required = {"object_type", "object_id", "payload_sha256", "content_sha256"}
    if not required.issubset(obj): return False
    try:
        require_ascii_token(obj["object_type"], "object_type"); require_ascii_token(obj["object_id"], "object_id")
        without_content = {k: v for k, v in obj.items() if k != "content_sha256"}; expected_content = content_hash(without_content)
        payload = {k: v for k, v in obj.items() if k not in {"object_id", "payload_sha256", "content_sha256"}}; expected_payload = content_hash(payload)
    except CanonicalizationError: return False
    return expected_content == obj["content_sha256"] and expected_payload == obj["payload_sha256"]

def parse_json_strict(text: str) -> Any:
    def pairs_hook(pairs):
        out = {}
        for key, value in pairs:
            if key in out: raise CanonicalizationError(f"duplicate JSON key: {key}")
            out[key] = value
        return out
    def bad_constant(value): raise CanonicalizationError(f"non-standard JSON constant: {value}")
    try: value = json.loads(text, object_pairs_hook=pairs_hook, parse_constant=bad_constant)
    except CanonicalizationError: raise
    except (json.JSONDecodeError, ValueError) as exc: raise CanonicalizationError("invalid JSON") from exc
    _validate_tree(value); return value
