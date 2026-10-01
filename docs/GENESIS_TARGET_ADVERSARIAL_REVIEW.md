# Genesis Target Specific Adversarial Review

Date: 2026-09-11
Target candidate set: CPI monthly change, U-3 unemployment rate, real GDP advance estimate
Disposition: TARGET SET VIABLE WITH CONTRACT REPAIRS

## T-B01 CPI current database revision can overwrite first-release value

Severity: BLOCKING, RESOLVED IN DESIGN

BLS current databases can reflect later revisions or updated seasonal factors.

Resolution:

CPI Genesis outcome resolves only from the archived first CPI news release for the reference month, with retained artifact hash. Current database values cannot replace the archived first-release value.

## T-B02 CPI table layout can change

Severity: HIGH, OPEN FOR IMPLEMENTATION

A parser hard-coded to one HTML column position could silently read the wrong value after a BLS presentation change.

Required closure:

Resolution parser must bind semantic row and column labels, validate expected reference month, unit, seasonal-adjustment label, and produce an explicit parser failure on unrecognized layout. A second independent extraction check is required for Genesis rehearsal fixtures.

## T-B03 CPI seasonal adjustment revisions create semantic ambiguity

Severity: HIGH, RESOLVED IN DESIGN

Resolution:

The first archived release value is authoritative even if later annual seasonal adjustment revisions change history. The target explicitly forecasts a first-release statistic, not an eternally revised latent value.

## T-B04 Employment Situation annual population controls and seasonal revisions can change history

Severity: HIGH, RESOLVED IN DESIGN

Resolution:

U-3 resolves from the archived first Employment Situation release Table A-1 for the reference month. Later annual population controls or seasonal revisions do not rewrite the outcome.

## T-B05 U-3 could be confused with broader U-6 or an unadjusted rate

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

Target semantics explicitly bind official U-3, TOTAL civilian population, seasonally adjusted unemployment rate from Table A-1. Alternate underutilization measures and unadjusted columns are invalid resolution fields.

## T-B06 GDP current interactive table is superseded by later estimates

Severity: BLOCKING, RESOLVED IN DESIGN

BEA states that later GDP releases supersede current displayed data and provides a Data Archive.

Resolution:

GDP Genesis outcome is the Advance Estimate first-release value. Resolution retains the original release or Data Archive artifact and never resolves from a later current-table value.

## T-B07 GDP percent change definition can be confused with level, contribution, price index, or later estimate

Severity: BLOCKING, RESOLVED IN DESIGN

Resolution:

Target binds BEA Table 1.1.1 Percent Change From Preceding Period in Real GDP, Advance Estimate for the reference quarter. Other tables, nominal GDP, contribution measures, second estimate, and third estimate are invalid substitutes.

## T-B08 Official release schedule can change because of shutdowns or data availability

Severity: BLOCKING, RESOLVED AT POLICY LEVEL

BEA changed multiple 2026 release dates after shutdown disruption, demonstrating that nominal annual schedules are not immutable.

Resolution:

GENESIS_SCHEDULE_POLICY.md freezes a content-addressed official schedule snapshot before cycle precommitment and defines deterministic earlier, later, cancellation, and unresolved handling.

## T-B09 BLS calendars are updated over time

Severity: HIGH, RESOLVED AT POLICY LEVEL

BLS states that calendars are updated as needed.

Resolution:

Each cycle stores the actual schedule artifact used to derive the barrier. A later website update cannot rewrite the historical schedule input.

## T-B10 Time-zone conversion can be wrong around daylight-saving changes

Severity: HIGH, RESOLVED AT POLICY LEVEL

Resolution:

Official Eastern Time releases use a frozen IANA zone identifier and a recorded time-zone database version. Fixed offsets are prohibited.

## T-B11 Release web page may be modified after first publication

Severity: BLOCKING, OPEN FOR SOURCE CONTRACT

An archived URL alone is insufficient if bytes can change or archives are generated later.

Required closure:

At resolution, immediately capture content-addressed release artifacts from the official archive path where available. Retain raw bytes or durable content-addressed copies permitted by policy. Record retrieval time and source URL. If only a mutable page exists, require a second official artifact such as PDF, XLSX, API vintage, or agency archive before full resolution trust.

## T-B12 Precision and rounding can create evaluation disputes

Severity: HIGH, OPEN

Official releases often publish CPI and unemployment to one decimal while underlying APIs may have other representation choices.

Required closure:

Each TargetDefinition must freeze the authoritative displayed precision and canonical decimal parsing rule. Evaluation compares forecasts to the exact frozen released representation converted to a canonical decimal string, with no hidden extra precision.

## T-B13 Last-observed-value baseline can accidentally use revised data

Severity: BLOCKING, OPEN

A baseline that fetches a current historical series can introduce future revisions into its input.

Required closure:

Baseline SourceContract must use point-in-time archived releases or another vintage-preserving source. Current revised historical databases cannot satisfy the baseline without a frozen vintage reconstruction rule.

## T-B14 Selecting three targets after examining model performance would create target-selection bias

Severity: BLOCKING, RESOLVED BY PROCESS

Resolution:

The candidate set was selected from release-source and operational criteria before any production forecast values were generated. The repository prohibits forecast execution during GEN_001. Any later target replacement requires a documented non-performance-based reason before Genesis.

## T-B15 Continuous point forecasts provide limited calibration evidence

Severity: MEDIUM, ACCEPTED FOR GENESIS V1

Genesis version 1 prioritizes provenance and execution integrity with the smallest output surface. Point forecasts retain absolute and squared error only.

Probabilistic calibration remains a later protocol extension and must not be inferred from Genesis point-forecast results.

## Target set disposition

The three-target candidate set is scientifically suitable for Genesis provided the remaining source-contract, parser, precision, and baseline-vintage blockers are closed.

No forecast generation is authorized by this review.