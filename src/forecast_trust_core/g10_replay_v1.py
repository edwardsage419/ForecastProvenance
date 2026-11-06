"""T01 internal aggregation machinery, not a protocol or full-claim entry point.

Upstream logic must independently establish the mandatory universe and the
first three completeness facts. This module only reduces supplied typed facts;
it does not reconstruct sources, verify acceptance signatures, or confer trust.
Mandatory-set digests bind those facts to their aggregation subject; they do
not establish the universe's completeness, authority, or applicability.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields
from typing import Literal

from .authority_primitives_v1 import ExactRef
from .canonical import canonical_json, sha256_hex
from .core import Check, Result, aggregate


Status = Literal["FAIL", "UNKNOWN", "PASS"]
PredicateStatus = Literal["FAIL", "UNKNOWN", "PASS", "NOT_APPLICABLE"]
Applicability = Literal["APPLICABLE", "UNKNOWN", "NOT_APPLICABLE"]


@dataclass(frozen=True)
class ReplayBasis:
    mode: Literal["SYNTHETIC_MODEL", "PUBLIC_EVIDENCE"]
    project: str
    claim: str
    stage: str
    subject: ExactRef | None
    root_ref: ExactRef | None
    rule_ref: ExactRef | None
    scope_ref: ExactRef | None
    effective_ref: ExactRef | None
    source_selection_rule_ref: ExactRef | None
    historical_rule_ref: ExactRef | None
    workflow_rule_ref: ExactRef | None
    profile: tuple[ExactRef, ...]


@dataclass(frozen=True)
class PredicateKey:
    predicate_id: str
    subject: ExactRef
    role: str
    historical_boundary: str


def mandatory_set_identity(keys: tuple[PredicateKey, ...]) -> str:
    """Integrity binding for exact set membership, never a requirement source.

    Canonical rows contain predicate ID, subject ID/hash, role, and boundary.
    Ordering and multiplicity do not change set identity; the reducer separately
    rejects duplicate expected keys and duplicate raw terminal results.
    """
    members = sorted({(
        key.predicate_id, key.subject.object_id, key.subject.content_sha256,
        key.role, key.historical_boundary,
    ) for key in keys})
    return sha256_hex(b"FPP_G10_MANDATORY_SET_V1\x00" + canonical_json(
        [list(member) for member in members]
    ))


@dataclass(frozen=True)
class CompletenessProof:
    status: Status
    basis: ReplayBasis | None
    evidence_refs: tuple[ExactRef, ...]
    # Upstream supplies the set binding; absent binding cannot establish PASS.
    mandatory_set_identity: str | None = None


@dataclass(frozen=True)
class PredicateResult:
    key: PredicateKey
    basis: ReplayBasis | None
    source_type: str
    source_ref: ExactRef | None
    source_location: str
    requirement_ids: tuple[str, ...]
    method_ref: ExactRef | None
    implementation_ref: ExactRef | None
    input_refs: tuple[ExactRef, ...]
    raw_result: str | None
    normalized: PredicateStatus
    applicability: Applicability
    reason_codes: tuple[str, ...] = ()
    finding_refs: tuple[ExactRef, ...] = ()
    material: bool = True
    blocking: bool = False
    model_seam: bool = False
    exclusion_clause_ref: ExactRef | None = None
    exclusion_clause_location: str = ""
    exclusion_fact_refs: tuple[ExactRef, ...] = ()
    exclusion_result: Status | None = None


@dataclass(frozen=True)
class G10ReducerInput:
    basis: ReplayBasis
    expected_mandatory_keys: tuple[PredicateKey, ...] | None
    source_universe: CompletenessProof | None
    requirement_coverage: CompletenessProof | None
    predicate_expansion: CompletenessProof | None
    observed_results: tuple[PredicateResult, ...]
    # Non-decisive supplemental diagnostics cannot supply mandatory result rows.
    optional_diagnostics: tuple[Check, ...] = ()


@dataclass(frozen=True)
class ReplayResult:
    overall: Status
    basis: ReplayBasis
    mandatory_set_identity: str | None
    raw_results: tuple[PredicateResult, ...]
    records: tuple[PredicateResult, ...]
    coverage_diagnostics: tuple[Check, ...]
    optional_diagnostics: tuple[Check, ...]
    findings: tuple[ExactRef, ...]
    claim_label: str
    real_genesis_readiness: Literal["NOT_ESTABLISHED"] = "NOT_ESTABLISHED"
    prospective_eligible: Literal[False] = False


def _basis_status(actual: ReplayBasis | None, expected: ReplayBasis) -> Status:
    if actual is None:
        return "UNKNOWN"
    missing = False
    for field in fields(ReplayBasis):
        value, wanted = getattr(actual, field.name), getattr(expected, field.name)
        if value in (None, "", ()) or wanted in (None, "", ()):
            missing = True
        elif value != wanted:
            return "FAIL"
    if actual.mode not in ("SYNTHETIC_MODEL", "PUBLIC_EVIDENCE"):
        return "FAIL"
    return "UNKNOWN" if missing else "PASS"


def _proof_check(name: str, proof: CompletenessProof | None, basis: ReplayBasis,
                 expected_set_identity: str | None) -> Check:
    if proof is None:
        return Check(name, "UNKNOWN", "COMPLETENESS_PROOF_MISSING")
    if proof.status not in ("FAIL", "UNKNOWN", "PASS"):
        return Check(name, "FAIL", "INVALID_COMPLETENESS_STATUS")
    binding = _basis_status(proof.basis, basis)
    if proof.status == "FAIL" or binding == "FAIL":
        return Check(name, "FAIL", "COMPLETENESS_FAILURE_OR_WRONG_BINDING")
    if (proof.mandatory_set_identity not in (None, "")
            and expected_set_identity is not None
            and proof.mandatory_set_identity != expected_set_identity):
        return Check(name, "FAIL", "MANDATORY_SET_BINDING_MISMATCH")
    if proof.mandatory_set_identity in (None, "") or expected_set_identity is None:
        return Check(name, "UNKNOWN", "MANDATORY_SET_BINDING_NOT_ESTABLISHED")
    if proof.status == "UNKNOWN" or binding == "UNKNOWN" or not proof.evidence_refs:
        return Check(name, "UNKNOWN", "COMPLETENESS_NOT_ESTABLISHED")
    return Check(name, "PASS", "COMPLETENESS_ESTABLISHED_BY_UPSTREAM")


def _predicate_check(row: PredicateResult, basis: ReplayBasis) -> Check:
    name = row.key.predicate_id
    if row.normalized not in ("FAIL", "UNKNOWN", "PASS", "NOT_APPLICABLE"):
        return Check(name, "FAIL", "INVALID_NORMALIZED_STATUS")
    if row.applicability not in ("APPLICABLE", "UNKNOWN", "NOT_APPLICABLE"):
        return Check(name, "FAIL", "INVALID_APPLICABILITY")
    if row.normalized == "FAIL" or (row.blocking and row.applicability == "APPLICABLE"):
        return Check(name, "FAIL", "MANDATORY_FAILURE_OR_APPLICABLE_BLOCKER")
    binding = _basis_status(row.basis, basis)
    if binding == "FAIL":
        return Check(name, "FAIL", "WRONG_RESULT_BINDING")
    if row.normalized == "NOT_APPLICABLE":
        if row.exclusion_result == "FAIL":
            return Check(name, "FAIL", "EXCLUSION_FALSE")
        if row.exclusion_result not in (None, "UNKNOWN", "PASS"):
            return Check(name, "FAIL", "INVALID_EXCLUSION_STATUS")
        if row.applicability == "APPLICABLE":
            return Check(name, "FAIL", "APPLICABLE_PREDICATE_EXCLUDED")
        exclusion_verified = (
            row.applicability == "NOT_APPLICABLE"
            and row.exclusion_result == "PASS"
            and row.exclusion_clause_ref is not None
            and bool(row.exclusion_clause_location)
            and bool(row.exclusion_fact_refs)
        )
        if not exclusion_verified:
            return Check(name, "UNKNOWN", "EXCLUSION_NOT_ESTABLISHED")
    elif row.normalized == "UNKNOWN" or row.applicability != "APPLICABLE":
        # A mandatory UNKNOWN cannot be waived with a material=False flag:
        # PASS still requires every mandatory result to be PASS or justified N/A.
        return Check(name, "UNKNOWN", "MANDATORY_RESULT_OR_APPLICABILITY_UNKNOWN")
    if binding == "UNKNOWN":
        return Check(name, "UNKNOWN", "RESULT_BINDING_NOT_ESTABLISHED")
    if row.raw_result in (None, ""):
        return Check(name, "UNKNOWN", "LOCAL_RAW_RESULT_MISSING")
    if basis.mode == "PUBLIC_EVIDENCE" and row.model_seam:
        return Check(name, "UNKNOWN", "SYNTHETIC_SEAM_IS_NOT_PUBLIC_EVIDENCE")
    if not all((row.source_type, row.source_ref, row.source_location,
                row.requirement_ids, row.method_ref, row.implementation_ref, row.input_refs)):
        return Check(name, "UNKNOWN", "RESULT_PROVENANCE_NOT_ESTABLISHED")
    return Check(name, "PASS", "MANDATORY_RESULT_PASS_OR_VERIFIED_EXCLUSION")


def _aggregate_g10(reducer_input: G10ReducerInput) -> ReplayResult:
    """Pure internal reducer. A PASS describes these facts, not real readiness.

    Check raw O before adding diagnostics. In particular, UNKNOWN padding never
    repairs an already observed coverage FAIL. No result is overwritten or
    deduplicated, including equal duplicate terminal results.
    """
    basis = reducer_input.basis
    raw = reducer_input.observed_results
    expected = reducer_input.expected_mandatory_keys
    expected_set_identity = None if expected is None else mandatory_set_identity(expected)
    checks = [Check("BASIS_BINDING", _basis_status(basis, basis), "INDEPENDENT_BASIS_STATUS")]
    checks.extend((
        _proof_check("SOURCE_UNIVERSE_COMPLETE", reducer_input.source_universe, basis, expected_set_identity),
        _proof_check("CONSEQUENTIAL_REQUIREMENT_COVERAGE_COMPLETE", reducer_input.requirement_coverage, basis, expected_set_identity),
        _proof_check("PREDICATE_EXPANSION_COMPLETE", reducer_input.predicate_expansion, basis, expected_set_identity),
    ))
    universe_known = all(c.status == "PASS" for c in checks)
    counts = Counter(row.key for row in raw)
    duplicates = any(n != 1 for n in counts.values())
    expected_duplicates = expected is not None and len(set(expected)) != len(expected)
    missing = tuple(k for k in expected or () if k not in counts)
    unexpected = tuple(k for k in counts if expected is not None and k not in expected)
    bindings = tuple(_basis_status(row.basis, basis) for row in raw)
    if duplicates or expected_duplicates or "FAIL" in bindings:
        coverage = Check("RESULT_COVERAGE_COMPLETE", "FAIL", "DUPLICATE_OR_WRONG_RESULT_BINDING")
    elif expected is None or not universe_known:
        coverage = Check("RESULT_COVERAGE_COMPLETE", "UNKNOWN", "MANDATORY_UNIVERSE_NOT_ESTABLISHED")
    elif not expected or missing or unexpected:
        coverage = Check("RESULT_COVERAGE_COMPLETE", "FAIL", "EMPTY_MISSING_OR_UNEXPECTED_MANDATORY_RESULT")
    elif "UNKNOWN" in bindings:
        coverage = Check("RESULT_COVERAGE_COMPLETE", "UNKNOWN", "RESULT_BINDING_NOT_ESTABLISHED")
    else:
        coverage = Check("RESULT_COVERAGE_COMPLETE", "PASS", "EXACT_RAW_RESULT_COVERAGE")
    checks.append(coverage)

    # Only the mandatory lane and derived checks affect the verdict. Optional
    # diagnostics cannot contribute coverage or erase any mandatory result.
    reduced = aggregate(tuple(checks) + tuple(_predicate_check(r, basis) for r in raw))
    overall: Status = {
        Result.INVALID: "FAIL", Result.INELIGIBLE_TRUST_UNKNOWN: "UNKNOWN", Result.VALID: "PASS",
    }[reduced.result]
    padding = tuple(PredicateResult(
        key=k, basis=basis, source_type="REDUCER_DIAGNOSTIC", source_ref=None,
        source_location="", requirement_ids=(), method_ref=None, implementation_ref=None,
        input_refs=(), raw_result=None, normalized="UNKNOWN", applicability="UNKNOWN",
        reason_codes=("MISSING_RAW_RESULT",),
    ) for k in missing)
    return ReplayResult(
        overall=overall, basis=basis, mandatory_set_identity=expected_set_identity,
        raw_results=raw, records=raw + padding,
        coverage_diagnostics=tuple(checks), optional_diagnostics=reducer_input.optional_diagnostics,
        findings=tuple(ref for row in raw for ref in row.finding_refs),
        claim_label=f"{basis.mode}:G10_REDUCER_ONLY",
    )
