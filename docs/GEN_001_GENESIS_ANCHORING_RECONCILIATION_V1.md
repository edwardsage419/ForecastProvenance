# GEN_001 Genesis Anchoring Reconciliation V1

Date: 2026-09-14
Status: ARCHITECTURE_COMPRESSION_P1_DESIGN_CONTROL
Classification: PRE_GENESIS_DESIGN
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis commit: `9790e323a519558b92b7d6c1324b3bd847cfacfe`

## Purpose

This record closes Architecture Compression P1 at the design level. It identifies the existing Genesis anchoring inconsistencies and establishes the successor design target that P5 must implement through versioned candidate objects, schemas, validators, readiness controls, abort conditions, and tests.

Historical candidate objects and historical documents retain their original semantics. This record does not rewrite `candidate_object_set_v0_2.json` or patches v0.3 through v0.5. The current v0.5 candidate lineage remains non-prospective and is not eligible for Genesis freeze until P5 implements and validates the successor anchoring semantics.

## Existing inconsistency

The repository currently expresses three different anchoring gates.

| Surface | Current requirement | Problem |
| --- | --- | --- |
| `GENESIS_MANIFEST_PROCEDURE.md` | Separate external evidence for bootstrap governance, candidate manifest, and signed ManifestAcceptance | Three mandatory anchor stages |
| `GENESIS_PROTOCOL.md` | Governance envelope, candidate manifest, and ManifestAcceptance are independently externally evidenced | Repeats the three-stage requirement |
| `GENESIS_BOOTSTRAP_GOVERNANCE.md` | Bootstrap root or containing governance envelope must be externally anchored before prospective trust | Adds a mandatory bootstrap anchor |
| `policy:genesis-acceptance:v1` | Requires `FPP_TIME_EVIDENCE_V1_FOR_MANIFEST_AND_ACCEPTANCE` | Expresses two anchor subjects rather than three |
| `GENESIS_READINESS_EVIDENCE_MATRIX.md` | GR037 requires manifest and acceptance external evidence | No separate bootstrap-governance closure item equivalent to the procedure requirement |
| `GENESIS_ABORT_CONDITIONS.md` | Manifest or ManifestAcceptance external evidence failure rejects acceptance | Encodes separate manifest and acceptance anchoring |
| `validate_manifest_acceptance` | Requires `external_anchor_evidence_ref` inside ManifestAcceptance | The field can only refer to evidence created before the signed acceptance exists, so it cannot bind the final post-signature acceptance evidence without circularity |
| `GENESIS_OWNER_ACTION_PACKET.md` | Completion language emphasizes externally evidencing the signed ManifestAcceptance | Operational summary already points toward a single final acceptance anchor |

The three-stage procedure, two-stage policy/readiness model, and validator field semantics cannot all be authoritative at the same time.

## Security properties that must remain

The compressed design must preserve all of these properties.

1. `BootstrapGovernanceRoot` is supplied independently of the candidate manifest graph.
2. A candidate manifest cannot select or regenerate its own trust root.
3. The owner signature is verified against the exact bootstrap public key supplied as an external trust input.
4. The signed `ManifestAcceptance` binds the exact `TrustedManifest` by full content identity.
5. The signed `ManifestAcceptance` binds the exact acceptance policy and the complete required validation-report set by full content identity.
6. Blocking findings must be empty under the accepted rule before an `ACCEPT` decision can validate.
7. The final external evidence package binds the exact signed `ManifestAcceptance` bytes or exact sealed-object content hash.
8. Independent final validation receives the final external evidence package separately and reconstructs the complete acceptance basis without relying on mutable repository state.
9. No prospective issuance may occur until independent final validation passes and the owner separately gives explicit Genesis authorization.
10. Historical candidate objects, failed candidates, rehearsals, and evidence classifications remain immutable.

## P1 decision

The Architecture Compression successor design uses one mandatory final external evidence stage for Genesis governance acceptance.

```text
BootstrapGovernanceRoot
→ TrustedManifest
→ Validation Reports
→ owner-signed ManifestAcceptance
→ final external time/durability evidence package
→ independent final validation
→ separate explicit Genesis authorization
```

Standalone external anchoring of `BootstrapGovernanceRoot`, a containing governance envelope, or the candidate `TrustedManifest` is `OPTIONAL_AUDIT_EVIDENCE` under this successor design. Such evidence may be retained when useful. It cannot substitute for the mandatory final evidence over the signed `ManifestAcceptance`.

## Why the compression is acceptable

Before Genesis authorization there are no native prospective forecasts and no scientific outputs whose selection could benefit from choosing among differently anchored Genesis manifests after observing outcomes.

The bootstrap authority remains an external trust input. The exact root is bound into the acceptance basis and the owner signature must verify against it. Removing a standalone bootstrap timestamp therefore removes redundant chronology evidence while preserving authority authenticity and trust-root independence.

The `TrustedManifest` and required validation reports are content-addressed. The owner-signed `ManifestAcceptance` binds their exact identities. A final external commitment to the signed acceptance transitively commits the exact accepted manifest and validation basis.

Independent final validation occurs after the final external evidence exists. The separate Genesis authorization occurs only after that validation. The first forecast cycle must still satisfy its own deterministic schedule, precommitment, deadline-evidence, and durability rules. Genesis governance compression therefore does not remove forecast-cycle precommitment requirements.

## Security delta from removing intermediate mandatory anchors

Removing the standalone bootstrap anchor means the project no longer proves that the bootstrap root existed at an earlier independent wall-clock point than the final acceptance. The retained claim is narrower: the exact externally supplied bootstrap root participated in the signed and finally anchored Genesis acceptance state.

Removing the standalone manifest anchor means the project no longer proves that the candidate manifest existed at an earlier independent wall-clock point than its signed acceptance. The retained claim is narrower: the exact manifest was bound into the owner-signed acceptance and that signed acceptance was externally evidenced before Genesis authorization.

These narrower claims are sufficient for Genesis governance because no native prospective forecasting is authorized before final validation and explicit Genesis authorization. If a future governance model requires proof that a proposal existed for a minimum review period before acceptance, that requirement must be added through a successor manifest or versioned governance policy.

## Noncircular ManifestAcceptance rule

The signed `ManifestAcceptance` must not require a reference to the final evidence package that will be created only after the signature exists.

The successor object should bind at least:

```text
candidate_manifest_ref
bootstrap_governance_root_ref
acceptance_rule_ref
required_validation_report_refs
authority_ref
decision
reason_codes
blocking_finding_refs_or_empty
signature_or_signature_ref
```

The final evidence package is a separate object or package supplied to final validation.

```text
final_evidence_subject_ref == signed_manifest_acceptance_ref
```

Any preacceptance bootstrap or manifest anchor reference is optional audit metadata and is outside the mandatory acceptance core.

## Successor AcceptancePolicy target

P5 should create a new policy version. `policy:genesis-acceptance:v1` must remain immutable historical candidate material.

The successor policy should encode these semantics:

```text
intermediate_anchor_rule = OPTIONAL_AUDIT_ONLY
final_external_evidence_required = true
final_external_evidence_subject = SIGNED_MANIFEST_ACCEPTANCE
final_external_evidence_role = EXTERNAL_FINAL_VALIDATION_INPUT
bootstrap_root_source = EXTERNAL_TO_CANDIDATE_MANIFEST_GRAPH
required_validation_reports = exact frozen report set
blocking_findings_rule = MUST_BE_EMPTY_FOR_ACCEPT
first_execution_rule = STRICTLY_AFTER_FINAL_VALIDATION_AND_EXPLICIT_GENESIS_AUTHORIZATION
```

P5 must assign a new semantic policy ID and exact sealed content hash. It must use predecessor-bound retirement or replacement mechanics rather than editing v1.

## Validator changes required in P5

`validate_manifest_acceptance` currently requires `external_anchor_evidence_ref`. That requirement is incompatible with a final post-signature anchor and must not be silently reinterpreted.

P5 must version the validation semantics so that:

1. `ManifestAcceptance` itself does not require its own final evidence reference.
2. the acceptance binds the exact bootstrap root, manifest, acceptance rule, and required validation reports;
3. owner signature verification uses the externally supplied bootstrap trust root;
4. a separate final-validation path receives the final evidence package;
5. the final evidence package must bind the exact signed acceptance;
6. required existence and durability checks fail closed when missing, invalid, late under the applicable rule, or bound to another subject;
7. optional intermediate audit anchors have no authority to satisfy a missing final acceptance anchor.

## Readiness and abort-control changes required in P5

`GENESIS_READINESS_EVIDENCE_MATRIX.md` must replace the current manifest-and-acceptance anchoring closure concept with one explicit closure item for final signed-ManifestAcceptance external evidence.

The readiness matrix must still retain independent closure items for the exact BootstrapGovernanceRoot, TrustedManifest, ValidatorContract, validation reports, owner signature, final independent validation, and separate Genesis authorization gate.

`GENESIS_ABORT_CONDITIONS.md` must fail closed when final acceptance evidence is absent, invalid, late under the applicable final-evidence rule, or bound to a different signed acceptance. Failure of optional intermediate bootstrap or manifest audit anchoring must not block the compressed Genesis profile.

## Relationship to temporal-claim separation

P1 establishes the commitment topology. P2 will define the exact result vocabulary and derived states for wall-clock existence, Bitcoin durability, pre-outcome durability, and confirmatory prospective eligibility.

P1 therefore does not collapse wall-clock evidence and Bitcoin durability into one timestamp. Bitcoin block header time remains ineligible as a precise civil-time upper bound.

## Current implementation status

```text
P1_ANCHORING_RECONCILIATION = COMPLETE
P1_SINGLE_FINAL_ACCEPTANCE_ANCHOR_DESIGN = COMPLETE
CURRENT_V0_5_CANDIDATE_ALIGNED = NO
CURRENT_VALIDATOR_ALIGNED = NO
CURRENT_READINESS_MATRIX_ALIGNED = NO
P5_VERSIONED_IMPLEMENTATION_REQUIRED = YES
GENESIS_READY = NO
```

Until P5 implements and validates the successor semantics, the current candidate lineage and current validator must not be represented as the compressed Genesis profile.

## Network and qualification boundary

This P1 decision requires no provider request and does not reopen production qualification.

```text
network_authorized = false
Roughtime provider requests authorized = 0
RFC3161 requests authorized = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

## Safety boundary

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production forecasting = PROHIBITED
```

This record does not authorize Genesis, Forecast Ledger creation, forecast issuance, provider qualification execution, or any network time request.

The Genesis Ed25519 private key remains outside repository and connected-tool boundaries. Only the public key may later enter project objects under an authorized governance step.
