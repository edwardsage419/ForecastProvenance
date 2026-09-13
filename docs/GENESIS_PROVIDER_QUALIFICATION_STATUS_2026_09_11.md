# Genesis Provider Qualification Status

Date: 2026-09-11
Status: CURRENT RFC 3161 READ-ONLY ASSESSMENT / NON-CONTROLLING FOR THE V3 ROUGHTIME QUORUM

## Purpose

This document records the current GEN_001 provider-qualification state after the retained RFC 3161 rehearsals and the subsequent read-only production-prerequisite assessments.

D026 and `docs/GENESIS_READINESS_EVIDENCE_MATRIX.md` control the current Genesis deadline-receipt design. The RFC 3161 providers assessed here are auxiliary candidates under that design; this document does not select, qualify, or replace any member of the frozen version 3 Roughtime pool.

It is not a ProviderProfile, does not grant quorum eligibility, does not authorize an RFC 3161 request, and does not authorize Genesis or prospective forecasting.

The dated provider snapshot in `docs/GENESIS_PROVIDER_SNAPSHOT_2026_09_11.md` remains a historical design snapshot and is not rewritten to make old assumptions look current.

## Immutable safety state

- Genesis: `NOT STARTED`.
- Forecast Ledger Genesis: `NOT CREATED`.
- Forecast Ledger: `NOT CREATED`.
- Prospective forecast count: `0`.
- Production-qualified provider count: `0`.
- Genuine prospective forecasting: prohibited.
- No production ProviderProfile exists.
- Rehearsal artifacts remain permanently `NON_FORECAST_REHEARSAL`.
- `prospective_eligible=false` for retained rehearsal reports.
- The Genesis Ed25519 private key must remain outside the repository, GitHub, CI, and ChatGPT-managed artifacts.

## RFC 3161 checker state

RFC 3161 rehearsal checker engineering is closed unless a new concrete correctness or security defect is discovered.

Current retained checker state:

- checker version: `1.3`.
- report schema version: `1.2`.
- revocation scope: `TSA_SIGNER_ONLY`.
- retained rehearsal reports reproduce byte-identically under the final readiness run.

No provider becomes `PRODUCTION_QUALIFIED` merely because a rehearsal report is `REHEARSAL_VERIFIED`.

## Retained rehearsal outcomes

### FreeTSA

Current retained result: `REHEARSAL_INCOMPLETE`.

Current blockers under retained evidence:

- `TOKEN_POLICY_SEMANTICS_UNDOCUMENTED`.
- `TIMESTAMP_ACCURACY_UNSPECIFIED`.

Current disposition: disqualify for GEN_001 under the presently retained evidence unless new authoritative evidence appears.

### DigiCert

Current retained result: `REHEARSAL_INCOMPLETE`.

Observed token policy OID: `2.16.840.1.114412.7.1`.

Current disposition: `INSUFFICIENT_EVIDENCE`. Current retained policy evidence does not establish a defensible maximum UTC error for the observed service strongly enough for deadline qualification.

### Sectigo ordinary RFC 3161

Current retained result: `REHEARSAL_INCOMPLETE`.

Endpoint family previously rehearsed: `http://timestamp.sectigo.com/rfc3161`.

Observed token policy OID: `1.3.6.1.4.1.6449.2.1.1`.

Current disposition: `INSUFFICIENT_EVIDENCE`. Current retained official evidence does not clearly bind both policy semantics and a conservative maximum UTC error to the observed token.

### Sectigo Qualified

Retained report: `genesis/rehearsal/reports/sectigo_qualified_v1_report.json`.

Current retained result:

- `REHEARSAL_VERIFIED`.
- classification: `NON_FORECAST_REHEARSAL`.
- `prospective_eligible=false`.
- `PRODUCTION_QUALIFIED=NO`.
- production-qualified provider count remains `0`.

The retained report verifies subject binding, nonce, RFC 3161 signature, signer chain, timestamp EKU, policy OID `0.4.0.2023.1.1`, one-second token accuracy semantics, and signer CRL evidence under the frozen rehearsal checker.

The successful rehearsal proves the retained request and response satisfy the rehearsal criteria. It does not prove long-term free use, production authorization, service continuity, SLA, quota, unlimited access, or production qualification.

Current production-prerequisite disposition: `CONTINUE QUALIFICATION`, with commercial qualification blocked pending direct authoritative confirmation of production entitlement and controlling terms.

Unresolved production matters include:

- exact production-use authorization for the qualified endpoint.
- applicable subscriber, order, service, and acceptable-use terms.
- fees, subscription and entitlement model.
- quota, rate, concurrency and automation restrictions.
- contractual SLA, support, maintenance and termination rights.
- production evidence-retention and validation-material update procedures.

## Signicat second-provider candidate

Signicat AS is the current leading candidate for a second independent RFC 3161 provider group.

Current assessment state:

`SIGNICAT NOT READY FOR NON_FORECAST_REHEARSAL`

No Signicat RFC 3161 request or endpoint probe has been authorized or performed by this assessment.

Current positive evidence supports continued qualification work, including a currently qualified timestamp-service identity, published RFC 3161 QTSA documentation, documented policy and accuracy semantics, and a distinct operational trust-authority candidate from Sectigo.

Current blockers before any rehearsal authorization include:

- written permission for the proposed controlled `NON_FORECAST_REHEARSAL` or other explicit authorization covering the exact request.
- exact authorized endpoint and access constraints.
- unambiguous operative TSU signer set and its mapping to the trusted-list service identity.
- authoritative signer and chain material sufficient for fail-closed verification.
- nonce, `reqPolicy`, `certReq`, message-imprint, and revocation behavior needed to define the request profile before sending it.
- applicable rate, quota, concurrency and automation restrictions for the proposed request.

Commercial production qualification remains a separate gate and additionally requires the controlling contract, production entitlement, pricing, quota, SLA, support, maintenance, termination and retention terms.

## Rehearsal and production gates

The project maintains separate states:

```text
REHEARSAL_AUTHORIZATION
PRODUCTION_QUALIFICATION
```

They are not equivalent:

```text
REHEARSAL_AUTHORIZATION != PRODUCTION_AUTHORIZATION
REHEARSAL_VERIFIED != PRODUCTION_QUALIFIED
```

A provider may become eligible for one controlled `NON_FORECAST_REHEARSAL` after explicit authorization and technical-entry criteria are independently reviewed, while production-commercial requirements remain open.

A successful rehearsal does not close production-commercial or Genesis-governance requirements.

## Deadline accuracy rule

For an RFC 3161 receipt admitted under `FPP_TIME_EVIDENCE_V1`, deadline qualification uses the conservative upper bound:

```text
verified_receipt_upper_bound = genTime + declared_accuracy
```

For a documented one-second accuracy candidate, the corresponding candidate upper bound is:

```text
verified_receipt_upper_bound = genTime + 1 second
```

No alternate deadline semantics are introduced by provider assessment.

## Provider-group independence rule

The current `DEADLINE_RECEIPT_QUORUM_V3` candidate requires qualifying Roughtime receipts from distinct provider groups within its exactly three-profile frozen pool.

A provider group represents one operational trust authority. Multiple endpoints, TSUs or certificates controlled by the same operational authority remain one provider group.

Provider-group independence does not require ordinary infrastructure suppliers to be completely different. Shared hosting vendors, HSM vendors, TSA software vendors, network providers or time sources are supply-chain due diligence unless evidence shows that the overlap creates shared timestamp-issuance control, shared signing-key control, a common PKI authority, or another demonstrated dependency that defeats the independent-provider-group assumption.

## Current next actions

1. Do not extend RFC 3161 checker engineering absent a new concrete defect.
2. Seek direct written Sectigo confirmation for production entitlement and controlling commercial terms before any production ProviderProfile can be considered.
3. Seek direct written Signicat confirmation sufficient to evaluate `REHEARSAL_AUTHORIZATION` before any request is sent.
4. Independently review any provider reply before changing readiness state.
5. If a provider later becomes ready for rehearsal, authorize the exact request in a separate task and retain it permanently as `NON_FORECAST_REHEARSAL`.
6. Complete separate production qualification for all three frozen version 3 Roughtime provider groups before the current Genesis quorum can close; RFC 3161 qualification remains auxiliary.
7. Create and freeze production ProviderProfiles only in a separately authorized final-freeze task after all required qualification evidence is closed.

## Terminal state

- `Genesis = NOT STARTED`.
- `Forecast Ledger Genesis = NOT CREATED`.
- `Forecast Ledger = NOT CREATED`.
- `prospective forecast count = 0`.
- `production-qualified provider count = 0`.
- `PRODUCTION_QUALIFIED = NO` for every currently assessed provider.
