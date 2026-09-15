# GEN_001 Adversarial Readiness Review

Date: 2026-09-11
Review target: Genesis readiness candidate on design/gen-001
Disposition: HISTORICAL PRE-V3 REVIEW; BLOCKING READINESS ITEMS REMAIN WHERE NOT LATER SUPERSEDED

D026 and the current authoritative readiness matrix supersede this review's D015/RFC 3161-primary quorum and optional-Roughtime conclusions. The historical findings and evidence are retained; they are not current provider-selection or network-execution authority.

## Review objective

Attack the proposed Genesis trust root, time evidence, manifest acceptance, target admissibility, source resolution, operational completeness, and zero-cost assumptions before any Forecast Ledger Genesis can occur.

## G-B01 Single wall-clock provider would create excessive trust concentration

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

DEADLINE_RECEIPT_QUORUM_V1 requires two independent provider groups. At least one qualifying receipt must be RFC 3161. The current minimal operating plan aims to qualify both FreeTSA and DigiCert as independent RFC 3161 groups. Provider outage never lowers quorum.

## G-B02 Bitcoin block time is unsuitable as the precise forecast deadline clock

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

Wall-clock deadline evidence and Bitcoin durability evidence are separate. Bitcoin block header time cannot replace signed deadline receipts.

## G-B03 RFC 3161 token accuracy may be absent or unrelated to a cited provider policy

Severity: BLOCKING, OWNER EVIDENCE REQUIRED

Required closure:

Run non-forecast rehearsals for each selected RFC 3161 provider. Freeze raw request and response bytes, signer and chain fingerprints, policy OID, nonce behavior, token accuracy or hashed provider accuracy statement, revocation capture procedure, tool versions, and verifier output.

A token with no defensible conservative upper time bound cannot count toward quorum.

## G-B04 Roughtime protocol and provider profile remain operationally mutable

Severity: NONBLOCKING FOR GENESIS V1 MINIMUM PROFILE

Disposition:

Cloudflare Roughtime is optional. Current official documentation still labels the service beta and warns that its root key may change. Genesis v1 can proceed without Roughtime if two independent RFC 3161 provider groups qualify.

If later enabled, Roughtime requires a separately frozen provider profile and successful nonce-bound rehearsal.

## G-B05 Long-term RFC 3161 verification can degrade after certificate expiry or revocation evidence disappears

Severity: BLOCKING, RESOLVED IN DESIGN SUBJECT TO REHEARSAL

Resolution:

At stamping time retain request bytes, response bytes, signer certificate, required chain, provider policy, required CRL or OCSP evidence, HTTP metadata, and verifier tool versions. Retention failure degrades current verifiability and cannot be silently ignored.

## G-B06 Delayed OTS completion could occur after outcome information becomes public

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

After strong OTS verification, create a DurabilityVerificationRecord and obtain deadline receipt quorum for that exact record before the target outcome information barrier. Late durability completion is recorded but initial confirmatory eligibility fails closed.

## G-B07 GitHub server timestamps are platform evidence rather than portable signed time receipts

Severity: HIGH, RESOLVED IN DESIGN

Resolution:

GitHub timestamps are auxiliary witnesses only. They do not count toward deadline quorum or bootstrap authority.

## G-B08 Bootstrap governance requires an exact owner key

Severity: BLOCKING, OWNER ACTION REQUIRED

Required closure:

The owner generates the Ed25519 key on an owner-controlled local machine. The private key remains outside GitHub, CI, repository fixtures, and ChatGPT-managed artifacts. Only the public key and its SHA256 enter BootstrapGovernanceRoot.

## G-B09 Bootstrap root could self-authorize if first introduced by the candidate manifest

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

A separate GenesisGovernanceEnvelope containing the bootstrap root and acceptance rule receives external time evidence before the candidate Genesis manifest relies on it.

## G-B10 Manifest acceptance could be backdated after the first cycle starts

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

Signed ManifestAcceptance itself must receive FPP_TIME_EVIDENCE_V1 evidence. The first issuance execution window begins strictly after final acceptance verification.

## G-B11 Target release timing could leak outcome information before nominal release time

Severity: BLOCKING FOR TARGETS, RESOLVED AT POLICY LEVEL

Resolution:

Initial targets require an independently defined outcome information barrier and a 24-hour external-proof safety margin. Targets with uncontrolled early-disclosure risk are excluded or fail closed.

## G-B12 High-frequency targets are incompatible with the initial operating model

Severity: HIGH, RESOLVED IN DESIGN

Resolution:

Genesis v1 excludes intraday and same-day targets and uses a seven-calendar-day information-cutoff horizon for the selected targets.

## G-B13 Provider selection could be changed after observing a failed receipt

Severity: HIGH, RESOLVED IN DESIGN

Resolution:

Accepted ProviderProfiles and quorum policy are bound in the Genesis TrustedManifest. Unlisted providers cannot qualify. Failed attempts remain operational records and do not authorize silent substitution.

## G-B14 Provider groups can share correlated upstream UTC sources

Severity: MEDIUM, ACCEPTED WITH DISCLOSURE

Disposition:

The protocol requires independent operators and records provider time-source disclosures where available. It does not claim mathematical independence of global UTC realization.

## G-B15 Assistant execution environment cannot supply accepted live provider rehearsal evidence

Severity: BLOCKING FOR GEN_001 EXIT, OWNER ACTION REQUIRED

Resolution path:

Use the owner-controlled runbook and preserve successes and failures. Environment limitations are not classified as provider outages.

## G-B16 Strong OpenTimestamps verification has not been executed with owner-controlled Bitcoin Core

Severity: BLOCKING FOR GEN_001 EXIT, OWNER ACTION REQUIRED

Required closure:

Perform at least one non-forecast OTS stamp, upgrade, and strong verification against owner-controlled Bitcoin Core. Retain proof bytes, node/verifier versions, and verification report.

## G-B17 Initial production target set was unspecified

Severity: BLOCKING, RESOLVED AS GEN_001 CANDIDATE

Resolution:

Three target candidates were selected without generating production forecast values: CPI monthly all-items SA change, U-3 SA unemployment rate, and real GDP Advance Estimate annualized growth. Target-specific adversarial review and sealed candidate definitions are present.

Final acceptance still depends on real official source fixtures and the separate Genesis acceptance decision.

## G-B18 Evaluation policy depended on target outcome type

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

All three initial candidates use continuous scalar point forecasts. Target-specific absolute error and squared error are retained, with deltas against the transparent baseline. Universal cross-target scoring is prohibited.

## G-B19 Transparent baseline could silently use revised historical data

Severity: BLOCKING, RESOLVED IN DESIGN AND CANDIDATE OBJECTS

Resolution:

The baseline binds the immediately preceding same-target first-release artifact available by cutoff. Revised database fallback is prohibited. The baseline method binds all three compatible target full hashes.

## G-B20 Different target release dates make a shared cycle ambiguous

Severity: BLOCKING, RESOLVED IN DESIGN AND CANDIDATE OBJECTS

Resolution:

Genesis v1 uses one cycle per official target release instance. Each cycle has one target instance, one information cutoff, one precommitment timeline, and all manifest-admitted compatible methods.

## G-B21 Initial method breadth could delay Genesis and increase selection surface

Severity: HIGH, RESOLVED BY MINIMAL METHOD SET

Resolution:

The initial Genesis candidate admits only `method:last-observed-value:v1`. Additional methods require an accepted successor manifest. This begins the real provenance clock with the smallest model and infrastructure surface.

## G-B22 Candidate object dependencies could drift across review versions

Severity: BLOCKING, RESOLVED AT REPOSITORY LEVEL

Resolution:

The effective candidate is v0.2 base plus v0.3 patch. Patch replacements require predecessor full-hash match. Repository tests verify effective count, sealed objects, full dependency closure, one-cycle-per-release semantics, and operational policy presence. A deterministic materializer emits an inventory and overall inventory SHA256.

## G-B23 Official first-release web layouts can change

Severity: BLOCKING FOR SOURCE READINESS, EXTERNAL EVIDENCE REQUIRED

Resolution path:

Semantic target parsing is separated from HTML layout. A retrospective fixture manifest fixes three already-public official releases and expected semantics. A constrained downloader retains raw official bytes and SHA256 from admitted hosts. Owner-controlled retrieval must still be executed and future source adapters must prove unique semantic extraction from those retained bytes.

## G-B24 A current provider website snapshot can be mistaken for a frozen ProviderProfile

Severity: HIGH, RESOLVED IN GOVERNANCE

Resolution:

`GENESIS_PROVIDER_SNAPSHOT_2026_09_11.md` is explicitly review input only. Provider eligibility requires live rehearsal evidence and a separately sealed ProviderProfile. Changed certificates, keys, endpoints, or policies produce new evidence and cannot rewrite the historical snapshot.

## G-B25 Rehearsal scripts could produce incomplete forensic metadata

Severity: HIGH, RESOLVED AT TOOLING LEVEL SUBJECT TO OWNER EXECUTION

Resolution:

RFC 3161 rehearsal now retains raw query/response, parsed forms, HTTP headers, tool versions, hashes, and nonce policy. The runbook maps required output to readiness evidence IDs. Actual owner-run artifacts remain required.

## G-B26 Final validator binding could drift after evidence rehearsals

Severity: BLOCKING FOR FINAL FREEZE, OPEN

Required closure:

At final candidate freeze, bind exact validator source/artifact hash, validator contract identity, runtime requirements, and final test report into the candidate Genesis TrustedManifest. Any later consequential validator change requires a new candidate or successor manifest.

## G-B27 Rehearsal evidence might be mislabeled as native history

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

All rehearsal manifests, source fixtures, scripts, and candidate objects carry non-prospective classification. Rehearsal success can qualify a profile but can never create a native forecast record.

## Current disposition

The core Genesis architecture, target set candidate, schedule model, baseline, evaluation, operational policies, semantic parser, candidate object lineage, provider planning, and rehearsal tooling are viable.

The remaining critical blockers are external or final-freeze items:

1. Two qualifying independent wall-clock provider rehearsals and sealed ProviderProfiles.
2. Owner Ed25519 public key.
3. Strong non-forecast OTS verification against owner-controlled Bitcoin Core.
4. Three retained real official source fixture byte sets and successful adapter reports.
5. Exact final validator binding.
6. Final candidate TrustedManifest and ManifestAcceptance construction.
7. Final readiness adversarial review with no blocking finding.

The authoritative closure evidence is tracked in `GENESIS_READINESS_EVIDENCE_MATRIX.md`.

Forecast Ledger Genesis and genuine prospective forecasting remain prohibited.
