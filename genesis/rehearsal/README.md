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
