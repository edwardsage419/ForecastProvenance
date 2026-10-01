# GEN_001 Zero Cost Time Evidence Adversarial Review

Date: 2026-09-11
Review target: zero recurring cash cost deadline evidence candidate
Disposition: HISTORICAL V2 REVIEW; LATER REHEARSAL EVIDENCE RETAINED SEPARATELY

D026 and candidate v0.5 supersede this review's v2 policy references. Its design findings remain historical evidence; current rehearsal and production-qualification status is controlled by the authoritative readiness matrix and current state documents.

## Scope

This review attacks the proposed move from an RFC 3161 minimum provider requirement to a fixed three provider Roughtime pool with a two receipt threshold.

It does not authorize provider requests.

## Z-B01 Removing mandatory RFC 3161 could overstate the resulting assurance

Severity: HIGH, RESOLVED BY CLAIM BOUNDARY

Disposition:

The project does not claim eIDAS qualified timestamp status, regulated electronic signature status, or commercial TSA SLA.

The accepted claim is cryptographic, reproducible precommitment evidence under the frozen trust model.

RFC 3161 remains optional auxiliary evidence.

## Z-B02 A single time operator would create excessive trust concentration

Severity: BLOCKING, RESOLVED IN DESIGN

Disposition:

`policy:deadline-receipt-quorum:v2` requires two independent provider groups.

The frozen pool contains exactly three groups and the threshold remains two.

## Z-B03 Provider outage could pressure the operator to lower quorum

Severity: BLOCKING, RESOLVED IN DESIGN

Disposition:

Provider outage never lowers quorum.

One valid provider receipt produces failure, not degraded acceptance.

## Z-B04 Provider substitution after observing failure could create selection discretion

Severity: BLOCKING, RESOLVED IN DESIGN

Disposition:

The three provider pool is frozen before Genesis acceptance.

Unlisted providers cannot substitute after a failed request.

Any pool change requires a versioned policy or manifest change before use.

## Z-B05 Root key rotation could silently change trust identity

Severity: BLOCKING, RESOLVED IN DESIGN

Disposition:

Each ProviderProfile freezes the exact Roughtime root public key.

A changed key is ineligible until a new ProviderProfile and accepted manifest change are complete.

Historical evidence remains bound to the historical key.

## Z-B06 Roughtime protocol evolution could change verification semantics

Severity: BLOCKING, RESOLVED IN DESIGN SUBJECT TO REHEARSAL

Disposition:

Each ProviderProfile freezes the exact protocol version and verifier implementation.

A protocol change cannot silently alter historical verification.

The future synthetic rehearsal must prove compatibility with the frozen verifier.

## Z-B07 UDP transport can be spoofed or reordered

Severity: HIGH, RESOLVED BY SIGNED RESPONSE VERIFICATION

Disposition:

Transport identity is not trusted.

Eligibility depends on the frozen root key, valid delegation, valid response signature, and proof that the derived nonce is included in the signed response.

Invalid or missing cryptographic verification fails closed.

## Z-B08 A replayed old response could falsely prove current subject existence

Severity: BLOCKING, RESOLVED IN DESIGN

Disposition:

The nonce includes the exact subject SHA256 plus a fresh cryptographically secure client random value under a domain separated SHA512 construction.

The client random value is retained.

A stale response for another nonce cannot satisfy inclusion verification.

## Z-B09 Large or unstable radius could make a receipt useless near the deadline

Severity: BLOCKING, RESOLVED BY CONSERVATIVE UPPER BOUND

Disposition:

Each receipt independently computes:

```text
verified_receipt_upper_bound = midpoint + radius
```

The receipt qualifies only if that upper bound is at or before the frozen deadline.

The project does not average radii or provider times.

## Z-B10 Two providers could share correlated upstream time sources

Severity: MEDIUM, ACCEPTED WITH DISCLOSURE

Disposition:

Provider independence is defined by operational trust authority rather than perfect physical UTC independence.

ProviderProfiles record time source disclosures when available.

Evidence of shared timestamp issuance control, shared signing key control, or common operational authority is a blocker.

Ordinary shared network or upstream time infrastructure is due diligence unless it defeats the operational independence assumption.

## Z-B11 Public services provide weaker contractual availability than paid TSAs

Severity: HIGH, ACCEPTED AS OPERATIONAL OMISSION RISK

Disposition:

The project deliberately chooses zero recurring cash cost over contractual SLA.

The scientific response to outage is an omitted or failed cycle under precommitted rules.

The protocol does not weaken quorum to preserve publication continuity.

## Z-B12 Service usage authorization could be ambiguous

Severity: BLOCKING FOR PROVIDER FREEZE, EXTERNAL EVIDENCE REQUIRED

Required closure:

Each candidate must have a retained usage authorization basis appropriate to the project's low volume automated use before a final ProviderProfile is frozen.

Public reachability alone is insufficient.

## Z-B13 Public provider status can change after Genesis

Severity: HIGH, RESOLVED BY VERSIONED GOVERNANCE

Disposition:

A provider that becomes paid, changes terms incompatibly, rotates keys without accepted migration, or ceases operation becomes unavailable for future cycles.

Historical receipts remain retained.

A replacement provider requires an accepted versioned change before it can enter the frozen pool.

## Z-B14 OpenTimestamps Bitcoin anchoring cannot replace the precise deadline clock

Severity: BLOCKING, RESOLVED IN DESIGN

Disposition:

OpenTimestamps remains a durability layer.

Bitcoin block time is not interpreted as the forecast issuance deadline.

Roughtime deadline receipts and Bitcoin durability remain separate claims.

## Z-B15 A public GitHub commit could be mistaken for a deadline trust root

Severity: HIGH, RESOLVED IN DESIGN

Disposition:

GitHub timestamps and public commitments are auxiliary observability only.

They do not count toward the Roughtime deadline quorum.

## Z-B16 RFC 3161 engineering could be reopened merely to fit a free provider

Severity: MEDIUM, RESOLVED BY SCOPE CONTROL

Disposition:

RFC 3161 checker engineering remains closed at version 1.3 and report schema 1.2 absent a new concrete correctness or security defect.

A free RFC 3161 provider that does not satisfy the frozen checker is not a reason by itself to weaken or expand the checker.

## Z-B17 Candidate object history could be rewritten to remove the old RFC requirement

Severity: BLOCKING, RESOLVED BY VERSIONED PATCH

Disposition:

The v0.2 base and v0.3 patch remain unchanged.

Version 0.4 retires `policy:deadline-receipt-quorum:v1` by exact predecessor content hash and adds `policy:deadline-receipt-quorum:v2`.

The historical v1 object remains present in the historical base file.

Materialization fails closed on retirement predecessor mismatch.

## Z-B18 Zero cost could become a hidden hardware or bandwidth claim

Severity: MEDIUM, RESOLVED BY COST SCOPE

Disposition:

`ZERO_RECURRING_CASH_COST` means no new recurring paid project service is required.

Existing owner hardware, ordinary internet access, electricity, local storage, and the already chosen development subscription remain owner supplied environment costs.

The project does not claim literal zero economic resource consumption.

## Current disposition

The zero recurring cash cost time evidence architecture is viable as a Genesis candidate.

External closure still requires successful separately authorized non forecast rehearsals for all three frozen Roughtime provider candidates, strong OpenTimestamps verification, and final adversarial review.

Current safety state remains:

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```
