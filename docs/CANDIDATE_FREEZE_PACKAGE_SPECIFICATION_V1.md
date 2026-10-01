# Candidate Freeze Package Specification V1

Specification identifier: `CANDIDATE_FREEZE_PACKAGE_SPECIFICATION_V1`  
Version: `1.0` (first draft)  
Stage: specification draft; no Candidate Freeze Package is identified or accepted by this document.

**Reading rule.** Paragraphs marked **Normative** define the boundary and review requirements of a future Candidate Freeze Package. Paragraphs marked **Descriptive** explain design intent or current status and cannot add authority, change membership, or override a normative rule. This document does not amend the protocol contracts it references. Where a protocol question arises, the exact applicable TrustedManifest and its admitted contracts govern that question.

**Design basis (descriptive).** This draft implements the R2.3.21 boundary review, R2.3.22 content outline, R2.3.23 semantic review, R2.3.23.1 boundary update, and frozen R2.3.24 drafting plan. Repository documents named below are referenced for their existing authority boundaries, not used as a source of new package or protocol semantics.

## 1. Purpose and Scope

**Normative.** This specification defines the boundary for reviewing a future Candidate Freeze Package: its identity, artifact classes and inventories, exact references, dependency direction, historical compatibility, and package acceptance criteria. A package review must apply an identified version of this specification to an exactly identified candidate set. Approval of this specification is a separate decision from acceptance of that candidate set.

**Normative.** This specification is a package boundary specification. It is not a protocol trust root, a replacement for `TrustedManifest`, a `ManifestAcceptance`, Genesis authority or authorization, forecast authority, or verification that a package has been frozen. A separately constructed package and separately recorded package decision are required. Genesis `ManifestAcceptance` and explicit Genesis authorization remain later, independent transitions under [Trusted Manifest Contract](TRUSTED_MANIFEST.md) and [Genesis Manifest and Acceptance Procedure](GENESIS_MANIFEST_PROCEDURE.md).

**Normative.** The scope excludes creation of a Genesis Ledger, forecast issuance, production or private keys, live anchors, and runtime-generated authority. Runtime records may be classified and retained as evidence under an applicable contract; their presence does not create prospective status.

**Descriptive.** Current safety state for this draft: Genesis `NOT STARTED`; Forecast Ledger `NOT CREATED`; prospective forecast count `0`; `PRODUCTION_QUALIFIED = NO`; Candidate Freeze `NOT AUTHORIZED`.

## 2. Package Identity

**Normative.** The specification identifier and version above identify this drafting document, not a TrustedManifest or a package manifest. A future candidate review must identify the applicable specification version, candidate package identifier and version, freeze stage, scope, effective candidate selection, and exact bytes reviewed. Its record must distinguish committed source bytes from modified or untracked working-tree bytes. A Git HEAD by itself does not identify uncommitted bytes.

**Normative.** A later package manifest must bind the applicable specification version and the exact member identities. A successor candidate's existence or materialization does not make it effective; effective selection must follow its existing lineage authority. Any change in the meaning of inventory membership or classification, authority boundary, reference model, compatibility rule, or acceptance rule requires a new specification version. Pure editorial changes may preserve the semantic version only if normative meaning is unchanged, while any byte-bound digest must still track the changed bytes. A consequential change in candidate members or dependencies requires renewed candidate review and downstream acceptance treatment.

**Descriptive.** [Genesis candidate lineage](../genesis/candidate/README.md) distinguishes effective selection from successor proposals. [Canonicalization and Identifiers](CANONICALIZATION_AND_IDENTIFIERS.md) defines existing object identity and full content-hash references. This specification does not assign an identity to a package that has not been constructed.

## 3. Authority Model

**Normative.** A package review must identify the following roles separately; one role cannot be inferred from inclusion in another:

| Role | Boundary |
| --- | --- |
| A. Bootstrap Governance Root | Independently supplied, out-of-graph Genesis governance root. A candidate cannot select its own accepted root. |
| B. Trusted Manifest | Content-addressed protocol trust root for its applicable historical state; it binds admitted normative dependencies. This specification does not replace it. |
| C. Trust Core controls | Normative contracts and controls only to the extent exact versions are sealed, admitted, and applicable under the governing manifest. |
| D. Genesis domain definitions | Target, method, schedule, source, resolution, policy, and other Genesis definitions only through their exact admitted versions and scope. |
| E. Verification evidence | Reports, reviews, test results, retained source and qualification evidence support a decision but do not appoint their own authority. |
| F. Implementation artifacts | Schemas, validator sources and builds, runtime bindings, and test artifacts are identified and checked under applicable contracts; their presence alone grants no protocol authority. |
| G. Runtime records | Cycle, forecast, evidence, and validation records are evaluated under historical admitted authority. An origin label or a stored result is not prospective eligibility. |

**Normative.** The package inventory must distinguish Trust Core controls from Genesis domain definitions. The six R2.3 design responsibilities are: `ComponentRoleSet` for permitted component roles and object or schema bindings; `ArtifactBindingPolicy` for exact artifact selection, digest checks, cardinality, and missing or extra artifacts; `RuntimeCompatibilityPolicy` for comparison against frozen runtime requirements; `ValidationResultSemantics` for result interpretation and authenticated input closure; `FailureVocabulary` for closed failure meanings and precedence; and `ProjectionProfile` for versioned field selection and a digest recipe for a specified use. These names describe design boundaries. They do not assert that six sealed objects have been instantiated, admitted by a TrustedManifest, or exercised on the Genesis positive path. A projection digest is not a full-object `content_sha256` identity.

**Normative — C01.** `ValidationResultSemantics` defines interpretation boundaries. A successful interpretation, temporal verification, or retained report does not prove complete confirmatory authority unless the underlying admitted runtime authority and all required checks exist and pass. `UNKNOWN` on a required trust condition cannot become a stronger valid claim. The incomplete positive confirmatory path cannot be declared complete by this specification.

**Normative — C04.** Historical Human Review material does not create Genesis scientific selection authority. Human discretion applies only under an exact, accepted review rule for the applicable historical scope; retained wording alone cannot revive a superseded or dormant selection path.

**Descriptive.** The applicable boundaries are described in [Trusted Manifest Contract](TRUSTED_MANIFEST.md), [Forecast Trust Core Normative Contracts](TRUST_CORE_CONTRACTS.md), and [Genesis Manifest and Acceptance Procedure](GENESIS_MANIFEST_PROCEDURE.md). Designed, implemented, tested, effective, accepted, and authorized are distinct states.

## 4. Artifact Inventory Model

**Normative.** A future package must provide separate Trust Core authority and Genesis normative inventories. Each entry must state its class, role, governing authority, exact identity and version, applicable inclusion rule, and required dependencies. The review must account for required, missing, duplicate, and unexpected members under the applicable contracts; it may not silently convert a partial inventory into a complete one. Package inclusion, reference, or retention does not promote an artifact's authority.

| Class | Package-review treatment |
| --- | --- |
| A. Normative authority | Exact admitted governance, manifest, contract, policy, and domain-definition objects, with their scope and authority source distinguished. A designed object is not presumed admitted. |
| B. Verification evidence | Content-bound reports, independent reviews, retained fixtures, external evidence, and qualification evidence used to substantiate a claim. Evidence is not a trust root. |
| C. Implementation artifacts | Exact validator, schema, source, build, dependency, and test artifacts required by the admitted binding. Implementation is not acceptance. |
| D. Operational artifacts | Runtime records, working inventories, logs, and other operational outputs. Classify by actual origin and governing contract; do not treat them as normative definitions. |

**Normative — C05.** Qualification artifacts may be referenced as Class A admitted profiles and decisions or as Class B supporting evidence according to their actual role. Static qualification outputs do not by themselves establish provider state at every later deadline. Any dynamic historical admission claim requires the applicable pinned verifier and content-closed state evidence at the relevant `as_of_utc`. This specification neither claims the qualification transition complete nor chooses a replacement for its unresolved interface.

**Descriptive.** The existing [qualification firewall](GEN_001_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL_V1.md) separates the manifest-bound provider decisions from subsystem evidence and historical state recomputation. This section classifies those materials for package review; it does not qualify a provider.

## 5. Reference and Dependency Model

**Normative.** Every consequential object reference in a future package must identify the exact object by `object_id` and full `content_sha256` where its governing contract requires that pair. The governing version must be explicit or unambiguously fixed by the exact referenced object. Raw evidence and implementation bytes require a stable locator and a full digest under their applicable binding. A display name, shortened hash, Git HEAD alone, or semantic ID alone is insufficient to identify reviewed bytes.

**Normative.** Dependency direction is from the candidate package to this applicable specification version and its exact members; from a member to its already identified governing dependencies; and from a later review decision to the exact candidate and evidence basis it reviews. References must be acyclic. An object, report, candidate, or acceptance decision cannot provide its own authority by referring back to itself or to evidence it later creates. Evidence may substantiate a review but cannot become the authority that admits itself. A package review must check exact-reference closure and separately assess semantic completeness; closure alone does not prove completeness.

**Normative.** Where qualification evidence is involved, the review must preserve the distinction between static manifest-bound outputs and dynamic historical state admission. It must identify the exact applicable verifier and retained evidence basis without treating an isolated validation result as proof that every consequential claim path consumes that result.

**Descriptive.** [Canonicalization and Identifiers](CANONICALIZATION_AND_IDENTIFIERS.md) defines full identity and reference rules. [Trusted Manifest Contract](TRUSTED_MANIFEST.md) supplies the trust-root direction. This document adds no hash algorithm, canonicalization rule, or self-contained admission mechanism.

## 6. Compatibility Model

**Normative.** Historical verification must select the manifest, schema, parser, policy, validator, and digest interpretation applicable to the historical object or cycle, through that state’s governing authority. Retained historical bytes and hashes remain immutable. A successor version may govern later material but cannot silently reinterpret or rewrite earlier objects. The package review must record the exact versions and retained evidence needed to reproduce its compatibility claim.

**Normative.** A weaker historical validator cannot be used as a fallback to assert Genesis completeness or prospective authority. A `ProjectionProfile` digest must be interpreted under its exact profile and use; it cannot be recast as a full content identity or rehashed under a successor meaning. Compatibility of a runtime or locally reconstructed record does not prove semantic completeness of the entire system.

**Normative — C06.** Reconstruction of the cycles supplied to a validator does not prove reconstruction of the complete mandatory-cycle universe. A completeness claim also depends on the applicable historical target set, official retained schedule artifacts, and schedule policy, including accounting for missing mandatory cycles and enforced routing through the authoritative path. This specification does not claim those implementation paths complete.

**Descriptive.** [Trusted Manifest Contract](TRUSTED_MANIFEST.md) preserves historical manifest selection; [Genesis Issuance Schedule Policy](GENESIS_SCHEDULE_POLICY.md) defines mandatory-cycle coverage; [Forecast Trust Core Normative Contracts](TRUST_CORE_CONTRACTS.md) separates historical validation from current verifiability. These existing contracts govern their own semantics.

## 7. Acceptance Model

**Normative.** Four decisions remain distinct and sequentially scoped: (1) approval of this specification as a versioned package boundary; (2) acceptance or rejection of a separately identified Candidate Freeze Package; (3) Genesis `ManifestAcceptance` under its own policy, evidence, authority, and signature requirements; and (4) separate explicit Genesis authorization after independent final validation and readiness closure. Approval of this specification does not approve a package. Package acceptance does not constitute Genesis `ManifestAcceptance` or authorize Genesis. Successful final validation alone does not authorize Genesis.

**Normative.** A future package acceptance record must identify the exact candidate and applicable specification version, the exact evidence basis, an explicit `ACCEPT` or `REJECT` decision, unresolved and blocking findings, and its governing review authority. A rejected candidate cannot be treated as accepted; a consequential correction requires a new candidate or renewed review as its governing contract requires. This section defines review criteria only; it does not create that record or a Candidate Freeze Package.

**Normative.** C01 (confirmatory runtime authority), C05 (qualification transition and historical admission interface), and C06 (mandatory-cycle universe reconstruction and enforced routing) remain implementation-completeness blockers until independently resolved and verified. A package review must state the affected scope and cannot report implementation-complete acceptance while these findings remain open. C04’s historical Human Review limit must also be retained. No decision under this section resolves any of those findings by wording alone.

**Descriptive.** The existing [Genesis Manifest and Acceptance Procedure](GENESIS_MANIFEST_PROCEDURE.md) and [Trusted Manifest Contract](TRUSTED_MANIFEST.md) govern the later Genesis transitions. This first draft is a specification artifact only. Candidate Freeze remains `NOT AUTHORIZED`; Genesis remains `NOT STARTED`; Forecast Ledger remains `NOT CREATED`; no forecast has been issued; no production qualification has been established.
