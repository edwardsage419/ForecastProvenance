# Supporting Normative Contracts

Version: 0.5 candidate
Status: GEN_001 ARCHITECTURE COMPRESSION P5

These objects define supporting Trust Core contracts. They create no prospective history by themselves.

## SourceContract

A SourceContract freezes exact source identity, access mode, artifact identity/selection, availability semantics, publication semantics, revision treatment, retention class, and failure semantics. Retrieval time cannot silently substitute for historical availability.

## TransformationDefinition and FittedState

The generic Trust Core retains TransformationDefinition and FittedState interfaces for successor manifests. Genesis v1 does not instantiate a fitted transformation or FittedState dependency because `method:last-observed-value:v1` is deterministic and unfitted.

## ReviewDecision

ReviewDecision remains a generic successor interface. Compressed Genesis v1 does not instantiate a scientific Human Review policy and does not admit a ReviewDecision that chooses a resolved numerical value.

Official conflict or semantic ambiguity remains `REVIEW_REQUIRED` or `UNRESOLVED` under Genesis v1.

## ManifestAcceptance v2

Required substantive fields are:

```text
candidate_manifest_ref
bootstrap_governance_root_ref
acceptance_rule_ref
required_validation_report_refs
authority_ref
decision
reason_codes
blocking_finding_refs
signature_ref
```

The signed object intentionally contains no required `external_anchor_evidence_ref` or later final-evidence self-reference.

Final external evidence is created after signing and is supplied as a separate independent-final-validation input. It must bind the exact signed ManifestAcceptance.

## IssuanceCyclePlan

A Genesis v1 cycle plan binds exact historical protocol/manifest/schedule policy, cycle identity, information cutoff, execution window, plan commitment deadline, external proof deadline, deterministic expected slots, retry policy, and omission policy.

Because the sole initial method uses `randomness_policy = NONE`, Genesis v1 does not require a PublicRandomnessPolicy reference.

The exact plan is a direct P2 wall-clock subject. Its `DEADLINE_EXISTENCE_VERIFIED` deadline is the frozen `plan_commitment_deadline`.

## IssuanceCycleManifest

The exact cycle manifest binds the exact cycle plan, complete slot accounting, attempts, issued-forecast refs, omissions and failures.

It is the Genesis v1 direct forecast-deadline subject. Exact forecast refs inherit the deadline condition through validated membership in the complete mandatory slot accounting.

## DurabilityVerificationRecord

A DurabilityVerificationRecord binds the exact ExternalTimeEvidenceBundle, exact OTS proof and exact strong Bitcoin verification report.

For scientific forecast cycles it is a direct wall-clock subject whose deadline is the frozen outcome-information barrier. `PRE_OUTCOME_DURABILITY_VERIFIED` requires verified Bitcoin durability plus verified deadline existence of this exact record.

## ValidationReport v2

Version 2 deterministic validation output carries:

```text
validator_contract_ref
trusted_manifest_ref
manifest_acceptance_ref_or_absent
candidate_object_ref
dependency_refs
result
checks
derived_claims
```

`derived_claims` is a sorted deterministic vector. Claim types are:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

Claim states are:

```text
VERIFIED
FAILED
UNRESOLVED
NOT_APPLICABLE
```

A stronger claim failure never rewrites a weaker verified historical fact.

## RoughtimeProviderQualificationStatePackage

This is supporting evidence, not qualification or governance authority.

Required substantive fields include:

```text
provider_id
as_of_utc
provider_profile_ref
qualification_decision_ref
qualification_evidence_manifest_sha256
qualification_verifier_contract_ref
metadata_review_refs
requalification_event_refs
qualification_state_report_sha256
qualification_state
```

The authoritative collector/verifier scans the fixed retained qualification record root and requires exact equality between the package's metadata/requalification refs and all relevant retained state objects through `as_of_utc`.

A caller-selected event subset is insufficient.

For a Genesis v1 deadline event, `as_of_utc` equals the event's exact frozen deadline. Only `qualification_state = PRODUCTION_QUALIFIED` is admissible, and all three manifest-admitted providers must independently satisfy that state gate before receipt quorum is evaluated.

## Anchor evidence

Wall-clock existence evidence and Bitcoin durability remain separate evidence families. Bitcoin block header time is never interpreted as a precise civil-time upper bound.

## CurrentVerifiabilityReport

Current availability of retained bytes is a separate derived operational claim. Loss of required evidence can degrade current verifiability without rewriting immutable historical ValidationReports.

## Historical compatibility

Historical contract versions and historical validators remain valid for the bytes they originally governed. Architecture Compression v0.5 contracts apply prospectively only to the successor pre-Genesis candidate and do not reinterpret earlier candidate artifacts.
