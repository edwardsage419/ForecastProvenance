from __future__ import annotations
from typing import Any, Mapping, Sequence
from .canonical import CanonicalizationError, sorted_refs
from .core import Result, Validation, aggregate
from ._checks import check as _check

def validate_attempt_chain(attempts:Sequence[Mapping[str,Any]],retry_rules:Mapping[str,Any])->Validation:
    checks=[]; max_attempts=retry_rules.get("max_attempts")
    if not isinstance(max_attempts,int) or max_attempts<1: return aggregate([_check("attempts.max",False,"INVALID_MAX_ATTEMPTS")])
    checks.append(_check("attempts.budget",len(attempts)<=max_attempts,"RETRY_BUDGET_EXCEEDED")); seen=set(); first_success=False; allowed=set(retry_rules.get("retry_eligible_failure_codes",[]))
    for idx,attempt in enumerate(attempts):
        aid=attempt.get("attempt_id"); checks.append(_check(f"attempts.{idx}.unique",isinstance(aid,str) and aid not in seen,"DUPLICATE_ATTEMPT_ID")); pred=attempt.get("retry_of_or_none")
        if idx==0: checks.append(_check("attempts.first_predecessor",pred in ("NONE",None),"FIRST_ATTEMPT_HAS_PREDECESSOR"))
        else:
            checks.append(_check(f"attempts.{idx}.predecessor",isinstance(pred,str) and pred in seen,"RETRY_PREDECESSOR_MISSING")); prior=attempts[idx-1].get("failure_code_or_none"); checks.append(_check(f"attempts.{idx}.retry_trigger",prior in allowed,"RETRY_TRIGGER_NOT_PRECOMMITTED"))
        if isinstance(aid,str): seen.add(aid)
        if attempt.get("terminal_status")=="SUCCEEDED":
            if not first_success: first_success=True; checks.append(_check(f"attempts.{idx}.eligible_success",attempt.get("issuance_eligible") is True,"FIRST_SUCCESS_NOT_ISSUANCE_ELIGIBLE"))
            else: checks.append(_check(f"attempts.{idx}.later_success",attempt.get("issuance_eligible") is not True,"LATER_SUCCESS_CHERRY_PICKED"))
    return aggregate(checks)

def validate_forecast_correction(correction:Mapping[str,Any],*,original_forecast_ref:Mapping[str,Any],correction_policy:Mapping[str,Any])->Validation:
    checks=[_check("correction.original_binding",correction.get("original_forecast_ref")==original_forecast_ref,"CORRECTION_ORIGINAL_MISMATCH"),_check("correction.no_self_scoring","scoring_consequence" not in correction,"CORRECTION_SELF_SCORING")]
    affected=set(correction.get("affected_fields",[])); substantive=set(correction_policy.get("substantive_field_set",[])); ctype=correction.get("correction_type")
    if affected&substantive:
        checks.append(_check("correction.substantive_replacement",ctype=="SUBSTANTIVE_REPLACEMENT" and isinstance(correction.get("replacement_forecast_ref_or_none"),Mapping),"SUBSTANTIVE_CHANGE_WITHOUT_REPLACEMENT"))
        if correction.get("replacement_forecast_ref_or_none")==original_forecast_ref: checks.append(_check("correction.new_identity",False,"REPLACEMENT_REUSES_ORIGINAL_IDENTITY"))
    checks.append(_check("correction.no_erasure",correction.get("action")!="DELETE_ORIGINAL","CORRECTION_ERASURE_PROHIBITED")); return aggregate(checks)

def validate_evaluation_cohort(expected_refs:Sequence[Mapping[str,Any]],included_refs:Sequence[Mapping[str,Any]])->Validation:
    try: expected=sorted_refs(expected_refs); included=sorted_refs(included_refs)
    except CanonicalizationError: return aggregate([_check("cohort.refs",False,"MALFORMED_COHORT_REFERENCE")])
    return aggregate([_check("cohort.completeness",expected==included,"COHORT_DELETION_OR_INSERTION")])

def validate_slot_output(slot:Mapping[str,Any],forecast:Mapping[str,Any])->Validation:
    return aggregate([_check("slot.target",forecast.get("target_ref")==slot.get("target_ref"),"TARGET_SUBSTITUTION"),_check("slot.method",forecast.get("method_ref")==slot.get("method_ref"),"METHOD_SUBSTITUTION"),_check("slot.output_schema",forecast.get("output_schema_ref")==slot.get("output_schema_ref"),"OUTPUT_SCHEMA_SUBSTITUTION")])

def validate_allowed_fields(obj:Mapping[str,Any],allowed_fields:set[str])->Validation: return aggregate([_check("schema.unknown_fields",not(set(obj)-allowed_fields),"UNKNOWN_EXTENSION_FIELD")])
