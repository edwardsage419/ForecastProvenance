# RFC 3161 qualification rehearsal inputs

This directory contains only non-forecast qualification-readiness profiles and
derived reports. It does not contain a production provider profile, a forecast,
Genesis evidence, or authority to qualify a provider.

Raw rehearsal material remains in the owner-controlled evidence directory and
is addressed by hashes in each derived report. Profiles use paths relative to
that directory and contain no private-key reference.

The FreeTSA v2 profile intentionally records undocumented `tsa_policy1`
semantics and unspecified accuracy semantics. A cryptographically successful
run must therefore remain `REHEARSAL_INCOMPLETE`.

The Sectigo Qualified v1 candidate profile uses retained independent signer,
intermediate, root, signer-CRL, and policy evidence together with a sealed
GEN_001 independent semantic review. Its derived `REHEARSAL_VERIFIED` status is
limited to the `NON_FORECAST_REHEARSAL` classification and does not establish a
production provider profile, production qualification, or Genesis authority.

The owner-controlled `sectigo_qualified_v1` evidence directory is preserved
unchanged. To reproduce the report, create a temporary evidence view containing
the profile-named retained files plus a copy of the tracked reviewed assertion,
then run the checker against that temporary view. Raw evidence and local
absolute paths remain outside Git.
