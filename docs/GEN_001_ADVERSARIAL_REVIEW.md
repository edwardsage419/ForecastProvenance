# GEN_001 Adversarial Readiness Review

Date: 2026-09-11
Review target: Genesis readiness candidate on design/gen-001
Disposition: BLOCKING READINESS ITEMS REMAIN

## Review objective

Attack the proposed Genesis trust root, time evidence, manifest acceptance, target admissibility, and operational zero cost assumptions before any Forecast Ledger Genesis can occur.

## G-B01 Single wall clock provider would create excessive trust concentration

Severity: BLOCKING, RESOLVED IN DESIGN

A single TSA or Roughtime server could issue an incorrect or compromised time claim.

Resolution:

DEADLINE_RECEIPT_QUORUM_V1 requires two independent provider groups. At least one qualifying receipt must be RFC 3161. Provider outage never lowers quorum.

## G-B02 Bitcoin block time is unsuitable as the precise forecast deadline clock

Severity: BLOCKING, RESOLVED IN DESIGN

OpenTimestamps can establish durable Bitcoin inclusion, while Bitcoin header time does not provide the precise wall clock semantics required for a forecast cutoff.

Resolution:

Wall clock deadline evidence and Bitcoin durability evidence are separate. Block header time cannot replace signed deadline receipts.

## G-B03 RFC 3161 token accuracy may be absent or unrelated to a cited provider policy

Severity: BLOCKING, OPEN

RFC 3161 allows accuracy to be omitted. A generic provider accuracy statement cannot be applied to a token unless the frozen signer, policy OID, chain, and policy actually correspond.

Required closure:

Run non forecast rehearsals for each RFC 3161 provider. Freeze raw token examples, signer chain fingerprints, policy OID, nonce behavior, accuracy field or hashed policy accuracy statement, CRL or OCSP capture procedure, and verifier output.

A token with no defensible conservative accuracy cannot count toward quorum.

## G-B04 Roughtime protocol and provider profiles remain operationally unstable

Severity: HIGH, OPEN FOR QUORUM ELIGIBILITY

Cloudflare labels its Roughtime service beta and states its root key may change. The associated implementation also tracks evolving IETF drafts.

Required closure:

Roughtime is optional in Genesis version 1. It becomes quorum eligible only after a provider profile freezes the exact protocol version, root key, verifier version, response format, and successful rehearsal evidence.

Genesis must remain operable using accepted RFC 3161 provider profiles if Roughtime is excluded.

## G-B05 Long term RFC 3161 verification can degrade after certificate expiry or revocation information disappears

Severity: BLOCKING, RESOLVED IN DESIGN SUBJECT TO REHEARSAL

Resolution:

At stamping time retain content addressed request bytes, response bytes, signer certificate, required chain, provider policy, and required CRL or OCSP evidence. Retention failure degrades current verifiability and cannot be silently ignored.

Rehearsal must demonstrate the exact capture procedure.

## G-B06 Delayed OTS completion could occur after outcome information becomes public

Severity: BLOCKING, RESOLVED IN DESIGN

A valid pre deadline TSA receipt plus a much later OTS completion should not be promoted silently into the initial confirmatory cohort.

Resolution:

After strong OTS verification, create a DurabilityVerificationRecord and obtain deadline receipt quorum for that exact record before the target outcome information barrier. Late durability completion is recorded but initial confirmatory eligibility fails closed.

## G-B07 GitHub server timestamps are platform evidence rather than portable signed time receipts

Severity: HIGH, RESOLVED IN DESIGN

Resolution:

GitHub timestamps may be auxiliary witnesses only. They do not count toward deadline quorum or bootstrap authority.

## G-B08 Bootstrap governance remains unresolved without the exact owner key

Severity: BLOCKING, OPEN

The structure and Ed25519 algorithm are selected, while the exact owner public key has not been generated and frozen.

Required closure:

The owner generates the key offline or on an owner controlled local machine. The private key remains outside GitHub, CI, repository fixtures, and ChatGPT managed artifacts. Only the public key enters BootstrapGovernanceRoot.

## G-B09 Bootstrap root could still self authorize if it is first introduced by the candidate manifest

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

A separate GenesisGovernanceEnvelope containing the bootstrap root and acceptance policy must receive external time evidence before the candidate Genesis manifest can rely on it.

## G-B10 Manifest acceptance could be backdated after the first production cycle starts

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

The signed ManifestAcceptance itself must receive FPP_TIME_EVIDENCE_V1 evidence. The first issuance execution window begins strictly after final acceptance verification.

## G-B11 Target release timing could leak outcome information before a nominal release timestamp

Severity: BLOCKING FOR TARGETS, RESOLVED AT POLICY LEVEL

Resolution:

Initial targets require an independently defined outcome information barrier and a 24 hour issuance safety margin. Targets with unscheduled early disclosure risk that cannot be handled deterministically are excluded.

Exact target candidates still require individual review.

## G-B12 High frequency targets are incompatible with the initial external time evidence operating model

Severity: HIGH, RESOLVED IN DESIGN

Resolution:

Genesis version 1 requires at least a seven day forecast horizon and excludes intraday, same day, and next hour targets.

## G-B13 Provider selection could be changed after observing a failed or inconvenient receipt

Severity: HIGH, RESOLVED IN DESIGN

Resolution:

Accepted provider profiles and quorum policy are bound in the Genesis manifest. Receipts from unlisted providers cannot qualify. Failed provider attempts remain operational records and cannot justify silent provider substitution.

## G-B14 Two provider groups may share correlated upstream time sources

Severity: MEDIUM, ACCEPTED WITH DISCLOSURE

Independent provider operation does not prove fully independent upstream UTC realization.

Disposition:

The protocol requires independent operators and retains provider time source disclosures where available. It does not claim statistical independence of global UTC infrastructure. The wall clock claim is therefore a quorum of independent signed authorities, not a mathematically independent time ensemble.

## G-B15 Rehearsal success from the assistant execution environment is unavailable

Severity: BLOCKING FOR GEN_001 EXIT, OPEN

A FreeTSA non forecast rehearsal was attempted. External DNS is unavailable in the execution environment, so the request did not reach the provider.

Required closure:

Run provider and OTS rehearsals from a networked owner controlled environment. Preserve both successes and failures. This environment limitation is not classified as a provider outage.

## G-B16 Strong OpenTimestamps verification has not been executed with a locally controlled Bitcoin node

Severity: BLOCKING FOR GEN_001 EXIT, OPEN

OpenTimestamps documentation states that creation can use remote calendars while verification requires Bitcoin Core, with pruned mode acceptable.

Required closure:

Perform at least one non forecast OTS stamp, upgrade, and strong verification against an owner controlled pruned or full Bitcoin Core node. Retain proof bytes and verification report.

## G-B17 Initial production target set remains unspecified

Severity: BLOCKING FOR GEN_001 EXIT, OPEN

Target admissibility rules are now defined, but the exact initial TargetDefinition, ResolutionRule, SourceContract, schedule binding, and scoring rule set has not been frozen.

Required closure:

Select a minimal candidate set without generating forecast values, then conduct target specific adversarial review.

## G-B18 Genesis evaluation policy cannot freeze before target outcome types are selected

Severity: BLOCKING FOR GEN_001 EXIT, OPEN

Scoring rules depend on whether initial targets are binary, categorical, continuous, or distributional.

Required closure:

Freeze target set first, then bind target compatible scoring rules and transparent baselines in the candidate Genesis manifest.

## Current disposition

The core Genesis architecture is viable and materially stronger than the original OTS only design.

The following readiness blockers remain:

1. Exact RFC 3161 provider profiles and live rehearsals.
2. Optional Roughtime profile rehearsal if retained.
3. Exact owner Ed25519 bootstrap public key.
4. Strong OTS rehearsal against an owner controlled Bitcoin Core node.
5. Exact minimal initial target set.
6. Target compatible evaluation and baseline policies.

Forecast Ledger Genesis and genuine prospective forecasting remain prohibited.