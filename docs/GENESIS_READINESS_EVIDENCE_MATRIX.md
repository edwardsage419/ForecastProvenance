# GEN_001 Readiness Evidence Matrix

Date: 2026-09-13
Status: ACTIVE REVIEW CONTROL

## Purpose

This matrix is the authoritative checklist for closing GEN_001.

A readiness item closes only when the required evidence exists, is content addressed where applicable, and passes the stated review rule. Narrative confidence or successful execution without retained evidence does not close an item.

## Status values

`CLOSED_DESIGN`: normative design is complete and no further design choice is needed before external instantiation.

`CLOSED_REPOSITORY`: repository implementation or synthetic evidence is complete.

`OWNER_ACTION_REQUIRED`: completion requires an owner controlled local or networked environment.

`EXTERNAL_EVIDENCE_REQUIRED`: a real external provider, official source, or Bitcoin verification record is required.

`FINAL_FREEZE_REQUIRED`: all dependencies must be fixed before the exact final object can be sealed.

`PRODUCTION_QUALIFICATION_REQUIRED`: frozen production criteria exist, but the provider has not passed them and no production ProviderProfile or QualificationDecision has been sealed.

## Current Roughtime stage boundary

| Stage | Current state | Consequence |
| --- | --- | --- |
| Execution orchestrator | PUBLISHED_AND_OFFLINE_VERIFIED | The repository-owned persist-before-send and verification path exists; this does not authorize a new request |
| Non-forecast rehearsal execution | COMPLETED_3_OF_3_QUALIFYING | The exact authorization was consumed and cannot be reused |
| Rehearsal evidence review | PASS | Retained evidence supports later independent qualification review |
| Production qualification criteria | FROZEN_V1 | `FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1` is frozen by exact SHA256 `88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e`; this does not qualify a provider |
| Production qualification object model | PUBLISHED_HARDENED_CANDIDATE | Seven production schemas, semantic validators, authoritative package closure, signed-decision projection, requalification events, and deterministic state derivation exist |
| Production schema meta-validation | PASS_7_OF_7 | Exact committed schema bytes passed Draft 2020-12 `check_schema`; this does not replace repository regression or semantic validation |
| Ed25519 decision verification backend | PUBLISHED_CANDIDATE_NOT_FINAL_QUALIFIED | Verification-only Go standard-library backend exists; final content-addressed Go 1.27.x build qualification remains required |
| Production qualification execution | NOT_READY_REGRESSION_FINAL_BUILD_AUTHORITY_GATE | Exact current-HEAD full regression, final signature-backend build qualification, external owner public-key identity, and provider-specific qualification evidence remain open |
| Genesis readiness | NOT_READY | Roughtime production qualification and other GR items remain open |

## Evidence matrix

| ID | Readiness item | Current status | Required closing evidence |
| --- | --- | --- | --- |
| GR001 | Trust Core normative contract | CLOSED_REPOSITORY | FTC_001 frozen v0.4 and merged implementation |
| GR002 | Trust Core synthetic adversarial execution | CLOSED_REPOSITORY | ADV001 through ADV096 executable synthetic results |
| GR003 | Dual external time architecture | CLOSED_DESIGN | FPP_TIME_EVIDENCE_V1 design separating wall clock deadline evidence from Bitcoin durability |
| GR004 | Deadline receipt quorum rule | CLOSED_REPOSITORY | `policy:deadline-receipt-quorum:v3` requiring two of three frozen independent Roughtime provider groups, zero recurring cash cost, provider outage never lowering quorum, and exact protocol/control bindings |
| GR005 | Roughtime provider profile: roughtime.se | PRODUCTION_QUALIFICATION_REQUIRED | Frozen criteria, reviewed retained evidence, two-event repeatability under the exact profile, current permission basis, positive root/issuance independence evidence, complete scanned evidence package, independent review, explicit owner-authorized QualificationDecision, and sealed ProviderProfile |
| GR006 | Roughtime provider profile: time.txryan.com | PRODUCTION_QUALIFICATION_REQUIRED | Same retained evidence standard as GR005, including independent issuance/root-control classification and correlated-software risk review |
| GR007 | Roughtime provider profile: TimeNL-Roughtime | PRODUCTION_QUALIFICATION_REQUIRED | Same retained evidence standard as GR005 plus the frozen pilot conditions: explicit automated production-use permission, at least 90 days continuity evidence, current pilot/transition review, and no specific operator production prohibition |
| GR008 | OpenTimestamps non forecast rehearsal | OWNER_ACTION_REQUIRED | Stamp file, upgraded proof bytes, subject hash, command and verifier versions |
| GR009 | Strong Bitcoin verification | OWNER_ACTION_REQUIRED | Verification against owner controlled Bitcoin Core, retained block and proof report sufficient for independent replay |
| GR010 | Bootstrap governance contract | CLOSED_DESIGN | GenesisGovernanceEnvelope and ManifestAcceptance procedure |
| GR011 | Owner Ed25519 bootstrap public key | OWNER_ACTION_REQUIRED | Locally generated public key only. Private key never enters repository, GitHub, CI, connected tools, or ChatGPT artifacts |
| GR012 | Initial target selection policy | CLOSED_DESIGN | Admissibility rules and target specific adversarial review |
| GR013 | Initial target semantic definitions | CLOSED_REPOSITORY | Three sealed TargetDefinition candidates in effective object lineage |
| GR014 | Initial ResolutionRule objects | CLOSED_REPOSITORY | Three sealed resolution candidates with full target and source bindings |
| GR015 | BLS and BEA SourceContract candidates | CLOSED_REPOSITORY | Six sealed source contract candidates |
| GR016 | Semantic target parser | CLOSED_REPOSITORY | Synthetic fail closed parser tests for CPI, U-3, GDP Advance semantics, ambiguity, precision, and source constraints |
| GR017 | Real official archive fixture: CPI | EXTERNAL_EVIDENCE_REQUIRED | Retained official first release bytes, SHA256, retrieval evidence, adapter output, semantic parser report |
| GR018 | Real official archive fixture: U-3 | EXTERNAL_EVIDENCE_REQUIRED | Retained official first release bytes, SHA256, retrieval evidence, adapter output, semantic parser report |
| GR019 | Real official archive fixture: GDP Advance | EXTERNAL_EVIDENCE_REQUIRED | Retained official first release bytes, SHA256, retrieval evidence, adapter output, semantic parser report |
| GR020 | Issuance schedule policy | CLOSED_REPOSITORY | Sealed v0.3 schedule policy, one cycle per target release instance, predecessor hash validation |
| GR021 | Initial method set | CLOSED_REPOSITORY | Only method:last-observed-value:v1 admitted in Genesis candidate lineage |
| GR022 | Baseline point in time binding | CLOSED_REPOSITORY | Full target hashes, first release only input rule, revised database fallback prohibited |
| GR023 | Evaluation policy | CLOSED_REPOSITORY | Target specific absolute error, squared error, baseline delta, cohort retention semantics |
| GR024 | Retry policy | CLOSED_REPOSITORY | Sealed policy: max attempts, eligible failure codes, first success rule, retained attempts |
| GR025 | Omission policy | CLOSED_REPOSITORY | Sealed policy with explicit omission codes and mandatory release instance visibility |
| GR026 | Correction policy | CLOSED_REPOSITORY | Sealed policy with substantive replacement and cohort rules |
| GR027 | Retention policy | CLOSED_REPOSITORY | Sealed indefinite content addressed retention and second owner controlled copy requirement |
| GR028 | Human review policy | CLOSED_REPOSITORY | Sealed authority and hard override prohibitions |
| GR029 | Genesis acceptance policy | CLOSED_REPOSITORY | Sealed acceptance dependencies and first execution after final acceptance rule |
| GR030 | Candidate object dependency closure | CLOSED_REPOSITORY | Effective v0.5 lineage: v0.2 base plus v0.3, v0.4, and v0.5 patches, 22 objects, exact retirement predecessor hashes, full refs close exactly |
| GR031 | Exact Genesis validator implementation binding | FINAL_FREEZE_REQUIRED | Final accepted source tree or artifact hash, validator contract identity, test report, runtime requirements |
| GR032 | Final BootstrapGovernanceRoot | FINAL_FREEZE_REQUIRED | GR011 public key plus frozen acceptance rule and canonical sealed object |
| GR033 | Final Roughtime provider profiles | FINAL_FREEZE_REQUIRED | GR005, GR006, and GR007 closed under `FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1`, followed by three separately sealed ProviderProfile objects matching the frozen quorum pool |
| GR034 | Final OTS Bitcoin verifier profile | FINAL_FREEZE_REQUIRED | Successful GR008 and GR009 evidence plus frozen verifier semantics |
| GR035 | Candidate Genesis TrustedManifest | FINAL_FREEZE_REQUIRED | Exact full hash refs to all accepted targets, methods, policies, sources, three Roughtime provider profiles, bootstrap and validator contracts |
| GR036 | ManifestAcceptance signature | FINAL_FREEZE_REQUIRED | Owner Ed25519 signature over exact candidate manifest under accepted rule |
| GR037 | Manifest and acceptance external time evidence | FINAL_FREEZE_REQUIRED | FPP_TIME_EVIDENCE_V1 evidence satisfying `policy:deadline-receipt-quorum:v3` |
| GR038 | Final readiness adversarial review | FINAL_FREEZE_REQUIRED | No unresolved blocking finding across governance, time, source, schedule, manifest, cost, and retention paths |
| GR039 | Genesis acceptance decision | OUTSIDE GEN_001 | Separate explicit decision after GEN_001 closes. This is the only step that can authorize Forecast Ledger Genesis |

## RFC 3161 status

RFC 3161 is outside the selected minimum Genesis quorum profile.

Existing RFC 3161 rehearsal evidence remains permanently retained under its historical classification and may be used as auxiliary corroboration.

RFC 3161 checker engineering remains closed at version 1.3 and report schema 1.2 absent a new concrete correctness or security defect.

No commercial RFC 3161 entitlement is required to close GR004 through GR007 under the selected version 3 profile.

## Fail closed rule

Any item from GR005 through GR038 that is required by the selected final Genesis profile and remains unclosed blocks GEN_001 exit.

The three Roughtime ProviderProfiles must all be frozen before Genesis acceptance because the quorum pool itself is fixed at three.

For each actual deadline evidence event, at least two of those three provider groups must independently qualify.

Provider outage never lowers the threshold.

## Evidence handling rule

Rehearsal outputs are permanently labeled non prospective.

Successful rehearsal evidence may satisfy individual frozen qualification criteria after independent review. It never becomes a native forecast record and never changes historical classification.

Production qualification evidence must be validated through the authoritative package-root hardening path. A caller-selected in-memory artifact list is not sufficient proof of complete retained package closure.

Failures are retained when they materially inform provider eligibility, operational reliability, or abort rules.

## Current boundary

Repository design and candidate object work is substantially closed through GR030 for the zero recurring cash cost candidate.

The Roughtime production qualification governance criteria are frozen as `FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1`. The production qualification object model, seven schemas, signature projection, evidence-package hardening, and verification-only Ed25519 backend candidate now exist. Exact committed schema bytes passed Draft 2020-12 meta-validation.

The repository-wide regression for the current exact branch HEAD remains pending. The signature backend also requires final content-addressed build qualification under the accepted Go 1.27.x toolchain. GR011 owner public-key input remains required before an owner-authorized QualificationDecision can exist.

GR005 through GR007 remain open on actual frozen-criteria evidence review, repeatability, production-use permission, positive independence evidence, current metadata, production qualification decisions, and separately sealed ProviderProfiles. No provider is production qualified.

The other external critical path continues through GR008, GR009, and GR011, plus real official archive fixtures GR017 through GR019.

Final object freezing then proceeds through GR031 to GR038.

No Roughtime request is authorized by this matrix.
