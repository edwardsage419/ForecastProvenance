# Synthetic fixtures

Every fixture in this directory has origin class `SYNTHETIC` and is permanently ineligible for native prospective history.

`adversarial_registry.json` accounts for all 96 frozen FTC_001 adversarial cases. Cases marked `AUTOMATED` are covered by executable Trust Core primitives in this build. `DESIGN_BOUNDARY` cases require an object specific validator or governance artifact that is outside the minimal primitive layer. `GENESIS_BOUNDARY` cases require a real externally anchored Genesis instance and cannot be truthfully executed as prospective tests here.
