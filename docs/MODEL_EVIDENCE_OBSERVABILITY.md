# Model Evidence Observability

Version: 0.3 candidate
Status: FTC_001 FREEZE CANDIDATE

Forecast provenance claims must state what portion of a method's declared information inputs can be independently inspected.

Allowed `evidence_observability_class` values:

`FULL_DECLARED_EXTERNAL_INPUTS`: every declared external information input is represented through validated evidence contracts. This does not claim complete causal provenance of runtime, hardware, libraries, model parameters, or hidden upstream processes.

`PARTIAL_EXTERNAL`: consequential external retrievals are logged and validated, while some declared or internal information state remains opaque.

`OPAQUE_INTERNAL`: the method can be identified and prospectively evaluated, while internal informational provenance cannot be independently enumerated.

A closed language model will normally be `PARTIAL_EXTERNAL` or `OPAQUE_INTERNAL`.

Prospective evaluation may later include any class when all other Genesis conditions pass. Trust reports must state the observability class and cannot promote partial or opaque provenance into complete provenance.

A model statement about its own training cutoff does not establish item level historical availability.