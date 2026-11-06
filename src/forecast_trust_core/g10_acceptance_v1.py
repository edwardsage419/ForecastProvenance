"""T03 bounded internal acceptance/dependency/report/finding composition.

Component report replays are internal raw Check outputs of actual components;
the full orchestrator must compute them, never accept them from its caller.
Synthetic authentication is explicitly a formula-free seam. No real signing.
"""
from __future__ import annotations

from .architecture_compression_v1 import validate_manifest_acceptance_v2
from .claim_authority_contract_gate_v1 import validate_manifest_acceptance_v2_contract
from .authority_primitives_v1 import ExactRef, resolve_exact, AuthorityPrimitiveError
from .core import Check
from .replay_model_v1 import MODEL_SOURCE_REFS
from .replay_records_v1 import NativeReplay, emit_records, reduce_checks

REPORT_CHECKS = {
    "runtime": ("python-profile", "test-dependencies"),
    "sources": ("source-universe", "clause-coverage", "predicate-expansion"),
    "qualification": ("complete-history", "consumed-admission"),
    "bitcoin-pre-signing": ("model-bitcoin-capability",),
    "candidate-review": ("manifest-role-closure", "finding-closure"),
}
_ROOT_CHECKS = ("root_identity", "root_project", "root_role", "initial_authority", "initial_action_scope", "initial_effective_boundary", "authority_fork_absent", "initial_rule_binding", "initial_subject_class", "initial_no_predecessor")
_ACCEPTANCE_CHECKS = ("acceptance_identity", "acceptance_decision", "acceptance_exact_refs", "acceptance_blockers")
_MANIFEST_CHECKS = ("manifest_identity", "manifest_scope_sequence", "manifest_no_self_acceptance", "dependency_roles", "dependency_cardinality", "dependency_types", "dependency_acyclic")
_REPORT_SEMANTICS = ("required_report_roles", "report_subject_stage", "report_validator_dependencies", "report_raw_replay", "report_cardinality", "report_formation_acyclic")
_FINDING_SEMANTICS = ("finding_union", "finding_exact_closure", "finding_no_waiver")
_AUTH_SEMANTICS = ("authentication_contract", "authentication_consequential_coverage", "authentication_acyclic", "acceptance_actor_authority", "acceptance_authentication")


def _check(name, condition, reason):
    return Check(name, "UNKNOWN" if condition is None else "PASS" if condition else "FAIL", reason)


def _read(ref, resolver):
    try:
        return resolve_exact(ref, resolver), ()
    except AuthorityPrimitiveError as exc:
        status = "UNKNOWN" if str(exc) == "NO_AUTHORITATIVE_RESULT" else "FAIL"
        return None, (Check("exact-input", status, str(exc)),)


def _dependency_graph_checks(basis, report_ref, dependencies, acceptance_ref, resolver):
    """Resolve every explicit edge; verify formation order from typed objects.

    Fixed model sources are terminal authority inputs. Reports and the model
    manifest expose their full dependency collections. Unknown object kinds
    cannot certify a complete, acyclic pre-signing graph.
    """
    checks, nested_reports, input_refs = [], [], []
    fixed = {ExactRef.from_mapping(x) for x in MODEL_SOURCE_REFS.values()}
    fixed_by_id = {r.object_id: r for r in fixed}
    pending = [(x, (report_ref.object_id,)) for x in dependencies]
    examined = 0
    while pending:
        data, path = pending.pop()
        examined += 1
        if examined > 4096:
            checks.append(Check("report-graph", "UNKNOWN", "REPORT_DEPENDENCY_GRAPH_BOUND_EXCEEDED"))
            break
        try:
            ref = ExactRef.from_mapping(data)
        except (ValueError, TypeError):
            checks.append(Check("report-dependency", "FAIL", "REPORT_DEPENDENCY_REFERENCE_INVALID"))
            continue
        if ref.object_id == acceptance_ref.object_id or ref.object_id in path:
            checks.append(Check("report-acyclic", "FAIL", "PRE_SIGNING_ACCEPTANCE_OR_FINAL_REPORT_CYCLE"))
            continue
        obj, errors = _read(ref, resolver)
        input_refs.append(ref)
        checks.extend(errors)
        if obj is None:
            continue
        kind = obj.get("object_type")
        if kind in {"ManifestAcceptance", "SyntheticFinalReplayReport", "ReplayResult"}:
            checks.append(Check("report-acyclic", "FAIL", "PRE_SIGNING_ACCEPTANCE_OR_FINAL_REPORT_CYCLE"))
            continue
        if ref.object_id in fixed_by_id:
            checks.append(_check("report-dependency-pin", ref == fixed_by_id[ref.object_id], "REPORT_DEPENDENCY_FIXED_SOURCE_IDENTITY"))
            continue
        if kind == "SyntheticReplayReport":
            # The fixed model roles consume authority sources/manifest, not
            # extra reports chosen by the submitter. Still retain all known
            # nested failures/findings instead of dropping invalid inputs.
            checks.append(Check("report-dependency-role", "FAIL", "REPORT_DEPENDENCY_ROLE_NOT_PERMITTED"))
            nested_reports.append(obj)
            checks.append(_check("nested-report-stage", obj.get("stage") == "PRE_SIGNING", "WRONG_REPORT_STAGE"))
            checks.extend(_raw_report_failures(obj.get("checks")))
            if obj.get("status") == "FAIL":
                checks.append(Check("nested-report", "FAIL", "REPORT_RAW_BLOCKING_CHECK"))
            edges = obj.get("dependency_refs")
            valid = obj.get("schema_version") == "MODEL_REPORT_V1" and obj.get("model_only") is True and isinstance(edges, list)
        elif kind == "SyntheticCandidateManifest":
            checks.append(_check("report-manifest-dependency", ref == basis.subject, "REPORT_DEPENDENCY_MANIFEST_IDENTITY"))
            roles = obj.get("dependency_roles")
            valid = obj.get("model_only") is True and isinstance(roles, list) and all(isinstance(x, dict) and "ref" in x for x in roles)
            edges = [x["ref"] for x in roles] if valid else None
        else:
            checks.append(Check("report-dependency", "UNKNOWN", "REPORT_DEPENDENCY_KIND_UNSUPPORTED"))
            continue
        if not valid:
            checks.append(Check("report-dependency-schema", "FAIL", "REPORT_DEPENDENCY_COLLECTION_INVALID"))
            continue
        pending.extend((x, (*path, ref.object_id)) for x in edges)
    if not checks:
        checks.append(Check("report-acyclic", "PASS", "COMPLETE_TYPED_REPORT_DEPENDENCY_GRAPH"))
    return tuple(checks), tuple(nested_reports), tuple(input_refs)


def _raw_report_failures(raw):
    """A missing adjacent collection never discards a known raw failure."""
    checks = []
    if not isinstance(raw, list):
        return ()
    for row in raw:
        if not isinstance(row, dict):
            continue
        if row.get("status") == "FAIL":
            checks.append(Check(str(row.get("check_id")), "FAIL", "REPORT_RAW_BLOCKING_CHECK"))
        elif row.get("status") not in ("PASS", "UNKNOWN"):
            checks.append(Check(str(row.get("check_id")), "FAIL", "REPORT_INVALID_CHECK_STATUS"))
    return tuple(checks)


def replay_acceptance_bindings(basis, requirements, resolver, *, acceptance_ref, report_refs, component_reports=None):
    """Internal adapter, never a full-claim entry point or source of authority."""
    native = {}
    inputs = (basis.subject, basis.root_ref, basis.rule_ref, acceptance_ref, *report_refs)
    def publish(names, checks, seam=False, findings=()):
        for name in names:
            native[name] = NativeReplay(tuple(checks), tuple(r for r in inputs if r), seam, tuple(findings))

    root, root_errors = _read(basis.root_ref, resolver)
    rule, rule_errors = _read(basis.rule_ref, resolver)
    scope, scope_errors = _read(basis.scope_ref, resolver)
    root_checks = (*root_errors, *rule_errors, *scope_errors,
        _check("root", None if root is None else True, "ROOT_EXACT_BYTES_REPLAYED"),
        _check("project", None if root is None else root.get("project") == basis.project, "ROOT_PROJECT_BINDING"),
        _check("authority", None if root is None else root.get("authority") == "MODEL_INITIAL_ACCEPT_ONLY", "FINITE_INITIAL_MODEL_AUTHORITY"),
        _check("action", None if scope is None else scope.get("action") == "INITIAL_ACCEPT", "INITIAL_ACTION_SCOPE"),
        _check("subject-class", None if scope is None else scope.get("subject_class") == "SyntheticCandidateManifest", "INITIAL_SUBJECT_CLASS"),
        _check("effective", None if root is None else root.get("effective") <= "2030-02-01T00:00:00Z", "INITIAL_EFFECTIVE_BOUNDARY"),
        _check("forks", None if root is None else root.get("forks") == [], "NO_AUTHORITY_FORK"),
        _check("rule", None if root is None else root.get("initial_rule") == basis.rule_ref.to_dict(), "ROOT_SELECTED_INITIAL_RULE"),
        _check("rule-bytes", None if rule is None else True, "INITIAL_RULE_EXACT_BYTES_REPLAYED"),
    )
    publish(_ROOT_CHECKS, root_checks)
    manifest, manifest_errors = _read(basis.subject, resolver)
    manifest_checks = list(manifest_errors)
    if manifest is not None:
        expected_roles = {role: ref for role, ref in MODEL_SOURCE_REFS.items() if role not in {"root", "selection", "scope"}}
        actual = manifest.get("dependency_roles", [])
        role_names = [item.get("role") for item in actual]
        manifest_checks.extend((
            _check("manifest-type", manifest.get("object_type") == "SyntheticCandidateManifest" and manifest.get("model_only") is True, "MODEL_MANIFEST_TYPE_ORIGIN"),
            _check("sequence", manifest.get("sequence") == 0 and manifest.get("project") == basis.project, "INITIAL_MANIFEST_PROJECT_SEQUENCE"),
            _check("self-acceptance", manifest.get("status") == "MODEL_UNACCEPTED", "MANIFEST_SELF_ACCEPTANCE_PROHIBITED"),
            _check("roles", set(role_names) == set(expected_roles) and len(role_names) == len(set(role_names)), "DEPENDENCY_ROLE_CARDINALITY"),
            _check("refs", all(item.get("ref") == expected_roles.get(item.get("role")) for item in actual), "DEPENDENCY_EXACT_ROLE_REFS"),
            _check("closure", all(ExactRef.from_mapping(ref) in requirements.sources for ref in expected_roles.values()), "DEPENDENCY_SOURCE_CLOSURE"),
        ))
    publish(_MANIFEST_CHECKS, manifest_checks)

    acceptance, acceptance_errors = _read(acceptance_ref, resolver)
    acceptance_checks = list(acceptance_errors)
    if acceptance is not None:
        try:
            validate_manifest_acceptance_v2_contract(acceptance)
            acceptance_checks.append(Check("acceptance-contract", "PASS", "LOCAL_ACCEPTANCE_CONTRACT_VALID"))
        except (ValueError, TypeError, KeyError) as exc:
            acceptance_checks.append(Check("acceptance-contract", "FAIL", "ACCEPTANCE_CONTRACT_INVALID"))
        if manifest is not None:
            local = validate_manifest_acceptance_v2(manifest, acceptance, bootstrap_root_ref=basis.root_ref.to_dict(),
                                                     acceptance_rule_ref=basis.rule_ref.to_dict(), required_validation_report_refs=[r.to_dict() for r in report_refs])
            acceptance_checks.extend(local.checks)
        acceptance_checks.append(_check("authority-role", acceptance.get("authority_ref") == basis.root_ref.to_dict(), "INITIAL_AUTHORITY_ROLE_BINDING"))
    publish(_ACCEPTANCE_CHECKS, acceptance_checks)

    report_checks = []
    reports = []
    all_findings = []
    all_closures = []
    finding_inputs_complete = True
    roles = []
    if len(set(report_refs)) != len(report_refs):
        report_checks.append(Check("report-refs", "FAIL", "DUPLICATE_REPORT_IDENTITY"))
    for report_ref in report_refs:
        report, errors = _read(report_ref, resolver)
        report_checks.extend(errors)
        if report is None:
            finding_inputs_complete = False
            continue
        reports.append(report)
        kind = report.get("kind") if isinstance(report.get("kind"), str) else None
        roles.append(kind)
        fields = ("dependency_refs", "checks", "finding_refs", "finding_closure_refs")
        collections = {}
        if report.get("status") == "FAIL":
            report_checks.append(Check("report-declared", "FAIL", "REPORT_DECLARED_BLOCKER"))
        report_checks.extend(_raw_report_failures(report.get("checks")))
        for field in fields:
            value = report.get(field, [] if field == "finding_closure_refs" else None)
            if value is None and field not in report:
                report_checks.append(Check("report-schema", "UNKNOWN", "REPORT_REQUIRED_COLLECTION_MISSING"))
                finding_inputs_complete = False
            elif not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
                report_checks.append(Check("report-schema", "FAIL", "REPORT_COLLECTION_SCHEMA_INVALID"))
                finding_inputs_complete = False
            collections[field] = [x for x in value if isinstance(x, dict)] if isinstance(value, list) else []
        binding_checks = (
            _check("report-type", report.get("object_type") == "SyntheticReplayReport" and report.get("schema_version") == "MODEL_REPORT_V1" and report.get("model_only") is True, "MODEL_REPORT_SCHEMA_ORIGIN"),
            _check("report-kind", kind in REPORT_CHECKS, "WRONG_REPORT_KIND"),
            _check("report-subject", report.get("subject_ref") == basis.subject.to_dict(), "WRONG_REPORT_SUBJECT"),
            _check("report-stage", report.get("stage") == "PRE_SIGNING", "WRONG_REPORT_STAGE"),
            _check("report-validator", report.get("validator_ref") == basis.profile[0].to_dict(), "WRONG_REPORT_VALIDATOR"),
        )
        report_checks.extend(binding_checks)
        if any(c.status != "PASS" for c in binding_checks):
            finding_inputs_complete = False
        dependencies = collections["dependency_refs"]
        report_checks.append(_check("report-dependencies", basis.rule_ref.to_dict() in dependencies, "WRONG_REPORT_DEPENDENCIES"))
        graph_checks, nested_reports, graph_refs = _dependency_graph_checks(basis, report_ref, dependencies, acceptance_ref, resolver)
        report_checks.extend(graph_checks)
        inputs += graph_refs
        for nested in nested_reports:
            for field, destination in (("finding_refs", all_findings), ("finding_closure_refs", all_closures)):
                value = nested.get(field, [] if field == "finding_closure_refs" else None)
                if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
                    finding_inputs_complete = False
                if isinstance(value, list):
                    destination.extend(x for x in value if isinstance(x, dict))
        raw = collections["checks"]
        ids = [c.get("check_id") if isinstance(c.get("check_id"), str) else None for c in raw]
        if kind in REPORT_CHECKS:
            report_checks.append(_check("check-cardinality", set(ids) == set(REPORT_CHECKS[kind]) and len(ids) == len(set(ids)), "REPORT_RAW_CHECK_COVERAGE"))
        replayed = None if component_reports is None else component_reports.get(kind)
        if replayed is None:
            report_checks.append(Check(str(kind), "UNKNOWN", "REPORT_REPLAY_NOT_EXECUTED"))
        else:
            actual_rows = [{"check_id": c.check_id, "status": c.status, "reason_code": c.reason_code} for c in replayed]
            equality = raw == actual_rows and report.get("status") == reduce_checks(replayed)
            # A retained PASS is not contradicted merely by currently missing
            # execution inputs. Known report blockers and actual FAIL remain
            # separately in the conjunction and retain FAIL priority.
            report_checks.append(Check("raw-equality", "PASS" if equality else "UNKNOWN" if reduce_checks(replayed) == "UNKNOWN" else "FAIL", "REPORT_CURRENT_REPLAY_UNAVAILABLE" if not equality and reduce_checks(replayed) == "UNKNOWN" else "PERSISTED_REPORT_DIFFERS_FROM_RAW_REPLAY"))
            report_checks.extend(replayed)  # Preserve real FAIL/UNKNOWN, never label substitution.
        all_findings.extend(collections["finding_refs"])
        all_closures.extend(collections["finding_closure_refs"])
    complete_roles = set(roles) == set(REPORT_CHECKS) and len(roles) == len(REPORT_CHECKS)
    report_checks.append(_check("roles", complete_roles, "REQUIRED_REPORT_ROLE_CARDINALITY"))
    if not complete_roles:
        finding_inputs_complete = False
    publish(_REPORT_SEMANTICS, report_checks)

    if acceptance is not None and isinstance(acceptance.get("blocking_finding_refs"), list):
        all_findings.extend(acceptance["blocking_finding_refs"])
    else:
        finding_inputs_complete = False
    finding_checks, finding_refs = _replay_findings(basis, resolver, all_findings, all_closures, finding_inputs_complete)
    publish(_FINDING_SEMANTICS, finding_checks, findings=finding_refs)

    if basis.mode == "PUBLIC_EVIDENCE":
        auth_checks = (Check("authentication", "UNKNOWN", "BLOCKED_BY_G02"),)
        publish(_AUTH_SEMANTICS, auth_checks)
    else:
        carrier = None
        carrier_errors = ()
        if acceptance is not None:
            try:
                carrier, carrier_errors = _read(ExactRef.from_mapping(acceptance.get("signature_ref")), resolver)
            except (ValueError, TypeError):
                carrier_errors = (Check("authentication-ref", "FAIL", "ACCEPTANCE_SIGNATURE_REFERENCE_INVALID"),)
        auth_checks = list(carrier_errors)
        auth_checks.append(_check("authentication-model-fact", None if carrier is None else
            carrier.get("object_type") == "SyntheticAuthenticationFact" and carrier.get("model_only") is True and
            carrier.get("actor") == "MODEL_OWNER" and carrier.get("action") == "INITIAL_ACCEPT" and
            carrier.get("subject_ref") == basis.subject.to_dict() and carrier.get("root_ref") == basis.root_ref.to_dict(),
            "FORMULA_FREE_SYNTHETIC_AUTHENTICATION_SEAM"))
        # This is the only authentication substitution; not crypto replay and
        # never a signing projection/message/domain for a real acceptance.
        publish(_AUTH_SEMANTICS, auth_checks, seam=True)
    return emit_records(requirements, native, __file__)


def _replay_findings(basis, resolver, declared, declared_closures=(), inputs_complete=True):
    checks, refs = [], []
    closure_objects = []
    for data in declared_closures:
        try:
            closure, errors = _read(ExactRef.from_mapping(data), resolver)
        except (ValueError, TypeError):
            closure, errors = None, (Check("closure-ref", "FAIL", "MALFORMED_CLOSURE_REFERENCE"),)
        checks.extend(errors)
        if closure is not None:
            closure_objects.append(closure)
    if not inputs_complete:
        checks.append(Check("finding-union", "UNKNOWN", "COMPLETE_FINDING_INPUTS_NOT_ESTABLISHED"))
    for data in declared:
        try:
            ref = ExactRef.from_mapping(data)
        except (ValueError, TypeError):
            checks.append(Check("finding", "FAIL", "MALFORMED_FINDING_REFERENCE"))
            continue
        if ref in refs:
            continue
        refs.append(ref)
        finding, errors = _read(ref, resolver)
        checks.extend(errors)
        if finding is None:
            continue
        if finding.get("object_type") != "SyntheticFinding" or finding.get("model_only") is not True or not isinstance(finding.get("blocking"), bool) or finding.get("state") not in ("OPEN", "CLOSED"):
            checks.append(Check("finding-schema", "FAIL", "FINDING_SCHEMA_INVALID"))
            continue
        checks.append(_check("finding-subject", finding.get("subject_ref") == basis.subject.to_dict(), "FINDING_WRONG_SUBJECT"))
        if not finding.get("blocking"):
            continue
        # Closure is separate evidence for the immutable original finding;
        # no circular requirement to hash a CLOSED object pointing to its
        # own closure that in turn hashes that same object.
        closure = next((c for c in closure_objects if c.get("finding_ref") == ref.to_dict()), None)
        if closure is None and finding.get("closure_ref"):
            try:
                closure, errors = _read(ExactRef.from_mapping(finding["closure_ref"]), resolver)
            except (ValueError, TypeError):
                closure, errors = None, (Check("closure-ref", "FAIL", "MALFORMED_CLOSURE_REFERENCE"),)
            checks.extend(errors)
        if closure is None:
            checks.append(Check("finding-blocker", "FAIL", "APPLICABLE_BLOCKING_FINDING"))
            continue
        if closure is not None:
            checks.append(_check("closure-binding", closure.get("object_type") == "SyntheticFindingClosure" and closure.get("model_only") is True and closure.get("subject_ref") == basis.subject.to_dict() and closure.get("finding_ref") == ref.to_dict(), "FINDING_CLOSURE_WRONG_SUBJECT_OR_FINDING"))
            evidence = closure.get("evidence_refs", [])
            if not isinstance(evidence, list):
                checks.append(Check("closure-evidence", "FAIL", "MALFORMED_CLOSURE_EVIDENCE_REFERENCE"))
                continue
            checks.append(_check("closure-evidence", bool(evidence), "FINDING_CLOSURE_EVIDENCE_MISSING"))
            for proof in evidence:
                try:
                    obj, errors = _read(ExactRef.from_mapping(proof), resolver)
                except (ValueError, TypeError):
                    obj, errors = None, (Check("closure-evidence", "FAIL", "MALFORMED_CLOSURE_EVIDENCE_REFERENCE"),)
                checks.extend(errors)
                if obj is None:
                    continue
                checks.append(_check("closure-evidence-binding", obj.get("object_type") == "SyntheticClosureEvidence" and obj.get("model_only") is True and obj.get("subject_ref") == basis.subject.to_dict() and obj.get("root_ref") == basis.root_ref.to_dict(), "CLOSURE_EVIDENCE_BINDING"))
                checks.append(_check("closure-check-binding", None if not finding.get("check_id") else obj.get("check_id") == finding.get("check_id"), "FINDING_CLOSURE_CHECK_MISMATCH"))
                if obj.get("check_id") != "root-project":
                    checks.append(Check("closure-replay", "UNKNOWN", "CLOSURE_CHECK_REPLAY_UNSUPPORTED"))
                else:
                    root, errors = _read(basis.root_ref, resolver)
                    checks.extend(errors)
                    checks.append(_check("closure-replay", None if root is None else root.get("project") == basis.project and obj.get("expected_status") == "PASS", "EXACT_FINDING_CLOSURE_REEXECUTED"))
    if not checks:
        checks.append(Check("finding-union", "PASS", "COMPLETE_REQUIRED_REPORT_FINDING_UNION_EMPTY"))
    return tuple(checks), tuple(refs)
