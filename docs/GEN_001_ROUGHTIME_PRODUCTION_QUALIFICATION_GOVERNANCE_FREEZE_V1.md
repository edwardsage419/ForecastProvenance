# GEN_001 Roughtime Production Qualification Governance Freeze V1

Date: 2026-09-13
Decision ID: GEN_001_ROUGHTIME_PRODUCTION_QUALIFICATION_GOVERNANCE_FREEZE_V1
Status: ACCEPTED
Scope: production qualification governance criteria only

## Snapshot basis

```text
repository = edwardsage419/ForecastProvenance
branch = design/gen-001
snapshot_basis_commit = 005049c5153580b666a4736f17b6fc6140006203
```

This decision was prepared after confirming that the remote branch remained at the snapshot basis and that PR #6 remained open, Draft, and unmerged.

## Frozen criteria binding

The following exact criteria object is frozen:

```text
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_path = docs/GEN_001_ROUGHTIME_PRODUCTION_QUALIFICATION_CRITERIA_V1.md
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
```

The historical dated draft remains retained as design provenance and is not rewritten into a qualification result.

## Governance decisions

### 1. Pilot and experimental service admissibility

Pilot or experimental Roughtime services are conditionally admissible.

The fixed three-provider pool may contain at most one pilot or experimental provider.

A pilot or experimental provider must satisfy all ordinary criteria plus explicit low-volume automated production-use permission, at least 90 days of continuity evidence for the same service identity under the same operator and root-control domain, current metadata review, and no operator statement that the specific Roughtime service is unsuitable for production use.

TimeNL-Roughtime is therefore not automatically approved or rejected by its pilot label. Its admissibility remains evidence-dependent under the frozen criteria.

### 2. Contractual SLA

A contractual SLA is not required.

Any available SLA or operator-published availability statement is retained as risk evidence. Absence of an SLA never lowers quorum or weakens cryptographic, permission, repeatability, or independence requirements.

### 3. Automated production-use permission

Affirmative use permission is mandatory.

Acceptable evidence is either sufficiently explicit operator-controlled public documentation or direct written operator confirmation. Qualification must retain the projected request volume implied by the frozen schedule and retry policy and show that the permission evidence covers that use.

Pilot or experimental status requires explicit evidence that covers automated production use.

### 4. Live interoperability freshness

At least one qualifying live interoperability event must be no more than 30 days old when the provider QualificationDecision is issued.

Historical cryptographic evidence remains immutable and auditable after it becomes older than 30 days. Age alone does not erase historical validity.

### 5. Repeatability

Each provider requires at least two qualifying live interoperability events under the same exact qualification profile, separated by at least 7 * 24 hours.

At least one event must occur after this criteria freeze.

A retained `NON_FORECAST_REHEARSAL` may satisfy at most one event requirement after independent frozen-criteria review. Its classification and `prospective_eligible = false` state never change.

Every future live event requires a new separately authorized plan and independently consumed authorization.

### 6. Read-only metadata review

The provider metadata review interval is frozen at 90 days.

A missed review causes `QUALIFICATION_EXPIRED` for new production events until review completes. Any qualification-relevant change triggers `REQUALIFICATION_REQUIRED`.

This review rule does not authorize a Roughtime protocol request.

### 7. Root-secret and issuance-control independence

Positive independence evidence is mandatory for every provider pair that may form quorum.

Different root keys, domains, IP addresses, ASNs, legal names, hosting providers, or software families do not by themselves establish root-secret or issuance-control independence.

Public first-party evidence may establish a control fact when sufficiently explicit. Otherwise direct operator confirmation is required.

An unresolved `UNKNOWN` for root-secret control or issuance-control independence is BLOCKING.

### 8. Common-dependency threshold

The blocking threshold is two votes.

A common dependency is BLOCKING when one control domain can produce accepted false time evidence for two votes, or when a provider-side single dependency can realistically suppress at least two votes for the complete production evidence window with no qualified independent path.

Shared software, commodity hosting, transit, DNS, HSM vendor, upstream time source, geography, ASN, or jurisdiction remains a recorded risk until evidence establishes one of the blocking thresholds.

### 9. Evidence-manifest sealing and qualification authority

The complete evidence manifest uses `FPP_JCS_1` and SHA256.

The manifest excludes itself and is sealed externally by its canonical SHA256. The final QualificationDecision binds the exact manifest SHA256 and ProviderProfile SHA256.

The qualification executor cannot automatically approve qualification. A separate independent review event is mandatory.

The final GEN_001 QualificationDecision authority is the owner-controlled Ed25519 bootstrap authority. The exact decision schema and signature projection must be frozen and tested before qualification execution.

The private key remains outside GitHub, CI, repository fixtures, ChatGPT, Codex, logs, prompts, and third-party services.

## Canonicalization consistency correction

The dated criteria draft allowed `provider_id` and `attempt_number` to be JSON `null` when not applicable.

`FPP_JCS_1` prohibits JSON null in consequential normative content.

V1 resolves the conflict by requiring those fields when applicable and omitting them when not applicable. Manifest entries are deterministically ordered by canonical ASCII `relative_path`.

This is a correctness repair and does not weaken any qualification requirement.

## External policy basis observed at freeze preparation

The governance review used first-party or standards-organization sources only.

1. TimeNL publicly described `TimeNL-Roughtime` as a pilot and stated that protocol details, including the port, may change.
2. `time.txryan.com` publicly permitted individual use and stated that no formal uptime or accuracy guarantees exist.
3. `roughtime.se` publicly invited use for time synchronization, timestamping, testing, and development.
4. The IETF Datatracker showed `draft-ietf-ntp-roughtime-19` in the RFC Editor queue with intended status Experimental.

These observations explain the policy choices. They are not provider qualification evidence by themselves. Final qualification must retain its own current operator metadata and exact evidence.

## Effect of this decision

This decision changes only the criteria governance state:

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```

Production qualification execution remains blocked until separately reviewed schemas and validators exist for:

1. production ProviderProfile;
2. qualification decision and state;
3. complete evidence manifest;
4. independent qualification review report and exact cross-binding rules.

Retained rehearsal evidence may be evaluated against the frozen criteria only after those structures are ready. Evaluation cannot alter historical classification.

## Safety boundary

This decision does not:

1. qualify any provider;
2. create a production ProviderProfile;
3. create a QualificationDecision;
4. authorize a live provider request;
5. authorize RFC 3161 traffic;
6. create or accept Forecast Ledger Genesis;
7. create Forecast Ledger state;
8. create a prospective forecast.

The safety state remains:

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

The next main task is schema and validator design for production ProviderProfile, qualification decision/state, complete evidence manifest, and independent review records. No production qualification execution is authorized by this freeze.
