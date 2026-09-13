# GEN_001 Roughtime Production Qualification Criteria Draft

Date: 2026-09-13
Status: DRAFT / NOT YET FROZEN / NOT A QUALIFICATION DECISION

## Scope and non-authorization boundary

This document prepares a versioned Roughtime production qualification standard. It does not qualify a provider, freeze a production ProviderProfile, create a qualification decision record, authorize a network request, execute Genesis, or create Forecast Ledger state.

The criteria are independent of the completed non-forecast rehearsal outcome. A three-of-three rehearsal result may supply evidence for individual criteria; it cannot lower a criterion or cause an automatic production transition.

REHEARSAL_VERIFIED is not PRODUCTION_QUALIFIED. The production-qualified provider count remains zero, PRODUCTION_QUALIFIED remains NO, and network_authorized remains false.

Normative keywords in this draft are proposals. MUST, SHOULD, and INFORMATIONAL become controlling only after a separate governance decision freezes an exact version of this document.

## Provider cryptographic criteria

Each provider MUST satisfy all of the following against its exact frozen profile:

1. Exact long-term root public-key binding.
2. Valid root-signed delegation and supported signature schemes.
3. Valid response signature under the delegated online key.
4. Exact subject-bound, provider-specific nonce derivation and response binding.
5. Valid Merkle inclusion proof over the exact request leaf semantics.
6. Exact offered and selected wire version.
7. Exact wire acceptance profile without fallback.
8. Exact TYPE presence or absence semantics.
9. Exact root-derived SRV construction and validation.
10. Authenticated midpoint extraction.
11. Positive authenticated radius with lossless retained precision.
12. Midpoint inside the authenticated delegation interval.
13. Verified receipt upper bound equals midpoint plus radius and is at or before the frozen deadline.
14. Raw request and response retention with independent hash verification.
15. Successful strict offline replay through the exact qualified verifier build.

Operator documentation that agrees with the frozen protocol identity is SHOULD. Additional implementation and time-source disclosures are INFORMATIONAL unless they expose a conflicting trust or independence fact.

## Protocol stability criteria

The production ProviderProfile MUST freeze the operator identity, endpoint, port, transport, root key, offered and selected wire version, packet profile, TYPE behavior, SRV behavior, Merkle convention or accepted convention set, nonce profile, verifier profile, and no-fallback rule.

Any change to one of those fields invalidates the old profile for new events and requires a versioned profile plus scoped requalification. Historical evidence retains its original profile semantics.

The operator-published protocol revision and any published key-rotation or service-transition procedure SHOULD be retained. Absence of a contractual stability promise is an operational risk; it does not permit silent reinterpretation.

## Operational criteria

Each provider MUST have:

1. At least one independently replayable live success under the exact profile.
2. Current operator-published evidence that the service and endpoint are active at freeze.
3. A retained basis permitting the project's low-volume automated production use.
4. Fail-closed timeout, transport, retry, backoff, deadline, and crash behavior qualified with offline tests.
5. Natural live failures, if observed, retained without selective omission.
6. A governance-approved repeatability rule before final qualification.
7. An explicit assessment of pilot, experimental, retirement, or continuity status.

A single live success proves point-in-time interoperability and may satisfy the cryptographic evidence criteria. It does not prove long-term availability. Intentional malformed or abusive live traffic is prohibited; failure paths should be qualified offline.

Formal SLA and uptime commitments are SHOULD, not an automatic MUST for the zero-recurring-cash-cost profile. Their absence must be recorded as operational risk and never lowers the event quorum.

## Independence criteria

The following are BLOCKING when shared across providers expected to form quorum:

- root-secret control;
- timestamp issuance authority;
- administrative or control-plane authority capable of controlling issuance;
- another common control dependency capable of forging or suppressing two votes.

The following are RISK inputs and do not automatically merge provider groups:

- shared software implementation family;
- shared hosting provider;
- shared network or DNS dependency;
- shared HSM vendor;
- shared upstream time source.

Geography, ASN, jurisdiction, and implementation disclosure are INFORMATIONAL unless retained evidence shows they create a material common control or quorum-survivability failure.

The known Tanner Ryan software-family correlation between time.txryan.com and TimeNL remains a recorded common-mode risk. It is not evidence of shared operational authority by itself.

## Provenance criteria

Every qualification evidence package MUST retain and cross-bind:

- exact plan and subject;
- exact authorization and unique-consumption evidence;
- request and response bytes and digests;
- request-builder and verifier transcripts;
- execution transcript;
- retry state before, per-attempt reservation state, and retry state after;
- verifier source, binary, toolchain, dependency-lock, fixture-report, and build-profile identities;
- semantic validation and independent cryptographic replay results;
- sealed qualifying receipts and aggregate report;
- complete sealed evidence manifest.

The final production ProviderProfile, qualification decision, qualifying receipts, aggregate qualification report, and complete evidence manifest MUST be sealed. Other artifacts may remain self-hashed when the sealed manifest includes their exact bytes and their semantic cross-bindings are independently validated.

## Evidence manifest criteria

The production evidence manifest MUST contain, at minimum:

- schema_version;
- event_id;
- relative_path;
- size;
- sha256;
- artifact_type;
- provider_id;
- attempt_number;
- required.

provider_id and attempt_number may be null only when the artifact is not provider- or attempt-specific.

Manifest validation MUST enforce canonical relative paths, no traversal, no symlink ambiguity, no duplicate paths, inclusion of every required file, rejection of missing required artifacts, and rejection of unclassified unexpected artifacts. The manifest must be sealed, and a future qualification decision must bind its exact hash.

## Provider-set criteria

The following proposal is DRAFT POLICY / REQUIRES FREEZE:

1. All three frozen providers are individually production qualified.
2. Each event requires two of three qualifying receipts.
3. At least two providers represent distinct issuance and root-control domains.
4. No single common control dependency can control two votes.
5. One provider outage never lowers the threshold.
6. Software, hosting, network, upstream-time, geographic, and availability correlations are recorded and reviewed.
7. The exact provider order, three profile hashes, policy version, and verifier profile are bound by the final manifest.

Qualifying only two members would turn the pool into an operational two-of-two set and remove the intended one-provider outage tolerance.

## Freshness and requalification criteria

Immutable retained cryptographic evidence does not expire merely because of age. Production qualification must record an exact freeze timestamp and is primarily invalidated by a qualifying change event.

The following numeric values are PROPOSED PARAMETER / REQUIRES POLICY DECISION:

- live interoperability maximum age at initial freeze: proposed 30 days;
- repeatability event separation: proposed minimum 7 days;
- read-only provider metadata review interval: proposed 180 days.

These values are not frozen by this draft. Immediate read-only endpoint, root, operator, protocol, and standards-transition review is required before final profile freeze regardless of age.

## Failure-path criteria

The following MUST be demonstrated with synthetic or local offline fixtures rather than intentionally induced provider failures:

- timeout, DNS and transport errors;
- malformed response and wrong response source;
- TYPE, root, SRV and wire-profile mismatch;
- delegation, signature, nonce and Merkle failure;
- verified-but-nonqualifying radius or deadline outcome;
- retry success, retry exhaustion and identical request bytes;
- BACKOFF_ACTIVE without a send;
- deadline expiry and pre-send deadline recheck;
- duplicate authorization refusal;
- crash before send, at the send boundary, and after receive;
- final cross-artifact validation failure.

Natural live failures must be retained if they occur, but no production criterion requires intentionally sending malformed or excessive requests.

## Merkle coverage criterion

Effective non-empty Merkle-path coverage is a production qualification MUST.

The required offline matrix is:

1. typed hash-first, multi-leaf;
2. typed node-first, multi-leaf;
3. untyped draft-12 node-first, multi-leaf;
4. negative wrong-order rejection where the profile does not permit alternate-order acceptance.

The current deterministic offline fixture matrix satisfies this engineering coverage requirement: each of the three positive ordering fixtures uses a two-leaf tree and demonstrates a PATH of exactly one hash / 32 bytes, and the negative wrong-order fixture requires rejection as a Merkle root mismatch under the frozen node-first-only profile. This closes the fixture-engineering gap only. It does not freeze these production qualification criteria, qualify any provider, create a production ProviderProfile, or authorize any live request.

## TimeNL pilot policy gate

TimeNL-Roughtime production admissibility is REQUIRES_POLICY_DECISION.

Governance must decide:

- whether a pilot or experimental service may enter the production pool;
- whether a contractual SLA is required;
- whether explicit operator confirmation of low-volume automated production use is required;
- what continuity evidence is sufficient;
- whether the unavailable historical implementation tag creates an unacceptable reproducibility risk.

This draft does not approve TimeNL and does not change its production status.

## Standards-transition criteria

RFC publication or provider migration never causes automatic migration or silent profile reinterpretation. Draft and RFC profiles may coexist only as separately named and versioned profiles. A provider may remain on an older frozen draft profile only while the accepted policy allows it and all frozen semantics remain exact.

A change in request bytes, wire/profile behavior, cryptographic semantics, or verifier acceptance requires new offline fixtures and scoped requalification. New live interoperability evidence is required only when the changed profile alters bytes or behavior presented to the provider.

## Qualification state machine

The proposed states are:

- UNREVIEWED;
- REHEARSAL_VERIFIED;
- QUALIFICATION_REVIEW_READY;
- QUALIFICATION_BLOCKED;
- PRODUCTION_QUALIFIED;
- QUALIFICATION_EXPIRED;
- REQUALIFICATION_REQUIRED.

No transition is automatic. REHEARSAL_VERIFIED can advance only to qualification review after evidence completeness and criteria-version checks. PRODUCTION_QUALIFIED additionally requires every MUST criterion, an independent review, a sealed qualification decision, and a sealed production ProviderProfile.

## Requalification triggers

Each of the following moves an affected production provider to REQUALIFICATION_REQUIRED:

- root, endpoint, port, or transport change;
- wire profile, TYPE, SRV, or Merkle semantics change;
- operator, ownership, issuance authority, root-secret control, or administrative control change;
- standards migration;
- verifier or checker correctness bug;
- request-builder semantic change;
- qualification-relevant orchestrator, semantic-validator, or schema change;
- evidence corruption or failed hash closure;
- production-use authorization withdrawal or service retirement.

The scope may be limited to offline regression when a component change cannot affect request bytes, trust acceptance, provider identity, or retained evidence semantics. Any such limitation requires a documented independent review.

## Acceptance rules

A provider may be production qualified only when every provider-level MUST is SATISFIED, all required evidence is complete and sealed, independence is established, freshness requirements are met, no blocking defect remains, and an independent explicit qualification decision binds the exact criteria, profile, verifier, and evidence-manifest hashes.

The provider set may be production ready only when all three frozen members are individually qualified and the provider-set criteria are satisfied. Criteria are never weakened to accommodate a provider.

## Unresolved policy decisions

This draft cannot be frozen until governance decides:

1. TimeNL pilot admissibility and continuity evidence.
2. Whether a contractual SLA is required.
3. The evidence sufficient for low-volume automated production-use permission.
4. Live-evidence maximum age.
5. Repeatability event count and separation.
6. Read-only metadata review interval.
7. Minimum proof of root-secret and issuance-control independence.
8. Common-dependency risk thresholds.
9. Evidence-manifest sealing and qualification-decision authority.

## Safety state

Genesis remains NOT STARTED. Forecast Ledger Genesis and Forecast Ledger remain NOT CREATED. The prospective forecast count and production-qualified provider count remain zero. PRODUCTION_QUALIFIED remains NO and network_authorized remains false.
