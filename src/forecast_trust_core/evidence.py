from __future__ import annotations
from typing import Any, Mapping, Sequence
from .canonical import CanonicalizationError, sorted_refs, timestamp_le, validate_ref
from .core import Result, Validation, aggregate
from ._checks import check as _check, required as _required

def validate_outcome_information_barrier(external_proof_deadline:str,outcome_information_barrier:str)->Validation:
    try: ok=timestamp_le(external_proof_deadline,outcome_information_barrier)
    except CanonicalizationError: return aggregate([_check("target.outcome_barrier",False,"INVALID_TIMESTAMP")])
    return aggregate([_check("target.outcome_barrier",ok,"FORECAST_DEADLINE_AFTER_OUTCOME_INFORMATION_BARRIER")])

def validate_public_randomness(randomness:Mapping[str,Any],*,plan_bound:str,expected_challenge:str,expected_source_ref:Mapping[str,Any]|None=None)->Validation:
    checks=_required(randomness,("observed_external_bound","challenge","source_ref"),"randomness"); observed=randomness.get("observed_external_bound")
    after_plan=isinstance(observed,str) and plan_bound<observed
    checks.append(_check("randomness.after_plan",after_plan,"RANDOMNESS_PRECEDES_PLAN_COMMITMENT")); checks.append(_check("randomness.challenge",randomness.get("challenge")==expected_challenge,"RANDOMNESS_CHALLENGE_MISMATCH"))
    if expected_source_ref is not None: checks.append(_check("randomness.source",randomness.get("source_ref")==expected_source_ref,"PUBLIC_RANDOMNESS_SOURCE_SUBSTITUTION"))
    return aggregate(checks)

def validate_source_selection(candidates:Sequence[Mapping[str,Any]],selected_ref:Mapping[str,Any])->Validation:
    try: ordered=sorted_refs(candidates); validate_ref(selected_ref)
    except CanonicalizationError: return aggregate([_check("source.selection",False,"MALFORMED_SOURCE_REFERENCE")])
    if not ordered: return aggregate([_check("source.selection",None,"NO_ELIGIBLE_SOURCE_ARTIFACT")])
    return aggregate([_check("source.selection",selected_ref==ordered[0],"NONDETERMINISTIC_SOURCE_SELECTION")])

def validate_current_verifiability_report(report:Mapping[str,Any])->Validation: return aggregate(_required(report,("assessed_at","subject_ref","current_verifiability_state","evidence_refs"),"verifiability"))

def validate_resolution_evidence(policy:Mapping[str,Any],evidence:Mapping[str,Any])->Validation:
    rules=policy.get("rules",policy); checks=[]; expected=rules.get("vintage_selection")
    if expected is not None: checks.append(_check("resolution.vintage",evidence.get("selected_vintage")==expected,"RESOLUTION_VINTAGE_MISMATCH"))
    deadline=rules.get("resolution_deadline"); resolved=evidence.get("resolved_at")
    if deadline is not None and resolved is not None:
        try: checks.append(_check("resolution.deadline",timestamp_le(resolved,deadline),"RESOLUTION_AFTER_FROZEN_DEADLINE"))
        except CanonicalizationError: checks.append(_check("resolution.deadline",False,"INVALID_RESOLUTION_TIMESTAMP"))
    elif deadline is not None: checks.append(_check("resolution.deadline",None,"RESOLUTION_TIME_UNKNOWN"))
    return aggregate(checks)

def validate_trust_report(method:Mapping[str,Any],report:Mapping[str,Any])->Validation:
    complete=report.get("evidence_provenance_claim")=="COMPLETE"; allowed=method.get("evidence_observability_class")=="FULL_DECLARED_EXTERNAL_INPUTS"; return aggregate([_check("trust_report.observability",not complete or allowed,"OPAQUE_MODEL_PROVENANCE_OVERCLAIM")])

def validate_retrieval_accounting(required_retrieval_refs:Sequence[Mapping[str,Any]],logged_retrieval_refs:Sequence[Mapping[str,Any]])->Validation:
    try: required=sorted_refs(required_retrieval_refs); logged=sorted_refs(logged_retrieval_refs)
    except CanonicalizationError: return aggregate([_check("retrieval.refs",False,"MALFORMED_RETRIEVAL_REFERENCE")])
    if required!=logged: return Validation(Result.INELIGIBLE_TRUST_UNKNOWN,(_check("retrieval.completeness",None,"CONSEQUENTIAL_RETRIEVAL_UNLOGGED"),))
    return aggregate([_check("retrieval.completeness",True,"OK")])

def validate_fitted_state(state:Mapping[str,Any],forecast_cutoff:str)->Validation:
    checks=_required(state,("transformation_ref","fit_information_cutoff","fit_window","fit_snapshot_refs","configuration_ref","state_artifact_ref"),"fitted_state"); cutoff=state.get("fit_information_cutoff")
    if cutoff is not None:
        try: checks.append(_check("fitted_state.cutoff",timestamp_le(cutoff,forecast_cutoff),"FITTED_STATE_FUTURE_INFORMATION"))
        except CanonicalizationError: checks.append(_check("fitted_state.cutoff",False,"INVALID_FIT_CUTOFF"))
    return aggregate(checks)

def validate_current_verifiability_with_availability(report:Mapping[str,Any],*,required_evidence_available:bool)->Validation:
    checks=list(validate_current_verifiability_report(report).checks)
    if report.get("current_verifiability_state")=="FULL" and not required_evidence_available: checks.append(_check("verifiability.required_evidence",False,"FULL_VERIFIABILITY_WITH_MISSING_EVIDENCE"))
    return aggregate(checks)

def validate_resolution_state(*,ambiguous:bool,ambiguity_policy:str,resolution_state:str)->Validation:
    if ambiguous and ambiguity_policy in {"UNRESOLVED","REVIEW_REQUIRED"}: return aggregate([_check("resolution.ambiguity",resolution_state in {"UNRESOLVED","REVIEW_REQUIRED"},"AMBIGUITY_SUPPRESSED")])
    return aggregate([_check("resolution.ambiguity",True,"OK")])
