from __future__ import annotations
from typing import Any, Mapping
from .canonical import verify_sealed_object
from .core import Validation, aggregate
from ._checks import check as _check, required as _required

POLICY_REQUIRED: dict[str, tuple[str, ...]] = {
    "RetryPolicy": ("max_attempts", "retry_eligible_failure_codes", "randomness_progression_rule", "issuance_eligible_success_rule", "infrastructure_timeout_rule", "exhausted_budget_rule"),
    "OmissionPolicy": ("allowed_omission_codes", "required_evidence_by_code", "operator_discretion_rule", "cohort_accounting_rule"),
    "CorrectionPolicy": ("correction_types", "substantive_field_set", "replacement_requirement", "withdrawal_rule", "scoring_treatment_by_type"),
    "EvaluationPolicy": ("cohort_definition", "inclusion_rule", "withdrawal_treatment", "missing_slot_treatment", "unresolved_treatment", "scoring_rule_refs", "aggregation_rule"),
    "RetentionPolicy": ("artifact_class_rules", "minimum_retention_by_class", "external_recovery_rule", "current_verifiability_rule"),
    "ReviewRule": ("authorized_subject_types", "authorized_decisions", "reviewer_authority_requirements", "required_evidence", "conflict_rule", "hard_override_prohibitions"),
    "AcceptanceRule": ("candidate_subject_type", "authority_requirement", "required_validation_reports", "required_external_anchor_evidence", "decision_values", "predecessor_binding_rule"),
    "ResolutionEvidencePolicy": ("source_priority", "publication_semantics", "retrieval_semantics", "vintage_selection", "conflict_rule", "evidence_sufficiency", "resolution_deadline_rule", "human_review_rule_or_none"),
    "IssuanceSchedulePolicy": ("target_set", "method_set", "cadence_rule", "horizon_rule", "slot_construction_rule", "plan_deadline_rule", "execution_window_rule", "forecast_deadline_rule"),
    "PublicRandomnessPolicy": ("source_contract_ref", "challenge_construction_rule", "observation_time_rule", "seed_derivation_rule", "retry_progression_rule"),
    "SourceSelectionPolicy": ("candidate_artifact_rule", "selection_order", "tie_break_rule", "revision_rule"),
}
SOURCE_REQUIRED = ("source_contract_id", "source_contract_version", "source_identity", "access_mode", "artifact_identity_rule", "availability_rule", "publication_rule", "revision_rule", "artifact_selection_rule", "retention_class", "failure_semantics")

def validate_policy_definition(policy: Mapping[str, Any]) -> Validation:
    checks = []
    if not verify_sealed_object(policy): return aggregate([_check("policy.seal", False, "INVALID_SEAL")])
    checks += _required(policy, ("policy_id", "policy_version", "policy_type", "scope", "rules", "change_policy"), "policy")
    required = POLICY_REQUIRED.get(policy.get("policy_type"))
    if required is None: checks.append(_check("policy.type", None, "UNKNOWN_POLICY_TYPE")); return aggregate(checks)
    rules = policy.get("rules")
    if not isinstance(rules, Mapping): checks.append(_check("policy.rules", False, "RULES_NOT_OBJECT")); return aggregate(checks)
    checks += _required(rules, required, f"policy.{policy.get('policy_type')}")
    if policy.get("policy_type") == "OmissionPolicy": checks.append(_check("policy.omission_discretion", rules.get("operator_discretion_rule") == "PROHIBITED_AFTER_OUTPUT_INSPECTION", "OUTPUT_INSPECTION_DISCRETION_NOT_PROHIBITED"))
    return aggregate(checks)

def validate_source_contract(contract: Mapping[str, Any]) -> Validation:
    if not verify_sealed_object(contract): return aggregate([_check("source.seal", False, "INVALID_SEAL")])
    checks = _required(contract, SOURCE_REQUIRED, "source"); rule = contract.get("artifact_selection_rule")
    checks.append(_check("source.selection_rule", bool(rule) and rule not in {"OPERATOR_DISCRETION", "NONE", "AMBIGUOUS"}, "ARTIFACT_SELECTION_UNDEFINED_OR_DISCRETIONARY"))
    return aggregate(checks)
