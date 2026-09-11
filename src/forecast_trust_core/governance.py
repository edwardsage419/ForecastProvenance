from __future__ import annotations
from typing import Any, Mapping, Sequence
from .canonical import CanonicalizationError, sorted_refs, validate_ref, verify_sealed_object
from .core import Result, Validation, aggregate
from ._checks import check as _check, required as _required

def validate_review_decision(decision: Mapping[str, Any], *, hard_failure: bool = False, human_authentic: bool = True) -> Validation:
    if not verify_sealed_object(decision): return aggregate([_check("review.seal", False, "INVALID_SEAL")])
    checks = _required(decision, ("review_rule_ref", "subject_ref", "reviewer_authority_ref", "evidence_refs", "decision", "reason_codes", "rationale"), "review")
    if hard_failure and decision.get("decision") in {"ACCEPT", "OVERRIDE", "VALID"}: checks.append(_check("review.hard_override", False, "HARD_FAILURE_NON_OVERRIDABLE"))
    if not human_authentic: checks.append(_check("review.human_authenticity", False, "SYNTHETIC_HUMAN_EVIDENCE"))
    return aggregate(checks)

def validate_manifest_acceptance(manifest: Mapping[str, Any], acceptance: Mapping[str, Any], *, bootstrap_root_ref: Mapping[str, Any] | None) -> Validation:
    if not verify_sealed_object(manifest) or not verify_sealed_object(acceptance): return aggregate([_check("acceptance.seals", False, "INVALID_SEAL")])
    checks = _required(acceptance, ("candidate_manifest_ref", "external_anchor_evidence_ref", "acceptance_rule_ref", "authority_ref", "decision", "reason_codes"), "acceptance")
    exact = {"object_id": manifest["object_id"], "content_sha256": manifest["content_sha256"]}
    checks.append(_check("acceptance.manifest_binding", acceptance.get("candidate_manifest_ref") == exact, "MANIFEST_HASH_MISMATCH")); checks.append(_check("acceptance.no_self_authority", acceptance.get("authority_ref") != exact, "MANIFEST_SELF_AUTHORIZATION"))
    if manifest.get("manifest_sequence") == 1: checks.append(_check("acceptance.bootstrap_root", bootstrap_root_ref is not None and acceptance.get("authority_ref") == bootstrap_root_ref, "BOOTSTRAP_ROOT_MISMATCH"))
    checks.append(_check("acceptance.decision", acceptance.get("decision") == "ACCEPT", "MANIFEST_NOT_ACCEPTED")); return aggregate(checks)

def validate_anchor_event_dag(events: Sequence[Mapping[str, Any]], subject_ref: Mapping[str, Any]) -> Validation:
    checks=[]
    try: validate_ref(subject_ref)
    except CanonicalizationError: return aggregate([_check("anchor.subject", False, "MALFORMED_SUBJECT_REF")])
    ids=set(); by_id={}
    for event in events:
        if not verify_sealed_object(event): checks.append(_check("anchor.event_seal", False, "INVALID_ANCHOR_EVENT_SEAL")); continue
        eid=event["object_id"]
        if eid in ids: checks.append(_check("anchor.event_unique", False, "DUPLICATE_ANCHOR_EVENT"))
        ids.add(eid); by_id[eid]=event; checks.append(_check("anchor.subject_binding", event.get("anchored_subject_ref") == subject_ref, "ANCHOR_SUBJECT_CONFLICT"))
        if event.get("event_type") == "OPERATIONAL_FAILURE_RECORD": checks.append(_check("anchor.failure_claim", event.get("external_attestation") in (None,"NONE",""), "OPERATIONAL_FAILURE_OVERCLAIMS_EXTERNAL_EVIDENCE"))
    for event in events:
        pred=event.get("predecessor_event_ref_or_none")
        if isinstance(pred, Mapping): checks.append(_check("anchor.predecessor_exists", pred.get("object_id") in by_id, "ANCHOR_PREDECESSOR_MISSING"))
    return aggregate(checks)

def validate_origin_class(obj: Mapping[str, Any]) -> Validation:
    checks=[_check("origin.class", obj.get("origin_class") in {"SYNTHETIC","RETROSPECTIVE","NATIVE_POST_GENESIS"}, "STORED_PROSPECTIVE_SELF_LABEL_OR_UNKNOWN_ORIGIN")]
    if "prospective_eligible" in obj: checks.append(_check("origin.no_self_prospective", obj.get("prospective_eligible") is False, "PROSPECTIVE_ELIGIBILITY_MUST_BE_DERIVED"))
    return aggregate(checks)

def validate_validation_report(report: Mapping[str, Any], *, required_trusted_manifest_ref: Mapping[str, Any] | None = None, required_validator_contract_ref: Mapping[str, Any] | None = None) -> Validation:
    if not verify_sealed_object(report): return aggregate([_check("validation_report.seal", False, "INVALID_SEAL")])
    checks=_required(report,("validator_contract_ref","trusted_manifest_ref","candidate_object_ref","dependency_refs","result","checks"),"validation_report")
    checks.append(_check("validation_report.no_runtime_time", "validated_at" not in report, "RUNTIME_TIMESTAMP_IN_DETERMINISTIC_REPORT")); checks.append(_check("validation_report.no_undefined_root", "dependency_root" not in report, "UNDEFINED_DEPENDENCY_ROOT"))
    if required_trusted_manifest_ref is not None: checks.append(_check("validation_report.manifest_binding", report.get("trusted_manifest_ref") == required_trusted_manifest_ref, "TRUSTED_MANIFEST_SUBSTITUTION"))
    if required_validator_contract_ref is not None: checks.append(_check("validation_report.validator_binding", report.get("validator_contract_ref") == required_validator_contract_ref, "VALIDATOR_VERSION_SUBSTITUTION"))
    deps=report.get("dependency_refs")
    if isinstance(deps,list):
        try: checks.append(_check("validation_report.dependency_order", deps == sorted_refs(deps), "UNSORTED_DEPENDENCY_REFS"))
        except CanonicalizationError: checks.append(_check("validation_report.dependency_order", False, "MALFORMED_DEPENDENCY_REF"))
    else: checks.append(_check("validation_report.dependency_order", False, "DEPENDENCY_REFS_NOT_LIST"))
    return aggregate(checks)

def validate_governance_fork(successors: Sequence[Mapping[str, Any]], *, fork_rule: str | None) -> Validation:
    if len(successors)<=1: return aggregate([_check("governance.fork",True,"OK")])
    if fork_rule in {None,"NONE","PROHIBITED"}: return Validation(Result.INELIGIBLE_TRUST_UNKNOWN,(_check("governance.fork",None,"UNRESOLVED_GOVERNANCE_FORK"),))
    return aggregate([_check("governance.fork",True,"AUTHORIZED_FORK_RULE")])

def validate_manifest_candidate(manifest: Mapping[str, Any]) -> Validation:
    if not verify_sealed_object(manifest): return aggregate([_check("manifest_candidate.seal",False,"INVALID_SEAL")])
    return aggregate([_check("manifest_candidate.no_self_status", "status" not in manifest, "CANDIDATE_MANIFEST_SELF_ACCEPTANCE_FIELD")])
