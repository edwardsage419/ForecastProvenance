"""Fixed synthetic reducer facts; no source reconstruction or acceptance adapter.

Literal expectations catch vacuous PASS, overwritten blockers, coverage padding,
identity substitution, duplicate reduction, and unsupported exclusions.
"""
from dataclasses import replace
import importlib
import importlib.util

import pytest

from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.core import Check


SUBJECT = ExactRef("synthetic:manifest:v1", "a" * 64)
SOURCE = ExactRef("synthetic:source:v1", "b" * 64)
SCOPE = ExactRef("synthetic:scope:v1", "c" * 64)
PROOF = ExactRef("synthetic:coverage:v1", "d" * 64)
OTHER = ExactRef("synthetic:other:v1", "e" * 64)


def api():
    # Fail as a test assertion, not a collection/environment import error.
    assert importlib.util.find_spec("forecast_trust_core.g10_replay_v1") is not None, (
        "T01 reducer API is not implemented"
    )
    return importlib.import_module("forecast_trust_core.g10_replay_v1")


def vector(m, *, indexes=(0, 1, 2)):
    basis = m.ReplayBasis(
        mode="SYNTHETIC_MODEL", project="synthetic-project", claim="G10",
        stage="PRE_GENESIS", subject=SUBJECT, root_ref=SOURCE, rule_ref=SOURCE,
        scope_ref=SCOPE, effective_ref=SOURCE, source_selection_rule_ref=SOURCE,
        historical_rule_ref=SOURCE, workflow_rule_ref=SOURCE, profile=(SOURCE,),
    )
    keys = (
        m.PredicateKey("P07", SUBJECT, "acceptance", "synthetic-boundary"),
        m.PredicateKey("P22", SUBJECT, "findings", "synthetic-boundary"),
        m.PredicateKey("P10", SUBJECT, "local-validation", "synthetic-boundary"),
    )
    keys = tuple(keys[i] for i in indexes)
    proof = m.CompletenessProof(status="PASS", basis=basis, evidence_refs=(PROOF,),
                                mandatory_set_identity=m.mandatory_set_identity(keys))
    rows = tuple(m.PredicateResult(
        key=k, basis=basis, source_type="SYNTHETIC_REQUIREMENT", source_ref=SOURCE,
        source_location="/synthetic/clause", requirement_ids=("synthetic-obligation",),
        method_ref=SOURCE, implementation_ref=SOURCE, input_refs=(SUBJECT,),
        raw_result="VALID", normalized="PASS", applicability="APPLICABLE",
        reason_codes=("SYNTHETIC_PASS",), model_seam=True,
    ) for k in keys)
    return m.G10ReducerInput(
        basis=basis, expected_mandatory_keys=keys, source_universe=proof,
        requirement_coverage=proof, predicate_expansion=proof, observed_results=rows,
    )


def with_row(v, index, **updates):
    rows = list(v.observed_results)
    rows[index] = replace(rows[index], **updates)
    return replace(v, observed_results=tuple(rows))


def coverage(result):
    return next(c for c in result.coverage_diagnostics if c.check_id == "RESULT_COVERAGE_COMPLETE")


@pytest.mark.parametrize("count", [0, 1, 2])
def test_empty_or_partial_raw_vector_fails(count):
    m = api()
    v = vector(m)
    result = m._aggregate_g10(replace(v, observed_results=v.observed_results[:count]))
    assert result.overall == "FAIL"
    assert coverage(result).status == "FAIL"
    assert result.raw_results == v.observed_results[:count]


def test_fail_dominates_unknown():
    m = api()
    v = with_row(vector(m), 0, raw_result="INVALID", normalized="FAIL")
    v = with_row(v, 1, raw_result="UNRESOLVED", normalized="UNKNOWN")
    for rows in (v.observed_results, tuple(reversed(v.observed_results))):
        result = m._aggregate_g10(replace(v, observed_results=rows))
        assert result.overall == "FAIL"
        assert result.raw_results == rows
        assert {r.normalized for r in result.raw_results} == {"FAIL", "UNKNOWN", "PASS"}


def test_material_unknown_never_verified():
    m = api()
    v = with_row(vector(m), 0, raw_result="UNRESOLVED", normalized="UNKNOWN")
    result = m._aggregate_g10(v)
    assert result.overall == "UNKNOWN"
    assert result.raw_results[0].raw_result == "UNRESOLVED"
    assert result.raw_results[0].normalized == "UNKNOWN"
    assert coverage(result).status == "PASS"
    assert result.prospective_eligible is False


@pytest.mark.parametrize("status", ["FAIL", "UNKNOWN", "PASS", "NOT_APPLICABLE"])
def test_duplicate_conflicting_result_fails(status):
    m = api()
    v = vector(m)
    duplicate = replace(v.observed_results[0], normalized=status, raw_result=status)
    for rows in (v.observed_results + (duplicate,), (duplicate,) + v.observed_results):
        result = m._aggregate_g10(replace(v, observed_results=rows))
        assert result.overall == "FAIL"
        assert coverage(result).status == "FAIL"
        assert result.raw_results == rows
        assert len(result.raw_results) == 4


def test_diagnostic_padding_does_not_erase_coverage_failure():
    m = api()
    v = vector(m)
    v = replace(v, observed_results=v.observed_results[1:], optional_diagnostics=(
        Check("P07", "UNKNOWN", "SUPPLEMENTAL_DIAGNOSTIC"),
        Check("RESULT_COVERAGE_COMPLETE", "PASS", "CALLER_PADDING"),
    ))
    result = m._aggregate_g10(v)
    assert result.overall == "FAIL"
    assert coverage(result).status == "FAIL"
    assert result.raw_results == v.observed_results
    assert len(result.raw_results) == 2
    missing = [r for r in result.records if r.key == v.expected_mandatory_keys[0]]
    assert len(missing) == 1 and missing[0].normalized == "UNKNOWN"
    assert result.optional_diagnostics == v.optional_diagnostics


@pytest.mark.parametrize("exclusion_status,want", [(None, "UNKNOWN"), ("UNKNOWN", "UNKNOWN"), ("FAIL", "FAIL"), ("PASS", "PASS")])
def test_na_requires_verified_exclusion(exclusion_status, want):
    m = api()
    v = with_row(vector(m), 0, normalized="NOT_APPLICABLE", raw_result="NOT_APPLICABLE",
                 applicability="NOT_APPLICABLE", exclusion_clause_ref=SOURCE,
                 exclusion_clause_location="/exclusion", exclusion_fact_refs=(PROOF,),
                 exclusion_result=exclusion_status)
    assert m._aggregate_g10(v).overall == want


@pytest.mark.parametrize("field,value", [
    ("exclusion_clause_ref", None), ("exclusion_clause_location", ""),
    ("exclusion_fact_refs", ()),
])
def test_na_missing_rule_or_facts_stays_unknown(field, value):
    m = api()
    v = with_row(vector(m), 0, normalized="NOT_APPLICABLE", applicability="NOT_APPLICABLE",
                 exclusion_clause_ref=SOURCE, exclusion_clause_location="/exclusion",
                 exclusion_fact_refs=(PROOF,), exclusion_result="PASS")
    v = with_row(v, 0, **{field: value})
    assert m._aggregate_g10(v).overall == "UNKNOWN"


def test_complete_vector_passes_only_with_four_completeness_proofs():
    m = api()
    v = vector(m)
    result = m._aggregate_g10(v)
    assert result.overall == "PASS"
    assert coverage(result).status == "PASS"
    assert result.raw_results == v.observed_results
    assert result.records == v.observed_results
    assert result.basis == v.basis
    assert result.real_genesis_readiness == "NOT_ESTABLISHED"
    assert result.prospective_eligible is False
    assert result.claim_label == "SYNTHETIC_MODEL:G10_REDUCER_ONLY"
    assert v.expected_mandatory_keys == tuple(r.key for r in v.observed_results)


@pytest.mark.parametrize("field", ["source_universe", "requirement_coverage", "predicate_expansion"])
@pytest.mark.parametrize("status,want", [(None, "UNKNOWN"), ("UNKNOWN", "UNKNOWN"), ("FAIL", "FAIL")])
def test_missing_or_nonpass_upstream_completeness_proof(field, status, want):
    m = api()
    v = vector(m)
    proof = None if status is None else replace(getattr(v, field), status=status)
    assert m._aggregate_g10(replace(v, **{field: proof})).overall == want


@pytest.mark.parametrize("field", ["source_universe", "requirement_coverage", "predicate_expansion"])
def test_completeness_pass_without_retained_binding_evidence_is_unknown(field):
    m = api()
    v = vector(m)
    assert m._aggregate_g10(replace(v, **{field: replace(getattr(v, field), evidence_refs=())})).overall == "UNKNOWN"


def test_result_coverage_unestablished_when_mandatory_universe_unknown():
    m = api()
    v = vector(m)
    v = replace(v, predicate_expansion=replace(v.predicate_expansion, status="UNKNOWN"),
                observed_results=v.observed_results[1:])
    result = m._aggregate_g10(v)
    assert result.overall == "UNKNOWN"
    assert coverage(result).status == "UNKNOWN"


@pytest.mark.parametrize("expected", [None, ()])
def test_empty_or_unknown_mandatory_universe_cannot_pass(expected):
    m = api()
    v = vector(m)
    result = m._aggregate_g10(replace(v, expected_mandatory_keys=expected, observed_results=()))
    assert result.overall == ("UNKNOWN" if expected is None else "FAIL")


def test_reject_with_local_valid_fails():
    m = api()
    v = with_row(vector(m), 0, raw_result="REJECT", normalized="FAIL", reason_codes=("ACCEPTANCE_REJECTED",))
    result = m._aggregate_g10(v)
    assert result.overall == "FAIL"
    assert result.raw_results[0].raw_result == "REJECT"
    assert result.raw_results[0].normalized == "FAIL"
    assert result.raw_results[2].raw_result == "VALID"
    assert result.raw_results[2].normalized == "PASS"


def test_blocking_finding_with_local_pass_fails():
    m = api()
    v = with_row(vector(m), 1, raw_result="APPLICABLE_BLOCKING_FINDING_PRESENT", normalized="FAIL",
                 blocking=True, finding_refs=(OTHER,), reason_codes=("BLOCKING_FINDING",))
    result = m._aggregate_g10(v)
    assert result.overall == "FAIL"
    assert result.raw_results[1].blocking is True
    assert result.raw_results[1].raw_result == "APPLICABLE_BLOCKING_FINDING_PRESENT"
    assert result.raw_results[2].normalized == "PASS"
    assert OTHER in result.findings


@pytest.mark.parametrize("field,value", [("scope_ref", OTHER), ("profile", (OTHER,)), ("project", "other"), ("stage", "OTHER")])
def test_wrong_result_binding_fails(field, value):
    m = api()
    v = vector(m)
    v = with_row(v, 0, basis=replace(v.basis, **{field: value}))
    assert m._aggregate_g10(v).overall == "FAIL"


def test_wrong_proof_binding_fails():
    m = api()
    v = vector(m)
    proof = replace(v.source_universe, basis=replace(v.basis, scope_ref=OTHER))
    assert m._aggregate_g10(replace(v, source_universe=proof)).overall == "FAIL"


def test_missing_binding_remains_unknown():
    m = api()
    v = vector(m)
    assert m._aggregate_g10(with_row(v, 0, basis=None)).overall == "UNKNOWN"
    assert m._aggregate_g10(replace(v, basis=replace(v.basis, root_ref=None))).overall == "UNKNOWN"


def test_missing_whole_predicate_identity_fails_even_with_same_count():
    m = api()
    v = vector(m)
    unknown_key = replace(v.observed_results[0].key, predicate_id="UNEXPECTED_PREDICATE")
    result = m._aggregate_g10(with_row(v, 0, key=unknown_key))
    assert result.overall == "FAIL"
    assert coverage(result).status == "FAIL"


@pytest.mark.parametrize("field,value", [("subject", OTHER), ("subject", ExactRef(SUBJECT.object_id, "f" * 64)),
                                         ("role", "other"), ("historical_boundary", "other-boundary")])
def test_exact_predicate_identity_substitution_fails(field, value):
    m = api()
    v = vector(m)
    key = replace(v.observed_results[0].key, **{field: value})
    assert m._aggregate_g10(with_row(v, 0, key=key)).overall == "FAIL"


def test_different_subjects_at_same_boundary_are_distinct_instances():
    m = api()
    v = vector(m)
    key = replace(v.expected_mandatory_keys[0], subject=OTHER)
    row = replace(v.observed_results[0], key=key)
    keys = v.expected_mandatory_keys + (key,)
    # This positive case deliberately establishes a new universe, so its proofs
    # explicitly bind that expanded set rather than reuse the old set's proofs.
    proof = replace(v.predicate_expansion, mandatory_set_identity=m.mandatory_set_identity(keys))
    result = m._aggregate_g10(replace(v, expected_mandatory_keys=keys,
                                    observed_results=v.observed_results + (row,),
                                    source_universe=proof, requirement_coverage=proof,
                                    predicate_expansion=proof))
    assert result.overall == "PASS"
    assert len(result.raw_results) == 4


def test_duplicate_expected_key_fails():
    m = api()
    v = vector(m)
    assert m._aggregate_g10(replace(v, expected_mandatory_keys=v.expected_mandatory_keys + v.expected_mandatory_keys[:1])).overall == "FAIL"


@pytest.mark.parametrize("status", ["VALID", "VERIFIED", True, None])
def test_invalid_normalized_value_cannot_become_pass(status):
    m = api()
    v = with_row(vector(m), 0, normalized=status)
    assert m._aggregate_g10(v).overall == "FAIL"


def test_unknown_applicability_cannot_pass():
    m = api()
    assert m._aggregate_g10(with_row(vector(m), 0, applicability="UNKNOWN")).overall == "UNKNOWN"


def test_fail_survives_unestablished_completeness():
    m = api()
    v = with_row(vector(m), 0, normalized="FAIL", raw_result="REJECT")
    assert m._aggregate_g10(replace(v, source_universe=None)).overall == "FAIL"


@pytest.mark.parametrize("field,value", [("source_ref", None), ("source_location", ""),
                                         ("requirement_ids", ()), ("method_ref", None),
                                         ("implementation_ref", None), ("input_refs", ())])
def test_pass_without_required_provenance_is_unknown(field, value):
    m = api()
    assert m._aggregate_g10(with_row(vector(m), 0, **{field: value})).overall == "UNKNOWN"


def test_applicable_blocking_fact_cannot_be_laundered_by_normalized_pass():
    m = api()
    v = with_row(vector(m), 1, blocking=True, normalized="PASS", finding_refs=(OTHER,))
    assert m._aggregate_g10(v).overall == "FAIL"


def test_material_false_does_not_waive_mandatory_unknown():
    m = api()
    assert m._aggregate_g10(with_row(vector(m), 0, normalized="UNKNOWN", material=False)).overall == "UNKNOWN"


def test_synthetic_seam_cannot_pass_in_public_evidence_mode():
    m = api()
    v = vector(m)
    basis = replace(v.basis, mode="PUBLIC_EVIDENCE")
    v = replace(v, basis=basis, observed_results=tuple(replace(r, basis=basis) for r in v.observed_results),
                source_universe=replace(v.source_universe, basis=basis),
                requirement_coverage=replace(v.requirement_coverage, basis=basis),
                predicate_expansion=replace(v.predicate_expansion, basis=basis))
    assert m._aggregate_g10(v).overall == "UNKNOWN"


@pytest.mark.parametrize("status", ["VALID", True, None, "NOT_APPLICABLE"])
def test_invalid_completeness_status_fails_closed(status):
    m = api()
    v = vector(m)
    assert m._aggregate_g10(replace(v, source_universe=replace(v.source_universe, status=status))).overall == "FAIL"


@pytest.mark.parametrize("raw_result", [None, ""])
def test_missing_local_raw_result_is_unknown(raw_result):
    m = api()
    v = with_row(vector(m), 0, raw_result=raw_result, normalized="PASS")
    result = m._aggregate_g10(v)
    assert result.overall == "UNKNOWN"
    assert result.raw_results[0].raw_result == raw_result
    assert result.raw_results[0].normalized == "PASS"
    assert coverage(result).status == "PASS"


def test_explicit_fail_still_dominates_missing_local_raw_result():
    m = api()
    v = with_row(vector(m), 0, raw_result=None, normalized="PASS")
    v = with_row(v, 1, raw_result="INVALID", normalized="FAIL")
    assert m._aggregate_g10(v).overall == "FAIL"


@pytest.mark.parametrize("with_blockers", [False, True])
def test_unchanged_completeness_proofs_cannot_pass_simultaneous_set_shrink(with_blockers):
    m = api()
    v = vector(m)
    if with_blockers:
        v = with_row(v, 0, raw_result="REJECT", normalized="FAIL")
        v = with_row(v, 1, raw_result="BLOCKING", normalized="FAIL", blocking=True)
    assert m._aggregate_g10(v).overall == ("FAIL" if with_blockers else "PASS")
    shrunk = replace(v, expected_mandatory_keys=v.expected_mandatory_keys[2:],
                     observed_results=v.observed_results[2:])
    assert shrunk.basis is v.basis
    for field in ("source_universe", "requirement_coverage", "predicate_expansion"):
        assert getattr(shrunk, field) is getattr(v, field)
    result = m._aggregate_g10(shrunk)
    assert result.overall == "FAIL"
    assert result.raw_results == shrunk.observed_results


def test_small_universe_proofs_cannot_authorize_larger_expected_set():
    m = api()
    small, full = vector(m, indexes=(0,)), vector(m)
    assert m._aggregate_g10(small).overall == "PASS"
    expanded = replace(full, source_universe=small.source_universe,
                       requirement_coverage=small.requirement_coverage,
                       predicate_expansion=small.predicate_expansion)
    assert expanded.basis == small.basis
    assert expanded.source_universe is small.source_universe
    assert expanded.source_universe.evidence_refs == full.source_universe.evidence_refs
    assert m._aggregate_g10(expanded).overall == "FAIL"


def test_mandatory_set_identity_and_binding_are_order_independent():
    m = api()
    assert callable(getattr(m, "mandatory_set_identity", None)), "Exact-set identity is missing"
    v = vector(m)
    reordered = (v.expected_mandatory_keys[2], v.expected_mandatory_keys[0], v.expected_mandatory_keys[1])
    assert m.mandatory_set_identity(reordered) == m.mandatory_set_identity(v.expected_mandatory_keys)
    result = m._aggregate_g10(replace(v, expected_mandatory_keys=reordered,
                                      observed_results=tuple(reversed(v.observed_results))))
    assert result.overall == "PASS"
    assert result.mandatory_set_identity == v.predicate_expansion.mandatory_set_identity


@pytest.mark.parametrize("field,value", [
    ("predicate_id", "OTHER_PREDICATE"),
    ("subject", ExactRef(SUBJECT.object_id, "f" * 64)),
    ("subject", ExactRef("synthetic:other-manifest:v1", SUBJECT.content_sha256)),
    ("role", "other-role"),
    ("historical_boundary", "other-boundary"),
])
def test_exact_set_substitution_with_same_count_and_old_proofs_fails(field, value):
    m = api()
    v = vector(m)
    key = replace(v.expected_mandatory_keys[0], **{field: value})
    changed = with_row(v, 0, key=key)
    changed = replace(changed, expected_mandatory_keys=(key,) + v.expected_mandatory_keys[1:])
    assert m._aggregate_g10(changed).overall == "FAIL"
    assert m.mandatory_set_identity(changed.expected_mandatory_keys) != m.mandatory_set_identity(v.expected_mandatory_keys)


@pytest.mark.parametrize("field", ["source_universe", "requirement_coverage", "predicate_expansion"])
def test_each_completeness_proof_must_bind_current_exact_set(field):
    m = api()
    v = vector(m)
    small = vector(m, indexes=(0,))
    result = m._aggregate_g10(replace(v, **{field: getattr(small, field)}))
    assert result.overall == "FAIL"
    assert next(c for c in result.coverage_diagnostics if c.status == "FAIL")


@pytest.mark.parametrize("field", ["source_universe", "requirement_coverage", "predicate_expansion"])
@pytest.mark.parametrize("identity", [None, ""])
def test_missing_exact_set_binding_stays_unknown(field, identity):
    m = api()
    v = vector(m)
    proof = getattr(v, field)
    assert hasattr(proof, "mandatory_set_identity"), "Completeness proof lacks exact-set binding"
    result = m._aggregate_g10(replace(v, **{field: replace(proof, mandatory_set_identity=identity)}))
    assert result.overall == "UNKNOWN"


def test_valid_exact_set_binding_allows_only_scoped_reducer_pass():
    m = api()
    v = vector(m)
    assert hasattr(v.predicate_expansion, "mandatory_set_identity"), "Completeness proof lacks exact-set binding"
    result = m._aggregate_g10(v)
    assert result.overall == "PASS"
    assert result.mandatory_set_identity == v.predicate_expansion.mandatory_set_identity
    assert result.real_genesis_readiness == "NOT_ESTABLISHED"
    assert result.prospective_eligible is False


def test_exact_set_binding_does_not_substitute_for_completeness_evidence():
    m = api()
    v = vector(m)
    assert hasattr(v.source_universe, "mandatory_set_identity"), "Completeness proof lacks exact-set binding"
    v = replace(v, source_universe=replace(v.source_universe, evidence_refs=()))
    assert m._aggregate_g10(v).overall == "UNKNOWN"


def test_explicit_fail_dominates_missing_exact_set_binding():
    m = api()
    v = with_row(vector(m), 0, raw_result="REJECT", normalized="FAIL")
    assert hasattr(v.source_universe, "mandatory_set_identity"), "Completeness proof lacks exact-set binding"
    v = replace(v, source_universe=replace(v.source_universe, mandatory_set_identity=None))
    assert m._aggregate_g10(v).overall == "FAIL"


def test_exact_binding_to_empty_set_does_not_waive_nonempty_universe_gate():
    m = api()
    v = vector(m, indexes=())
    result = m._aggregate_g10(v)
    assert result.overall == "FAIL"
    assert coverage(result).status == "FAIL"
    assert all(c.status == "PASS" for c in result.coverage_diagnostics[:-1])
