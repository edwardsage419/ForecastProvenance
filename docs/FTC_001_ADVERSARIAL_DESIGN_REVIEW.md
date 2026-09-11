# FTC_001 Adversarial Scientific Design Review

Date: 2026-09-11
Review target: design/ftc-001
Disposition: BLOCKING FINDINGS IDENTIFIED

## Review objective

Attempt to break the current Trust Core design before implementation. A finding is blocking when the current normative text permits two reasonable implementations to produce materially different trust classifications, or permits a stronger scientific claim than the evidence supports.

## B01 Forecast object identity has a circular construction

Severity: BLOCKING

The current identifier contract proposes content derived suffixes for IssuedForecast and ForecastRunAttempt while the shared envelope places object_id inside the substantive object. If object_id is included in the substantive projection, the hash depends on the ID and the ID depends on the hash.

Required resolution:

1. Normative content addressed event IDs must be derived from a hash projection that excludes object_id.
2. Define a separate payload hash or define object_id as non substantive derived metadata.
3. Dependency references must bind the final full content identity without circularity.

## B02 Mutable lifecycle fields are mixed with immutable object content

Severity: BLOCKING

AnchorReceipt includes verification_state and verified_at while OpenTimestamps proofs naturally evolve from pending to upgraded Bitcoin attestation. IssuedForecast also has a trust lifecycle described as if the forecast object itself changes state.

This conflicts with append only object identity.

Required resolution:

1. Separate immutable evidence events from derived lifecycle state.
2. An IssuedForecast must never mutate from pending to verified.
3. Anchor submission, proof upgrade, verification, failure, and lateness must be append only events or immutable receipt versions with explicit predecessor binding.
4. Lifecycle status must be derived from the event graph under a validator version.

## B03 Claimed submission time is insufficient for anchor latency policy

Severity: BLOCKING

A locally claimed submitted_at can be backdated. A maximum anchor latency rule cannot safely measure from local submission time to Bitcoin attestation without an independently defensible lower or upper bound.

Required resolution:

Genesis must define latency in terms of verifiable external evidence or classify the latency claim as operational metadata only. Prospective eligibility must depend on an externally verifiable existence boundary relative to the target cutoff or other frozen temporal boundary.

## B04 Prospective time relation to target closure is underspecified

Severity: BLOCKING

The current design requires external anchoring but does not yet state the exact inequality required between the external existence bound and the event or target information closure boundary.

Required resolution:

Each target contract must expose a latest admissible external proof boundary or an equivalent deterministic issuance deadline. Genesis must define the inequality used for prospective eligibility.

## B05 Batch completeness is not independently committed

Severity: BLOCKING

Timestamping a manifest proves existence of listed forecasts. It does not prove that an operator did not run or seal additional forecasts and selectively omit unfavorable ones before anchoring.

Required resolution:

Define an issuance cycle commitment before method outputs are inspected, or define a complete attempt accounting mechanism that binds scheduled targets, methods, expected slots, attempts, omissions, failures, and issued outputs into the anchored cycle manifest.

## B06 Retry policy can still permit selection bias

Severity: BLOCKING

Attempt lineage is recorded, but the design does not yet define how the expected first attempt or retry budget is committed before outputs are known.

Required resolution:

Retry policy must specify precommitted retry triggers, maximum attempts, deterministic selection of the issuance eligible attempt, and treatment of infrastructure failure. The issuance manifest must account for all expected attempts or explicit missing slots.

## B07 External source contracts are referenced but undefined as normative objects

Severity: BLOCKING

Point in time eligibility depends on source contracts, while Trust Core currently defines only eight object families and gives no normative SourceContract schema.

Required resolution:

Either add SourceContract as a ninth normative contract object or define it as a first class normative sub contract with the same identity, hash, manifest, and versioning guarantees.

## B08 Transformation contracts are referenced but undefined

Severity: BLOCKING

EvidenceSnapshot and fitted transformation rules bind transformation_refs, yet no normative TransformationDefinition or FittedState contract exists.

Required resolution:

Define transformation identity, code identity, parameters, stateless or fitted classification, fit evidence, fit cutoff, and fitted state hash under a first class normative contract.

## B09 Human review record has no normative object contract

Severity: HIGH, BLOCKING FOR HUMAN REVIEW PATHS

The design allows REQUIRES_REVIEW and immutable human review records, but does not define their identity, evidence binding, authority, conflict handling, or correction semantics.

Required resolution:

Define a ReviewDecision contract before any target or resolution rule can rely on human judgment.

## B10 Validation result includes validated_at without defining hash semantics

Severity: HIGH

A validation result may be reproducible in scientific content while validated_at changes every run. If validated_at is substantive, reproducibility breaks. If excluded, that exclusion must be explicit.

Required resolution:

Separate deterministic ValidationReport content from execution metadata. A deterministic report should contain validator version, inputs, checks, and result. Runtime validation timestamp belongs to a non authoritative execution record.

## B11 Classification is vulnerable to semantic confusion

Severity: HIGH

NORMATIVE, SYNTHETIC, RETROSPECTIVE, and PROSPECTIVE mix object role with experimental evidence class. A TargetDefinition can be normative while a synthetic forecast is synthetic. One scalar field cannot represent both axes safely.

Required resolution:

Separate object_role from evidence_class. Normative definitions use object_role. Forecast and evidence records use evidence_class. Prospective eligibility is derived, not self asserted.

## B12 Unicode policy is deterministic but operationally dangerous

Severity: MEDIUM

RFC 8785 intentionally preserves strings without Unicode normalization. Visually identical identifiers can therefore have distinct byte identities.

Required resolution:

Keep no normalization for arbitrary scientific text. Restrict machine identifiers and enum tokens to ASCII. Add adversarial cases for confusable identifiers and non ASCII object IDs.

## B13 Array ordering is insufficiently specified per schema

Severity: HIGH

The canonicalization document says each schema must state whether array order matters. Current object schemas do not do so consistently.

Required resolution:

For every array field, define ordered semantics or a deterministic sort key. Reject unsorted set like arrays before hashing.

## B14 Hash algorithm agility is only partially designed

Severity: MEDIUM

Version 1 says SHA256 while references structurally name content_sha256. A future migration could require parallel hashes.

Required resolution:

For version 1, explicitly freeze SHA256 and state that algorithm migration requires new reference and manifest schema versions. Avoid premature generic agility.

## B15 Trusted manifest acceptance record is not defined

Severity: BLOCKING

The manifest document says status becomes accepted through an append only acceptance record, but that record has no normative schema. External anchoring of a candidate manifest alone does not establish project governance acceptance.

Required resolution:

Define ManifestAcceptance as an immutable governance object binding candidate manifest hash, external proof reference, decision authority, acceptance rule version, and predecessor protocol state.

## B16 Git retention is insufficient as sole availability guarantee

Severity: HIGH

The architecture allows durable reproducible references. A remote URL can disappear or change, breaking future independent verification.

Required resolution:

Define retention classes. Consequential compact artifacts should be retained by content. External large artifacts need content hashes plus a documented reproducibility or archival policy. Trust classification must degrade if required bytes become unavailable.

## B17 Correction scoring consequence can be self serving

Severity: BLOCKING

ForecastCorrection currently carries scoring_consequence as a field. This could allow a correction to choose its own evaluation treatment after forecast performance becomes apparent.

Required resolution:

Scoring consequence must be derived from the precommitted correction policy in the trusted manifest. The correction event records facts and requested type. It cannot author its own scoring treatment.

## B18 Withdrawal semantics are underspecified

Severity: BLOCKING

A withdrawal after information arrives could become a mechanism for removing losing forecasts.

Required resolution:

Precommit whether and how withdrawals remain in confirmatory evaluation. Default scientific rule should preserve the original issued forecast in cohort accounting unless the precommitted evaluation policy provides an independently justified exception.

## B19 Resolution source availability after outcome is not the same problem as forecast evidence availability

Severity: HIGH

Point in time rules focus on forecast inputs. Outcome resolution evidence has different temporal requirements and can legitimately arrive after the forecast target period.

Required resolution:

Keep forecast evidence eligibility and resolution evidence admissibility as separate contracts. Do not reuse forecast information_cutoff rules for resolution.

## B20 Model internal knowledge cannot be fully provenance audited

Severity: HIGH

For a closed model, pretraining and internal memorized facts cannot be enumerated as EvidenceSnapshot members. The current language could imply stronger provenance completeness than is achievable.

Required resolution:

ForecastMethod must declare evidence observability class. Closed or partially observable methods can be evaluated prospectively, while Trust Core must distinguish externally logged evidence provenance from opaque internal model state.

## Review disposition

FTC_001 is not ready to freeze.

The core architecture remains viable. The review found no reason to abandon the provenance first strategy, explicit trusted manifests, external time anchoring, or model neutrality.

The blocking work is contract boundary repair. Implementation remains prohibited until B01 through B09, B15, B17, and B18 are resolved and the remaining high severity findings have explicit dispositions.
