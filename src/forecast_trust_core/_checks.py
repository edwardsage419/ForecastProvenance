from __future__ import annotations
from typing import Any, Mapping, Sequence
from .core import Check

def check(check_id: str, passed: bool | None, reason: str) -> Check:
    return Check(check_id, "PASS" if passed is True else "UNKNOWN" if passed is None else "FAIL", reason)

def required(obj: Mapping[str, Any], fields: Sequence[str], prefix: str) -> list[Check]:
    return [check(f"{prefix}.{field}", field in obj, "OK" if field in obj else "MISSING_REQUIRED_FIELD") for field in fields]
