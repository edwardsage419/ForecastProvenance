# GEN_001 Readiness Evidence Matrix

Date: 2026-09-11
Status: ACTIVE REVIEW CONTROL

## Purpose

This matrix is the authoritative checklist for closing GEN_001.

A readiness item closes only when the required evidence exists, is content addressed where applicable, and passes the stated review rule. Narrative confidence or successful execution without retained evidence does not close an item.

## Status values

`CLOSED_DESIGN`: normative design is complete and no further design choice is needed before external instantiation.

`CLOSED_REPOSITORY`: repository implementation or synthetic evidence is complete.

`OWNER_ACTION_REQUIRED`: completion requires an owner-controlled local or networked environment.

`EXTERNAL_EVIDENCE_REQUIRED`: a real external provider, official source, or Bitcoin verification record is required.

`FINAL_FREEZE_REQUIRED`: all dependencies must be fixed before the exact final object can be sealed.

## Evidence matrix

| ID | Readiness item | Current status | Required closing evidence |
| --- | --- | --- | --- |
| GR001 | Trust Core normative contract | CLOSED_REPOSITORY | FTC_001 frozen v0.4 and merged implementation |
| GR002 | Trust Core synthetic adversarial execution | CLOSED_REPOSITORY | ADV001 through ADV096 executable synthetic results |
| GR003 | Dual external time architecture | CLOSED_DESIGN | FPP_TIME_EVIDENCE_V1 design and adversarial disposition |
| GR004 | Deadline receipt quorum rule | CLOSED_DESIGN | DEADLINE_RECEIPT_QUORUM_V1 requiring two independent groups and at least one RFC 3161 provider |
| GR005 | RFC 3161 provider profile A | OWNER_ACTION_REQUIRED | Raw request and response, exact signer and chain, policy OID, accuracy rule, nonce behavior, revocation material, verifier report, hashes |
| GR006 | RFC 3161 provider profile B or independently qualified second provider group | OWNER_ACTION_REQUIRED | Same retained evidence standard as GR005 and independent provider-group classification |
| GR007 | Optional Roughtime provider | EXTERNAL_EVIDENCE_REQUIRED | Exact protocol version, root key, successful nonce-bound rehearsal, verifier version. Optional for Genesis v1 if two RFC 3161 groups qualify |
| GR008 | OpenTimestamps non-forecast rehearsal | OWNER_ACTION_REQUIRED | Stamp file, upgraded proof bytes, subject hash, command and verifier versions |
| GR009 | Strong Bitcoin verification | OWNER_ACTION_REQUIRED | Verification against owner-controlled Bitcoin Core, retained block and proof report sufficient for independent replay |
| GR010 | Bootstrap governance contract | CLOSED_DESIGN | GenesisGovernanceEnvelope and ManifestAcceptance procedure |
| GR011 | Owner Ed25519 bootstrap public key | OWNER_ACTION_REQUIRED | Locally generated public key only. Private key never enters repository, GitHub, CI, or ChatGPT artifacts |
| GR012 | Initial target selection policy | CLOSED_DESIGN | Admissibility rules and target-specific adversarial review |
| GR013 | Initial target semantic definitions | CLOSED_REPOSITORY | Three sealed TargetDefinition candidates in effective object lineage |
| GR014 | Initial ResolutionRule objects | CLOSED_REPOSITORY | Three sealed resolution candidates with full target/source bindings |
| GR015 | BLS and BEA SourceContract candidates | CLOSED_REPOSITORY | Six sealed source-contract candidates |
| GR016 | Semantic target parser | CLOSED_REPOSITORY | Synthetic fail-closed parser tests for CPI, U-3, GDP Advance semantics, ambiguity, precision, and source constraints |
| GR017 | Real official archive fixture: CPI | EXTERNAL_EVIDENCE_REQUIRED | Retained official first-release bytes, SHA256, retrieval evidence, adapter output, semantic parser report |
| GR018 | Real official archive fixture: U-3 | EXTERNAL_EVIDENCE_REQUIRED | Retained official first-release bytes, SHA256, retrieval evidence, adapter output, semantic parser report |
| GR019 | Real official archive fixture: GDP Advance | EXTERNAL_EVIDENCE_REQUIRED | Retained official first-release bytes, SHA256, retrieval evidence, adapter output, semantic parser report |
| GR020 | Issuance schedule policy | CLOSED_REPOSITORY | Sealed v0.3 schedule policy, one cycle per target release instance, predecessor hash validation |
| GR021 | Initial method set | CLOSED_REPOSITORY | Only method:last-observed-value:v1 admitted in Genesis candidate lineage |
| GR022 | Baseline point-in-time binding | CLOSED_REPOSITORY | Full target hashes, first-release-only input rule, revised database fallback prohibited |
| GR023 | Evaluation policy | CLOSED_REPOSITORY | Target-specific absolute error, squared error, baseline delta, cohort retention semantics |
| GR024 | Retry policy | CLOSED_REPOSITORY | Sealed policy: max attempts, eligible failure codes, first-success rule, retained attempts |
| GR025 | Omission policy | CLOSED_REPOSITORY | Sealed policy with explicit omission codes and mandatory release-instance visibility |
| GR026 | Correction policy | CLOSED_REPOSITORY | Sealed policy with substantive replacement and cohort rules |
| GR027 | Retention policy | CLOSED_REPOSITORY | Sealed indefinite content-addressed retention and second owner-controlled copy requirement |
| GR028 | Human review policy | CLOSED_REPOSITORY | Sealed authority and hard-override prohibitions |
| GR029 | Genesis acceptance policy | CLOSED_REPOSITORY | Sealed acceptance dependencies and first-execution-after-final-acceptance rule |
| GR030 | Candidate object dependency closure | CLOSED_REPOSITORY | Effective v0.3 lineage: v0.2 base plus v0.3 patch, 22 objects, full refs close exactly |
| GR031 | Exact Genesis validator implementation binding | FINAL_FREEZE_REQUIRED | Final accepted source tree or artifact hash, validator contract identity, test report, runtime requirements |
| GR032 | Final BootstrapGovernanceRoot | FINAL_FREEZE_REQUIRED | GR011 public key plus frozen acceptance rule and canonical sealed object |
| GR033 | Final provider profiles | FINAL_FREEZE_REQUIRED | Successful GR005 and GR006 evidence converted into sealed provider-profile objects |
| GR034 | Final OTS Bitcoin verifier profile | FINAL_FREEZE_REQUIRED | Successful GR008 and GR009 evidence plus frozen verifier semantics |
| GR035 | Candidate Genesis TrustedManifest | FINAL_FREEZE_REQUIRED | Exact full-hash refs to all accepted targets, methods, policies, sources, provider profiles, bootstrap and validator contracts |
| GR036 | ManifestAcceptance signature | FINAL_FREEZE_REQUIRED | Owner Ed25519 signature over exact candidate manifest under accepted rule |
| GR037 | Manifest and acceptance external time evidence | FINAL_FREEZE_REQUIRED | FPP_TIME_EVIDENCE_V1 evidence satisfying the Genesis acceptance protocol |
| GR038 | Final readiness adversarial review | FINAL_FREEZE_REQUIRED | No unresolved blocking finding across governance, time, source, schedule, manifest, and retention paths |
| GR039 | Genesis acceptance decision | OUTSIDE GEN_001 | Separate explicit decision after GEN_001 closes. This is the only step that can authorize Forecast Ledger Genesis |

## Fail-closed rule

Any item from GR005 through GR038 that is required by the selected final Genesis profile and remains unclosed blocks GEN_001 exit.

Optional mechanisms can be excluded only before final manifest freeze and only when the remaining selected mechanisms still satisfy every accepted invariant and quorum rule.

## Evidence handling rule

Rehearsal outputs are permanently labeled non-prospective.

Successful rehearsal evidence may justify freezing a provider or verifier profile. It never becomes a native forecast record.

Failures are retained when they materially inform provider eligibility, operational reliability, or abort rules.

## Current boundary

Repository design and candidate-object work is substantially closed through GR030.

The remaining critical path begins with owner-controlled external evidence at GR005, GR006, GR008, GR009, and GR011, plus real official archive fixtures GR017 through GR019. Final object freezing then proceeds through GR031 to GR038.