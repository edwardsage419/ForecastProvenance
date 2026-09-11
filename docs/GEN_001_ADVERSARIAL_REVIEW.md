# GEN_001 Adversarial Readiness Review

Date: 2026-09-11
Review target: Genesis readiness candidate on design/gen-001
Disposition: EXTERNAL READINESS BLOCKERS REMAIN

## Review objective

Attack the proposed Genesis trust root, time evidence, manifest acceptance, target admissibility, evaluation, and zero-cost operating assumptions before Forecast Ledger Genesis can occur.

## G-B01 Single wall-clock provider concentration

Severity: BLOCKING, RESOLVED IN DESIGN

DEADLINE_RECEIPT_QUORUM_V1 requires two independent provider groups. At least one qualifying receipt must be RFC 3161. Provider outage never lowers quorum.

## G-B02 Bitcoin block time used as precise forecast clock

Severity: BLOCKING, RESOLVED IN DESIGN

Wall-clock deadline evidence and Bitcoin durability evidence are separate. Bitcoin block header time cannot replace signed deadline receipts.

## G-B03 RFC 3161 accuracy and provider-profile ambiguity

Severity: BLOCKING FOR GEN_001 EXIT, OPEN

A generic provider statement cannot be applied to an arbitrary timestamp token.

Required closure:

Run non-forecast rehearsals for every RFC 3161 provider that will count toward quorum. Freeze raw request and response bytes, signer chain fingerprints, policy OID, nonce behavior, accuracy field or exact hashed accuracy policy, revocation capture procedure, and verifier output.

A receipt without a defensible conservative upper time bound cannot count toward deadline quorum.

## G-B04 Roughtime protocol and provider stability

Severity: HIGH, OPEN FOR QUORUM ELIGIBILITY

Roughtime remains optional for Genesis version 1.

It becomes quorum eligible only after freezing the exact protocol version, root key, verifier version, response contract, and successful non-forecast rehearsal evidence.

Genesis must remain operable with accepted RFC 3161 profiles if Roughtime is excluded.

## G-B05 Long-term RFC 3161 verification degradation

Severity: BLOCKING, RESOLVED IN DESIGN SUBJECT TO REHEARSAL

At stamping time retain content-addressed request bytes, response bytes, signer certificate, required chain, provider policy, and required revocation evidence.

Rehearsal must demonstrate the exact capture procedure.

## G-B06 OTS completion after outcome disclosure

Severity: BLOCKING, RESOLVED IN DESIGN

After strong OTS verification, create a DurabilityVerificationRecord and obtain deadline receipt quorum for that exact record before the target outcome information barrier.

Late durability completion remains in historical evidence and is ineligible for the initial confirmatory cohort.

## G-B07 GitHub server timestamps as trust root

Severity: HIGH, RESOLVED IN DESIGN

GitHub timestamps may be auxiliary public witnesses only. They do not count toward deadline quorum or bootstrap authority.

## G-B08 Exact bootstrap authority key absent

Severity: BLOCKING FOR GEN_001 EXIT, OPEN

Ed25519 and the bootstrap root structure are selected. The exact owner public key has not been generated and frozen.

Required closure:

Generate the key on an owner-controlled local or offline machine. Keep the private key outside GitHub, CI, repository fixtures, and ChatGPT-managed artifacts. Only the public key enters BootstrapGovernanceRoot.

## G-B09 Bootstrap self-authorization

Severity: BLOCKING, RESOLVED IN DESIGN

A separate GenesisGovernanceEnvelope containing the bootstrap root and acceptance policy must receive external time evidence before the candidate Genesis manifest can rely on it.

## G-B10 Manifest acceptance backdating

Severity: BLOCKING, RESOLVED IN DESIGN

The signed ManifestAcceptance itself receives FPP_TIME_EVIDENCE_V1 evidence. The first issuance execution window begins strictly after final acceptance verification.

## G-B11 Outcome disclosure before nominal release

Severity: BLOCKING FOR TARGETS, RESOLVED AT POLICY LEVEL

Initial targets require an independently defined outcome information barrier and a 24-hour issuance safety margin. Schedule advances and early disclosure fail closed under GENESIS_SCHEDULE_POLICY.md.

## G-B12 High-frequency target incompatibility

Severity: HIGH, RESOLVED IN DESIGN

Genesis version 1 requires at least a seven-calendar-day forecast horizon and excludes intraday and same-day targets.

## G-B13 Provider substitution after failed receipt

Severity: HIGH, RESOLVED IN DESIGN

Accepted provider profiles and quorum policy are bound in the Genesis manifest. Failed attempts remain operational records and cannot justify silent provider substitution.

## G-B14 Correlated upstream UTC infrastructure

Severity: MEDIUM, ACCEPTED WITH DISCLOSURE

The protocol claims a quorum of independently operated signed time authorities. It does not claim mathematically independent realizations of UTC.

## G-B15 Live provider rehearsal unavailable in current assistant environment

Severity: BLOCKING FOR GEN_001 EXIT, OPEN

A FreeTSA non-forecast rehearsal was prepared, while external DNS was unavailable in the current execution environment. No provider request was completed.

Required closure:

Run provider rehearsals from a networked owner-controlled environment. Preserve successful and failed attempts. The current environment limitation is not classified as provider failure.

## G-B16 Strong OpenTimestamps verification not yet executed

Severity: BLOCKING FOR GEN_001 EXIT, OPEN

Required closure:

Perform at least one non-forecast OTS stamp, proof upgrade, and strong verification against an owner-controlled pruned or full Bitcoin Core node. Retain proof bytes and a content-addressed verification report.

## G-B17 Initial target set unspecified

Severity: BLOCKING, RESOLVED TO CANDIDATE SET

A three-target candidate set is now selected before any production forecast values are generated:

1. CPI all-items monthly change, seasonally adjusted, first release.
2. Official U-3 unemployment rate, seasonally adjusted, first release.
3. Real GDP quarter-over-quarter annualized growth, Advance Estimate.

Target-specific review found the set viable. Exact TargetDefinition and ResolutionRule objects, parser fixtures, precision rules, and archive procedures remain required before manifest freeze.

## G-B18 Evaluation policy dependent on target type

Severity: BLOCKING, RESOLVED IN DESIGN

All three candidate targets use continuous scalar point forecasts under Genesis version 1.

GENESIS_EVALUATION_POLICY.md freezes absolute error, squared error, target-specific aggregation, complete cohort accounting, and prohibition of an authoritative universal cross-target score.

GENESIS_BASELINE_METHOD.md freezes a deterministic point-in-time last-observed-value baseline using archived first-release artifacts.

## G-B19 Baseline can leak later revisions

Severity: BLOCKING, RESOLVED IN DESIGN SUBJECT TO FIXTURE TESTING

The baseline may use only the immediately preceding first-release official artifact that was available by the current information cutoff.

Current revised historical databases are inadmissible substitutes.

Required closure:

Archived non-production fixtures must demonstrate rejection of later revised artifacts and exact target-specific extraction.

## G-B20 Official release pages can mutate after publication

Severity: BLOCKING FOR SOURCE IMPLEMENTATION, OPEN

A URL is insufficient as a durable first-release identity.

Required closure:

For each candidate target, validate a content-addressed archive procedure and parser against archived non-production official releases. When only a mutable official page exists, the frozen source rule requires a second official representation before full resolution trust.

## G-B21 Parser layout drift and displayed precision

Severity: BLOCKING FOR SOURCE IMPLEMENTATION, OPEN

Hard-coded HTML positions or implicit hidden precision could change outcomes.

Required closure:

Build target-specific parsers that bind semantic labels, reference period, units, seasonal-adjustment status, estimate type, and displayed precision. Rehearsal fixtures must include mutation and layout-failure cases.

## G-B22 Cross-target composite score could obscure heterogeneous scales

Severity: HIGH, RESOLVED IN DESIGN

Genesis version 1 prohibits an authoritative single aggregate score across the three target definitions. Reporting remains target-specific with transparent baseline deltas.

## Current disposition

The Genesis architecture is viable. The remaining blockers have moved from broad scientific architecture to externally verifiable readiness work and source-parser evidence.

GEN_001 cannot exit until all of the following are complete:

1. At least two qualifying independent wall-clock provider profiles with successful live non-forecast rehearsals, including at least one RFC 3161 provider.
2. Exact owner Ed25519 bootstrap public key frozen in BootstrapGovernanceRoot.
3. Non-forecast OpenTimestamps stamp, upgrade, and strong Bitcoin Core verification.
4. Target-specific official source archive and parser fixtures for CPI, U-3, and GDP Advance Estimate.
5. Exact TargetDefinition, ResolutionRule, source, schedule, baseline, and evaluation object hashes prepared for the candidate Genesis manifest.
6. Final Genesis readiness adversarial review with no blocking finding.

Forecast Ledger Genesis and genuine prospective forecasting remain prohibited.