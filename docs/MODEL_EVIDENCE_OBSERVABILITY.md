# Model Evidence Observability

Version: 0.2 candidate
Status: FTC_001 REMEDIATION CANDIDATE

Forecast provenance claims must state what portion of a method's information state is observable.

Allowed `evidence_observability_class` values:

`FULL_EXTERNAL`: every consequential information input is represented through validated external evidence contracts.

`PARTIAL_EXTERNAL`: consequential external retrievals are logged and validated, while some internal model state or learned knowledge is opaque.

`OPAQUE_INTERNAL`: the method can be identified and prospectively evaluated, while its internal informational provenance cannot be independently enumerated.

A closed language model will normally be `PARTIAL_EXTERNAL` or `OPAQUE_INTERNAL`.

Prospective evaluation is allowed for these classes after Genesis if all other protocol conditions pass. Trust reports must not describe them as having complete evidence provenance.

Model statements about their own training cutoff do not establish item level historical availability.
