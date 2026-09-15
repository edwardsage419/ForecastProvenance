# GEN_001 Roughtime Production Qualification Criteria V1

Date: 2026-09-13
Criteria ID: FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
Version: 1.0
Status: NORMATIVE CANDIDATE, effective only when frozen by the separate governance freeze decision

## Scope and authorization boundary

This document defines the complete production qualification criteria for the GEN_001 Roughtime provider pool.

Freezing these criteria does not qualify a provider, create or freeze a production ProviderProfile, create a QualificationDecision, authorize a Roughtime request, authorize an RFC 3161 request, execute Genesis, create Forecast Ledger state, or create a prospective forecast.

A completed `NON_FORECAST_REHEARSAL` may provide retained evidence for individual criteria after exact review. Its historical classification never changes and it cannot automatically transition a provider into production qualification.

Normative `MUST`, `MUST NOT`, `SHOULD`, and `MAY` terms in this document become controlling only when a separate governance decision binds the exact SHA256 of this file.

## Fixed qualification model

The initial provider pool is exactly:

1. `roughtime.se`
2. `time.txryan.com`
3. `TimeNL-Roughtime`

The event policy remains `policy:deadline-receipt-quorum:v3`.

Each provider MUST be individually production qualified before the provider set is production ready. Each production time evidence event requires at least two qualifying receipts from the three frozen providers. Provider outage never lowers the threshold.

RFC 3161 remains `OPTIONAL_AUXILIARY` and cannot replace either required Roughtime vote.

## Provider cryptographic criteria

Each provider MUST satisfy all of the following against its exact frozen ProviderProfile:

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
13. Verified receipt upper bound equal to midpoint plus radius and at or before the frozen deadline.
14. Raw request and response retention with independent hash verification.
15. Successful strict offline replay through the exact qualified verifier build.

Operator documentation that agrees with the frozen protocol identity SHOULD be retained. Additional implementation and time-source disclosures are informational unless they expose a conflicting trust, permission, continuity, or independence fact.

## Protocol stability criteria

The production ProviderProfile MUST freeze the operator identity, endpoint, port, transport, root key, offered and selected wire version, packet profile, TYPE behavior, SRV behavior, Merkle convention or accepted convention set, nonce profile, verifier profile, and no-fallback rule.

Any change to one of those fields invalidates the old profile for new events and requires a versioned profile plus scoped requalification. Historical evidence retains its original profile semantics.

The operator-published protocol revision and any published key-rotation or service-transition procedure SHOULD be retained. Absence of a contractual stability promise is an operational risk and never permits silent reinterpretation.

## Production-use permission

Each provider MUST have retained affirmative evidence permitting the project's projected low-volume automated production use.

Acceptable evidence is either:

1. operator-controlled public documentation that clearly permits the relevant Roughtime use at a volume at least as large as the frozen projected use; or
2. direct written operator confirmation that clearly permits the relevant low-volume automated production use.

The qualification package MUST record the projected request volume implied by the frozen schedule, event policy, timeout rule, and retry cap, and MUST explain why the retained permission evidence covers that volume.

Publication of an endpoint, root key, source repository, ecosystem listing, or generic protocol description alone is insufficient permission evidence.

When a service is explicitly described by its operator as pilot or experimental, generic language inviting testing or adding the server to a list is insufficient to establish automated production-use permission. Explicit operator evidence covering automated production use is required.

Permission withdrawal, a newly published conflicting use restriction, or service retirement immediately triggers `REQUALIFICATION_REQUIRED` or `QUALIFICATION_EXPIRED`, as applicable.

## Contractual SLA policy

A contractual SLA is NOT REQUIRED.

The evidence package MUST record whether an SLA exists and MUST retain any operator-published availability or support statement used during review.

Absence of an SLA is an operational risk. It never lowers the event quorum, weakens cryptographic criteria, or permits fallback to another protocol, packet profile, transport, or provider identity.

## Live interoperability and repeatability

Each provider MUST have at least two independently authorized qualifying live interoperability events under the same exact qualification profile.

The two qualifying events MUST:

1. be separated by at least `7 * 24 hours`;
2. use separately authorized execution plans and independently consumed authorizations;
3. retain complete request, response, execution, retry-state, semantic-validation, and strict-verifier evidence;
4. satisfy every cryptographic and operational criterion applicable to the event;
5. have no intervening qualification-relevant profile change.

At least one of the two qualifying events MUST occur after the criteria freeze decision.

At least one qualifying live event MUST be no more than 30 days old at the time of the provider QualificationDecision.

A retained `NON_FORECAST_REHEARSAL` MAY satisfy at most one of the two live-event requirements if an independent review proves that its exact evidence satisfies the frozen criteria. Reuse as evidence never changes its classification, never changes `prospective_eligible`, and never creates a production event retroactively.

Natural live failures MUST be retained if they occur. Intentional malformed, abusive, or excessive provider traffic is prohibited. Failure paths are qualified offline.

## Pilot and experimental service policy

A provider explicitly labeled pilot or experimental by its operator is `CONDITIONALLY_ADMISSIBLE`.

The frozen three-provider pool MUST contain no more than one pilot or experimental provider.

A pilot or experimental provider MUST satisfy every ordinary production criterion and all of the following additional criteria:

1. explicit operator evidence permitting the project's low-volume automated production use;
2. at least 90 days of retained continuity evidence for the same service identity under the same operator and root-control domain;
3. no current operator statement that the specific Roughtime service is unsuitable for production use;
4. current operator metadata within the normal 90-day review interval;
5. a recorded assessment of expected transition, endpoint change, protocol change, and retirement risk.

Continuity evidence MAY consist of operator-controlled version history, archived operator documentation, independently timestamped retained operator metadata, or direct operator confirmation. It MUST bind the service identity, operator, root-control domain, and observation dates. The current endpoint and exact wire profile remain subject to the separate 30-day live-evidence freshness rule.

An unavailable historical provider implementation tag is a reproducibility risk. It is BLOCKING only when the qualification claim depends on reproducing that provider implementation rather than independently verifying retained protocol evidence and the provider's public cryptographic identity.

If the pilot or experimental provider ceases to satisfy these conditions, the fixed three-provider pool is no longer production ready until governance either requalifies the provider under a valid profile or separately changes the provider-set policy.

## Operational criteria

Each provider MUST have:

1. current operator-published evidence that the service and endpoint are active at qualification review;
2. the production-use permission basis defined above;
3. fail-closed timeout, transport, retry, backoff, deadline, and crash behavior qualified with offline tests;
4. natural live failures, if observed, retained without selective omission;
5. the required live repeatability evidence;
6. an explicit pilot, experimental, retirement, and continuity assessment.

A single live success proves only point-in-time interoperability. It cannot by itself establish repeatability or long-term availability.

## Independence criteria

For every pair of providers that may form the two-vote quorum, production qualification MUST establish positive evidence for distinct root-secret control and distinct timestamp-issuance control.

The minimum retained independence evidence MUST identify:

1. the accountable operator for each provider;
2. the long-term root public key for each provider;
3. the organizational or individual control domain responsible for the root secret;
4. the organizational or individual control domain responsible for delegation and online issuance;
5. any known administrative or control-plane authority capable of changing the root, delegation, signer, endpoint, or issuance behavior.

Different root keys, domain names, IP addresses, ASNs, legal names, hosting providers, or software families alone do not prove control independence.

Public first-party documentation MAY establish a control fact when it is sufficiently explicit. When public evidence is insufficient, direct operator confirmation is required. An unresolved `UNKNOWN` for root-secret control or issuance-control independence is BLOCKING.

The following are BLOCKING when shared across two providers that may form quorum:

1. root-secret control;
2. timestamp issuance authority;
3. administrative or control-plane authority capable of controlling issuance;
4. any other common control dependency capable of producing accepted false receipts for two votes.

## Common-dependency risk threshold

A common dependency becomes BLOCKING when retained evidence establishes either of the following:

1. a single control domain can cause two provider votes to produce cryptographically acceptable false time evidence; or
2. a provider-side single dependency can realistically suppress at least two votes for the complete production evidence window with no qualified independent path.

Shared software implementation family, commodity hosting, transit, DNS infrastructure, HSM vendor, upstream time source, geography, ASN, or jurisdiction is otherwise recorded as `RISK` and does not automatically merge provider groups.

A risk MUST be upgraded to BLOCKING when concrete evidence shows that it meets one of the two-vote thresholds above.

Client-side dependencies that are unavoidably common to the project execution environment are recorded separately as client availability risks and do not establish provider common control.

The known Tanner Ryan software-family correlation between `time.txryan.com` and `TimeNL-Roughtime` remains a recorded common-mode software risk. Software-family correlation alone is insufficient evidence of shared root or issuance authority.

## Provenance criteria

Every qualification evidence package MUST retain and cross-bind:

1. exact plan and subject;
2. exact authorization and unique-consumption evidence;
3. request and response bytes and digests;
4. request-builder and verifier transcripts;
5. execution transcript;
6. retry state before execution, per-attempt reservation state, and retry state after execution;
7. verifier source, binary, toolchain, dependency-lock, fixture-report, and build-profile identities;
8. semantic validation and independent cryptographic replay results;
9. qualifying receipts and aggregate report;
10. complete evidence manifest;
11. independent qualification review report;
12. final production ProviderProfile candidate;
13. final QualificationDecision.

## Evidence manifest canonicalization and sealing

The complete evidence manifest MUST use `FPP_JCS_1` and SHA256.

Each manifest entry MUST contain:

1. `relative_path`
2. `size`
3. `sha256`
4. `artifact_type`
5. `required`

`provider_id` and `attempt_number` MUST be present when applicable to the artifact and MUST be omitted when not applicable. JSON `null` MUST NOT be used for these fields.

Manifest entries MUST be sorted lexicographically by canonical ASCII `relative_path`.

The manifest validator MUST enforce:

1. canonical relative paths;
2. no path traversal;
3. no symlink ambiguity;
4. no duplicate paths;
5. exact inclusion of every required artifact;
6. rejection of a missing required artifact;
7. rejection of an unclassified unexpected artifact;
8. independent recomputation of file size and SHA256;
9. deterministic entry ordering.

The manifest MUST NOT contain itself. Its canonical `FPP_JCS_1` bytes are sealed by SHA256 outside the manifest. This avoids self-reference.

Qualifying receipts and the aggregate qualification report MUST be covered by the complete manifest. The production ProviderProfile MUST have its own canonical content SHA256. The final QualificationDecision MUST bind the exact manifest SHA256 and ProviderProfile SHA256.

## Provider-set criteria

The provider set is production ready only when all of the following hold:

1. all three frozen providers are individually production qualified;
2. each event requires two of three qualifying receipts;
3. at least two providers represent distinct issuance and root-control domains;
4. no single common control dependency meets the two-vote blocking threshold;
5. one provider outage never lowers the threshold;
6. the pool contains no more than one pilot or experimental provider;
7. software, hosting, network, upstream-time, geographic, jurisdictional, and availability correlations are retained and reviewed;
8. the exact provider order, three ProviderProfile hashes, policy version, and verifier profile are bound by the final trusted configuration.

Qualifying only two members is insufficient because it converts the intended three-member pool into an operational two-of-two system and removes one-provider outage tolerance.

## Freshness and metadata review

Immutable retained cryptographic evidence does not expire merely because of age.

For an initial QualificationDecision, at least one qualifying live interoperability event MUST be no more than 30 days old.

Each qualified provider MUST undergo a read-only operator metadata review at least once every 90 days.

The metadata review MUST cover, when published:

1. operator identity;
2. service status;
3. endpoint and port;
4. root public key;
5. protocol or standards transition;
6. use restrictions;
7. pilot, experimental, retirement, or deprecation status;
8. key-rotation or migration notice.

The review MUST retain source identifiers, retrieval time, retrieved bytes or a stable content capture where legally and technically practical, and cryptographic hashes of retained captures.

A missed 90-day metadata review moves the provider to `QUALIFICATION_EXPIRED` for new production events until the review is completed. A qualification-relevant change discovered during review triggers `REQUALIFICATION_REQUIRED`.

Immediate read-only review is required before final ProviderProfile freeze regardless of the previous review age.

## Failure-path criteria

The following MUST be demonstrated with synthetic or local offline fixtures rather than intentionally induced provider failures:

1. timeout, DNS, and transport errors;
2. malformed response and wrong response source;
3. TYPE, root, SRV, and wire-profile mismatch;
4. delegation, signature, nonce, and Merkle failure;
5. verified but nonqualifying radius or deadline outcome;
6. retry success, retry exhaustion, and identical request bytes;
7. `BACKOFF_ACTIVE` without a send;
8. deadline expiry and pre-send deadline recheck;
9. duplicate authorization refusal;
10. crash before send, at the send boundary, and after receive;
11. final cross-artifact validation failure.

Natural live failures MUST be retained if they occur.

## Merkle coverage criterion

Effective non-empty Merkle-path coverage is a production qualification MUST.

The required offline matrix is:

1. typed hash-first, multi-leaf;
2. typed node-first, multi-leaf;
3. untyped draft-12 node-first, multi-leaf;
4. negative wrong-order rejection where the profile does not permit alternate-order acceptance.

The existing deterministic offline fixture matrix may satisfy this engineering criterion after exact evidence review. Fixture completion alone does not qualify a provider.

## Standards-transition criteria

RFC publication, draft revision, or provider migration never causes automatic migration or silent profile reinterpretation.

Draft and RFC profiles may coexist only as separately named and versioned profiles. A provider may remain on an older frozen draft profile only while the accepted project policy permits it and all frozen semantics remain exact.

A change in request bytes, wire behavior, cryptographic semantics, or verifier acceptance requires new offline fixtures and scoped requalification.

New live interoperability evidence is required when the changed profile alters bytes or behavior presented to the provider.

## Qualification state machine

The states are:

1. `UNREVIEWED`
2. `REHEARSAL_VERIFIED`
3. `QUALIFICATION_REVIEW_READY`
4. `QUALIFICATION_BLOCKED`
5. `PRODUCTION_QUALIFIED`
6. `QUALIFICATION_EXPIRED`
7. `REQUALIFICATION_REQUIRED`

No transition is automatic.

`REHEARSAL_VERIFIED` may advance only to qualification review after evidence completeness and criteria-version checks.

`PRODUCTION_QUALIFIED` additionally requires every applicable MUST criterion, the complete manifest, the final ProviderProfile, a separate independent review event, and an explicit QualificationDecision under the authority rule below.

## Independent review and qualification decision authority

Qualification execution and qualification approval MUST be separate events.

The qualification executor MUST NOT automatically issue the final approval decision.

The independent review event MUST independently recompute consequential hashes, rerun deterministic validators and strict cryptographic replay where applicable, verify evidence completeness, verify criteria satisfaction, and produce an immutable review report.

The reviewer MAY be the project owner when the zero-cost operating model has no second human reviewer. In that case the review MUST still be a separate recorded event using independently reconstructed inputs rather than the executor's mutable in-memory state.

The final QualificationDecision authority for GEN_001 is the owner-controlled Ed25519 bootstrap authority.

The final QualificationDecision MUST be an immutable `FPP_JCS_1` object whose signed payload binds at minimum:

1. criteria ID and criteria SHA256;
2. provider identity;
3. ProviderProfile ID and SHA256;
4. complete evidence manifest SHA256;
5. verifier profile and qualified verifier build identities;
6. independent review report SHA256;
7. decision result;
8. decision timestamp;
9. authority public-key identity.

The exact QualificationDecision schema and signature projection MUST be frozen before qualification execution.

The owner Ed25519 private key MUST remain under owner control and MUST NOT enter GitHub, CI, repository fixtures, ChatGPT, Codex, logs, prompts, or third-party services.

No qualification execution is ready until the required public-key identity, schemas, validators, and offline tests exist.

## Requalification triggers

Each of the following moves an affected production provider to `REQUALIFICATION_REQUIRED`:

1. root, endpoint, port, or transport change;
2. wire profile, TYPE, SRV, or Merkle semantics change;
3. operator, ownership, issuance authority, root-secret control, or administrative control change;
4. standards migration;
5. verifier or checker correctness bug;
6. request-builder semantic change;
7. qualification-relevant orchestrator, semantic-validator, or schema change;
8. evidence corruption or failed hash closure;
9. production-use authorization withdrawal;
10. service retirement;
11. newly established blocking common dependency.

The scope MAY be limited to offline regression when a component change cannot affect request bytes, trust acceptance, provider identity, permission, independence, or retained evidence semantics. Any such limitation requires a documented independent review.

## Acceptance rules

A provider may be production qualified only when:

1. every applicable provider-level MUST criterion is satisfied;
2. required evidence is complete and sealed;
3. production-use permission is established;
4. root-secret and issuance-control independence are established;
5. freshness and repeatability requirements are met;
6. no blocking dependency or defect remains;
7. the independent review passes;
8. the exact schemas and validators have passed offline regression;
9. the owner-authorized QualificationDecision binds the exact criteria, profile, verifier, review, and evidence-manifest hashes.

Criteria are never weakened to accommodate a provider.

The provider set may be production ready only when all three frozen members are individually qualified and every provider-set criterion is satisfied.

## Safety state

Freezing these criteria changes no production or Genesis state.

The required state remains:

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
production forecasting = PROHIBITED
network_authorized = false
```

No live provider request is authorized by this document.
