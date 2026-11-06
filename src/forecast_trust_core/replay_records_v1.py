"""Formatting only: adapters must supply actual native checks, never authority."""
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .authority_primitives_v1 import ExactRef
from .canonical import canonical_json, sha256_hex
from .core import Check
from .g10_replay_v1 import PredicateResult


@dataclass(frozen=True)
class NativeReplay:
    checks: tuple[Check, ...]
    input_refs: tuple[ExactRef, ...]
    model_seam: bool = False
    finding_refs: tuple[ExactRef, ...] = ()


def reduce_checks(checks):
    return "FAIL" if any(c.status == "FAIL" for c in checks) else "UNKNOWN" if not checks or any(c.status != "PASS" for c in checks) else "PASS"


def emit_records(universe, native: Mapping[str, NativeReplay], implementation_path: str):
    """Private lane formatter. It performs no scientific/trust verification."""
    path = Path(implementation_path)
    impl = ExactRef("development:implementation:" + path.stem, sha256_hex(path.read_bytes()))
    rows = []
    for clause in universe.requirements:
        fact = native.get(clause.check)
        if fact is None:
            continue  # This adapter does not own this semantic; T09 covers M.
        status = reduce_checks(fact.checks)
        raw = canonical_json({"checks": [{"id": c.check_id, "status": c.status, "reason": c.reason_code} for c in fact.checks]}).decode()
        for key in clause.keys:
            rows.append(PredicateResult(key, universe.basis, "FIXED_MODEL_RULE", clause.source_ref,
                                        clause.source_location, (clause.requirement_id,), clause.source_ref,
                                        impl, fact.input_refs or (clause.source_ref,), raw, status,
                                        "APPLICABLE", tuple(c.reason_code for c in fact.checks),
                                        fact.finding_refs, blocking=status == "FAIL" and bool(fact.finding_refs),
                                        model_seam=fact.model_seam))
    return tuple(rows)
