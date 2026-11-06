"""Finite MODEL ONLY B→S→locations→C→L→M reconstruction.

Source-specific rules are verifier-owned. Exact identities do not establish
real trust/applicability; unrecognized public profiles stay unresolved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .authority_primitives_v1 import ExactRef, ExactRefResolver
from .canonical import parse_json_strict, verify_sealed_object, seal_object
from .core import Check
from .g10_replay_v1 import (
    ReplayBasis, PredicateKey, CompletenessProof, G10ReducerInput,
    PredicateResult, mandatory_set_identity,
)
from .replay_model_v1 import MODEL_BASIS_DATA, MODEL_SOURCE_REFS, MODEL_CHECK_SPECS

CHECK_SPECS = dict(MODEL_CHECK_SPECS)
_EXPECTED_CHECKS = frozenset(MODEL_CHECK_SPECS)
_META = {"object_id", "object_type", "payload_sha256", "content_sha256", "kind", "model_version"}
_DOMAINS = frozenset({"governance", "targets", "providers", "source_contracts", "cycles", "slots", "reports", "fixtures", "events", "workflow"})
# All non-clause consequential source fields have a source-specific semantic
# mapping. Descendant values inherit this mapping only inside a known shape.
_FIELDS = {
    "root": {"project": "root_project", "initial_rule": "initial_rule_binding", "selection_rule": "source_closure", "scope": "initial_action_scope", "authority": "initial_authority", "effective": "initial_effective_boundary", "actor": "acceptance_actor_authority", "forks": "authority_fork_absent"},
    "selection": {"required_sources": "source_closure", "exclusion": "source_closure"},
    "scope": {"project": "root_project", "action": "initial_action_scope", "subject_class": "initial_subject_class", "horizon": "calendar_horizon_boundaries", "domains": "source_closure", "qualification_boundaries": "history_scope_head"},
    "target": {"name": "target_method_compatibility", "method": "target_method_compatibility", "unit": "NT06_type_unit_decimal", "prediction_type": "NT06_type_unit_decimal", "resolution": "source_resolution_binding"},
    "resolution": {"name": "source_resolution_binding", "vintage": "NT07_first_release_resolution", "ambiguity": "NT07_conflict_ambiguity", "corrections": "NT07_correction_withdrawal", "scoring": "NT08_cohort_scoring"},
    "source_contract": {"name": "source_resolution_binding", "target": "source_resolution_binding", "parser": "parser_pairing", "source_kind": "source_resolution_binding", "official_model_source": "retrospective_source_vintage", "revision_policy": "calendar_page_revision_coverage"},
    "provider": {"name": "formation_authority", "authority_role": "formation_authority", "history_rule": "history_scope_head", "permission": "formation_permission", "independence": "formation_independence_review"},
    "method": {"name": "NT03_method_configuration", "configuration": "NT03_method_configuration", "retry": "NT04_failure_retry_budget", "control": "NT05_control_class"},
    "profile": {"name": "runtime_pairing", "python": "runtime_pairing", "pytest": "runtime_pairing", "jsonschema": "runtime_pairing", "parser": "parser_pairing", "tzdb": "calendar_parser_tzdb", "signing": "authentication_contract", "wall": "wall_signature_delegation", "bitcoin": "bitcoin_pin_chain"},
}
# Immutable verifier-side semantic specification, retained separately from
# the executable mapping table so a mapping substitution cannot self-certify.
_EXPECTED_FIELD_SEMANTICS = tuple((kind, field, semantic)
                                for kind, fields in _FIELDS.items()
                                for field, semantic in fields.items())


@dataclass(frozen=True)
class SourceLocation:
    source_ref: ExactRef
    location: str
    value: object
    disposition: str
    reason: str
    check: str | None = None


@dataclass(frozen=True)
class RequirementClause:
    requirement_id: str
    check: str
    source_ref: ExactRef
    source_location: str
    covered_locations: tuple[str, ...]
    keys: tuple[PredicateKey, ...]


@dataclass(frozen=True)
class RequirementUniverse:
    basis: ReplayBasis
    required_sources: tuple[ExactRef, ...]
    sources: tuple[ExactRef, ...]
    source_objects: Mapping[str, dict]
    inventory: tuple[SourceLocation, ...]
    requirements: tuple[RequirementClause, ...]
    mandatory_keys: tuple[PredicateKey, ...]
    domains: Mapping[str, tuple[dict, ...]]
    proofs: tuple[CompletenessProof, CompletenessProof, CompletenessProof]
    diagnostics: tuple[Check, ...]
    overall: str
    derivations: tuple[dict, ...]

    def reducer_input(self, records: tuple[PredicateResult, ...]) -> G10ReducerInput:
        return G10ReducerInput(self.basis, self.mandatory_keys, *self.proofs, records)


def _walk(value, location=""):
    # Visit EVERY raw node, including empty containers. No allowlist filtering
    # occurs before inventory construction.
    yield location or "/", value
    if isinstance(value, dict):
        for k, v in sorted(value.items()):
            escaped = k.replace("~", "~0").replace("/", "~1")
            yield from _walk(v, f"{location}/{escaped}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk(v, f"{location}/{i}")


def _known_shape(obj, path):
    parts = path.strip("/").split("/")
    top = parts[0]
    rest = parts[1:]
    if top == "requirements":
        return not rest or (rest[0].isdigit() and (len(rest) == 1 or
            (rest[1] in {"id", "check", "predicate", "domain", "parameters"} and len(rest) == 2)))
    if top in {"initial_rule", "selection_rule", "scope"}:
        return not rest or (len(rest) == 1 and rest[0] in {"object_id", "content_sha256"})
    if top == "horizon":
        return not rest or (len(rest) == 1 and rest[0] in {"start", "end"})
    if top == "configuration":
        return not rest or (len(rest) == 1 and rest[0] in {"selection", "arithmetic"})
    if top == "retry":
        return not rest or rest == ["budget"] or rest == ["eligible_failures"] or (
            len(rest) == 2 and rest[0] == "eligible_failures" and rest[1].isdigit())
    if top == "domains":
        if not rest:
            return True
        if rest[0] not in _DOMAINS:
            return False
        rest = rest[1:]
        if not rest or (len(rest) == 1 and rest[0].isdigit()):
            return True
        return _domain_member_shape(rest)
    if top == "qualification_boundaries":
        return not rest or (len(rest) == 1 and rest[0].isdigit()) or _domain_member_shape(rest)
    if top == "required_sources":
        return (not rest or (rest[0].isdigit() and (len(rest) == 1 or
            (len(rest) == 2 and rest[1] in {"role", "ref", "cardinality"}) or
            (len(rest) == 3 and rest[1] == "ref" and rest[2] in {"object_id", "content_sha256"}))))
    return not rest


def _domain_member_shape(parts):
    return (len(parts) == 2 and parts[0].isdigit() and parts[1] in {"name", "subject", "boundary"}) or (
        len(parts) == 3 and parts[0].isdigit() and parts[1] == "subject" and parts[2] in {"object_id", "content_sha256"})


def inventory_source(ref: ExactRef, obj: dict) -> tuple[SourceLocation, ...]:
    rows = []
    for path, value in _walk(obj):
        top = path.strip("/").split("/")[0]
        check = None
        if path == "/" or (isinstance(value, (dict, list)) and value):
            disposition, reason = "NON_CONSEQUENTIAL", "STRUCTURE_INVENTORIED_ALL_CHILDREN"
        elif top in _META and path == "/" + top:
            disposition, reason = "NON_CONSEQUENTIAL", "EXACT_IDENTITY_KIND_VERSION_CHECKED_BEFORE_EXTRACTION"
        elif top == "model_only" and path == "/model_only":
            check = "runtime_pairing"
            disposition, reason = "CONSEQUENTIAL", "MODEL_ORIGIN_MUST_NOT_BECOME_REAL_AUTHORITY"
        elif top == "requirements" and _known_shape(obj, path):
            parts = path.split("/")
            if len(parts) >= 3 and parts[2].isdigit():
                check = obj["requirements"][int(parts[2])].get("check")
                disposition, reason = "CONSEQUENTIAL", "ATOMIC_RULE_CONJUNCT_OR_DOMAIN_BINDING"
            else:
                disposition, reason = "UNKNOWN", "OBLIGATION_LIST_SEMANTICS_UNESTABLISHED"
        elif top in _FIELDS.get(obj.get("kind"), {}) and _known_shape(obj, path):
            check = _FIELDS[obj["kind"]][top]
            disposition, reason = "CONSEQUENTIAL", "SOURCE_SPECIFIC_FIELD_SEMANTICS"
        else:
            disposition, reason = "UNKNOWN", "UNRECOGNIZED_LOCATION_SEMANTICS"
        rows.append(SourceLocation(ref, path, value, disposition, reason, check))
    return tuple(rows)


def classify_exclusion(evidence: Mapping[str, object]) -> str:
    # This model has no excluded source or domain. Arbitrary rationale never
    # authorizes N/A. Real exclusions require a separately applicable contract.
    return "UNKNOWN"


def _overall(checks):
    return "FAIL" if any(c.status == "FAIL" for c in checks) else "UNKNOWN" if any(c.status == "UNKNOWN" for c in checks) else "PASS"


def _fixed_basis():
    d = dict(MODEL_BASIS_DATA)
    for k, v in tuple(d.items()):
        if isinstance(v, dict):
            d[k] = ExactRef.from_mapping(v)
    d["profile"] = tuple(ExactRef.from_mapping(v) for v in d["profile"])
    return ReplayBasis(**d)


def reconstruct_requirements(basis: ReplayBasis, resolver: ExactRefResolver) -> RequirementUniverse:
    expected = _fixed_basis()
    checks = []
    selection_checks, coverage_checks, expansion_checks = [], [], []
    objects, inventories, clauses, domains = {}, [], [], {}
    for name in expected.__dataclass_fields__:
        if name == "mode":
            continue
        actual, wanted = getattr(basis, name), getattr(expected, name)
        if actual in (None, "", ()):
            selection_checks.append(Check(name, "UNKNOWN", "INDEPENDENT_BASIS_MISSING"))
        elif actual != wanted:
            reason = "MODEL_PROFILE_NOT_ESTABLISHED" if name == "profile" else "INDEPENDENT_BASIS_MISMATCH"
            selection_checks.append(Check(name, "UNKNOWN" if name == "profile" else "FAIL", reason))
    if basis.mode not in {"SYNTHETIC_MODEL", "PUBLIC_EVIDENCE"}:
        selection_checks.append(Check("mode", "FAIL", "UNSUPPORTED_REPLAY_MODE"))

    # Start with independently fixed B anchors, then verify and traverse the
    # root-selected selection rule. Never enumerate caller resolver contents.
    anchors = (expected.root_ref, expected.rule_ref, expected.scope_ref,
               expected.source_selection_rule_ref, expected.historical_rule_ref,
               expected.workflow_rule_ref, *expected.profile)
    required = list(dict.fromkeys(anchors))
    resolved = []
    index = 0
    while index < len(required):
        ref = required[index]
        index += 1
        try:
            raw = resolver.resolve_exact(ref)
            if raw is None:
                selection_checks.append(Check(ref.object_id, "UNKNOWN", "SOURCE_BYTES_UNAVAILABLE"))
                continue
            obj = parse_json_strict(raw)
            if not isinstance(obj, dict) or ExactRef.from_mapping({k: obj.get(k) for k in ("object_id", "content_sha256")}) != ref or not verify_sealed_object(obj):
                selection_checks.append(Check(ref.object_id, "FAIL", "SOURCE_IDENTITY_MISMATCH"))
                continue
        except (ValueError, TypeError, KeyError) as exc:
            selection_checks.append(Check(ref.object_id, "FAIL", "SOURCE_PARSE_OR_IDENTITY_INVALID"))
            continue
        except Exception as exc:
            selection_checks.append(Check(ref.object_id, "UNKNOWN", f"SOURCE_RESOLVER_EXCEPTION:{type(exc).__name__}"))
            continue
        if obj.get("object_type") != "SyntheticReplaySource" or obj.get("model_only") is not True or obj.get("model_version") != "M1_FIXED_MODEL_V1":
            selection_checks.append(Check(ref.object_id, "FAIL", "SOURCE_MODEL_PROFILE_MISMATCH"))
            continue
        objects[ref.object_id] = obj
        resolved.append(ref)
        if ref == expected.source_selection_rule_ref:
            selected = obj.get("required_sources", [])
            roles = [x.get("role") for x in selected]
            if len(set(roles)) != len(roles) or any(x.get("cardinality") != 1 for x in selected):
                selection_checks.append(Check("selection", "FAIL", "SOURCE_ROLE_CARDINALITY_INVALID"))
            for item in selected:
                dep = ExactRef.from_mapping(item["ref"])
                fixed = MODEL_SOURCE_REFS.get(item["role"])
                if fixed is None or dep != ExactRef.from_mapping(fixed):
                    selection_checks.append(Check("selection", "FAIL", "SOURCE_ROLE_OR_VERSION_MISMATCH"))
                if dep not in required:
                    required.append(dep)
        inventories.extend(inventory_source(ref, obj))

    scope = objects.get(expected.scope_ref.object_id)
    if scope:
        domains = {d: tuple(members) for d, members in scope["domains"].items()}
        # Cartesian product preserves subject at identical timestamps. This
        # boundary source is fixed model input, not receipt-selected as-of.
        domains["provider_boundaries"] = tuple({
            "name": p["name"] + ":" + b["name"], "subject": p["subject"],
            "boundary": b["boundary"], "boundary_role": b["name"],
        } for p in domains["providers"] for b in scope["qualification_boundaries"])
    else:
        expansion_checks.append(Check("domains", "UNKNOWN", "INDEPENDENT_DOMAIN_UNESTABLISHED"))

    # Audit complete raw source locations independently with an iterative
    # traversal; it shares neither the extractor's _walk nor its classifier.
    # Known raw scalar/empty-container semantics must retain their disposition
    # and exact check, even when an executable field map silently changes.
    expected_fields = {(kind, field): check for kind, field, check in _EXPECTED_FIELD_SEMANTICS}
    for ref in resolved:
        obj = objects[ref.object_id]
        actual_rows = [r for r in inventories if r.source_ref == ref]
        actual_by_path = {r.location: r for r in actual_rows}
        raw_nodes = {}
        pending = [("/", obj)]
        while pending:
            path, value = pending.pop()
            raw_nodes[path] = value
            prefix = "" if path == "/" else path
            if isinstance(value, dict):
                for field, child in value.items():
                    escaped = field.replace("~", "~0").replace("/", "~1")
                    pending.append((prefix + "/" + escaped, child))
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    pending.append((prefix + "/" + str(i), child))
        if set(actual_by_path) != set(raw_nodes) or len(actual_rows) != len(raw_nodes):
            coverage_checks.append(Check(ref.object_id, "FAIL", "SOURCE_LOCATION_INVENTORY_OMISSION"))
        for path, value in raw_nodes.items():
            row = actual_by_path.get(path)
            if row is None:
                continue
            if row.value != value:
                coverage_checks.append(Check(path, "FAIL", "SOURCE_LOCATION_VALUE_MISMATCH"))
            if path == "/" or (isinstance(value, (dict, list)) and value):
                continue
            parts = path.strip("/").split("/")
            field = parts[0]
            wanted_check = None
            if field == "requirements" and len(parts) == 3 and parts[1].isdigit() and parts[2] in {"id", "check", "predicate", "domain", "parameters"}:
                wanted_check = obj["requirements"][int(parts[1])]["check"]
            elif field == "model_only" and len(parts) == 1:
                wanted_check = "runtime_pairing"
            elif (obj.get("kind"), field) in expected_fields:
                wanted_check = expected_fields[(obj["kind"], field)]
            if wanted_check is not None:
                if row.disposition != "CONSEQUENTIAL":
                    coverage_checks.append(Check(path, "FAIL", "SOURCE_FIELD_DISPOSITION_CONTRADICTION"))
                elif row.check != wanted_check:
                    coverage_checks.append(Check(path, "FAIL", "SOURCE_FIELD_MAPPING_CONTRADICTION"))

    # Immutable expectation for known exact source semantics prevents a deleted
    # mapping table from recategorizing required clauses as not required.
    seen_checks = set()
    clause_locations = set()
    for ref in resolved:
        obj = objects[ref.object_id]
        for i, rule in enumerate(obj.get("requirements", [])):
            name = rule.get("check")
            seen_checks.add(name)
            prefix = f"/requirements/{i}"
            covered = tuple(x.location for x in inventories if x.source_ref == ref and x.disposition == "CONSEQUENTIAL" and x.location.startswith(prefix + "/"))
            clause_locations.update((ref, loc) for loc in covered)
            wanted = MODEL_CHECK_SPECS.get(name)
            spec = CHECK_SPECS.get(name)
            if wanted is None:
                coverage_checks.append(Check(str(name), "UNKNOWN", "UNSUPPORTED_REQUIREMENT_SEMANTICS"))
            elif spec is None:
                coverage_checks.append(Check(name, "FAIL", "REQUIREMENT_MAPPING_MISSING"))
            elif spec != wanted or (rule.get("predicate"), rule.get("domain")) != wanted:
                coverage_checks.append(Check(name, "FAIL", "REQUIREMENT_MAPPING_CONTRADICTION"))
            keys = _expand(name, wanted, domains, ref, prefix + "/check", expansion_checks)
            clauses.append(RequirementClause(rule.get("id", str(name)), str(name), ref, prefix + "/check", covered, keys))
    for row in inventories:
        if row.disposition == "UNKNOWN":
            coverage_checks.append(Check(row.location, "UNKNOWN", "LOCATION_DISPOSITION_UNESTABLISHED"))
        elif row.disposition == "CONSEQUENTIAL" and (row.source_ref, row.location) not in clause_locations:
            spec = MODEL_CHECK_SPECS.get(row.check)
            if CHECK_SPECS.get(row.check) != spec or spec is None:
                coverage_checks.append(Check(row.location, "FAIL", "REQUIREMENT_MAPPING_MISSING"))
            keys = _expand(row.check, spec, domains, row.source_ref, row.location, expansion_checks)
            clauses.append(RequirementClause(f"{row.source_ref.object_id}{row.location}", row.check or "unsupported", row.source_ref, row.location, (row.location,), keys))
    if _overall(selection_checks) == "PASS" and seen_checks != _EXPECTED_CHECKS:
        coverage_checks.append(Check("clauses", "FAIL", "KNOWN_ATOMIC_REQUIREMENT_OMITTED"))

    # Independent expansion comparison starts from verified raw scope and
    # clauses, NOT from _expand's output or its derived domains. An expander
    # omission/substitution cannot establish its own completeness by hashing.
    if scope is not None:
        for clause in clauses:
            declared = MODEL_CHECK_SPECS.get(clause.check)
            if declared is None:
                continue
            predicate, domain_name = declared
            if domain_name == "provider_boundaries":
                raw_members = [
                    (provider["subject"], provider["name"] + ":" + boundary["name"], boundary["boundary"])
                    for provider in scope["domains"]["providers"]
                    for boundary in scope["qualification_boundaries"]
                ]
            else:
                raw_members = [(row["subject"], row["name"], row["boundary"])
                               for row in scope["domains"].get(domain_name, [])]
            if not raw_members:
                expansion_checks.append(Check(clause.requirement_id, "UNKNOWN", "RAW_QUANTIFIED_DOMAIN_NOT_ESTABLISHED"))
                continue
            directly_required = set()
            for subject_data, member_name, boundary in raw_members:
                role = clause.check + "@" + clause.source_ref.object_id + clause.source_location + "#" + member_name
                directly_required.add(PredicateKey(predicate, ExactRef.from_mapping(subject_data), role, boundary))
            if set(clause.keys) != directly_required or len(clause.keys) != len(directly_required):
                expansion_checks.append(Check(clause.requirement_id, "FAIL", "PREDICATE_INSTANCE_OMISSION_OR_SUBSTITUTION"))

    # Class meta-checks remain mandatory even if sources/domain are unresolved.
    meta_subject = expected.subject
    meta_keys = tuple(PredicateKey(f"P{i:02}", meta_subject, "CLASS_COMPLETENESS", "MODEL_SCOPE") for i in range(1, 26))
    keys = meta_keys + tuple(k for clause in clauses for k in clause.keys)
    if len(set(keys)) != len(keys):
        expansion_checks.append(Check("instances", "FAIL", "DUPLICATE_EXPANDED_INSTANCE"))
    if not clauses:
        coverage_checks.append(Check("clauses", "UNKNOWN", "NO_VERIFIABLE_REQUIREMENTS"))
    digest = mandatory_set_identity(keys)
    evidence_sets = (tuple(resolved), tuple(dict.fromkeys(c.source_ref for c in clauses)), tuple(dict.fromkeys(c.source_ref for c in clauses if c.keys)))
    lanes = (selection_checks, coverage_checks, expansion_checks)
    derivations = []
    proofs = []
    for name, lane, refs in zip(("SOURCE_UNIVERSE_COMPLETE", "CONSEQUENTIAL_REQUIREMENT_COVERAGE_COMPLETE", "PREDICATE_EXPANSION_COMPLETE"), lanes, evidence_sets):
        # Downstream completeness cannot claim established when an upstream
        # layer is unestablished. Known failures still retain priority.
        checks.extend(lane)
        status = _overall(checks)
        d = seal_object({"check": name, "status": status, "mandatory_set_identity": digest,
                         "source_refs": [r.to_dict() for r in refs],
                         "diagnostics": [{"check": c.check_id, "status": c.status, "reason": c.reason_code} for c in checks],
                         "requirements": [{"id": c.requirement_id, "source_location": c.source_location, "covered_locations": list(c.covered_locations), "keys": [_key_data(k) for k in c.keys]} for c in clauses] if name != "SOURCE_UNIVERSE_COMPLETE" else [],
                         "required_sources": [r.to_dict() for r in required]},
                        object_type="SyntheticCompletenessDerivation", stable_context="M1_DEVELOPMENT_ONLY")
        derivations.append(d)
        proof_ref = ExactRef(d["object_id"], d["content_sha256"])
        proofs.append(CompletenessProof(status, basis, refs + (proof_ref,), digest))
    return RequirementUniverse(basis, tuple(required), tuple(resolved), objects, tuple(inventories), tuple(clauses), keys, domains, tuple(proofs), tuple(checks), _overall(checks), tuple(derivations))


def _key_data(k):
    return {"predicate_id": k.predicate_id, "subject": k.subject.to_dict(), "role": k.role, "historical_boundary": k.historical_boundary}


def _expand(check, spec, domains, source, location, diagnostics):
    if spec is None:
        return ()
    predicate, domain = spec
    members = domains.get(domain)
    if members is None or not members:
        diagnostics.append(Check(str(check), "UNKNOWN", "QUANTIFIED_DOMAIN_NOT_ESTABLISHED"))
        return ()
    return tuple(PredicateKey(predicate, ExactRef.from_mapping(member["subject"]),
                              f"{check}@{source.object_id}{location}#{member['name']}", member["boundary"])
                 for member in members)
