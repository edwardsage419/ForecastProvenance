"""Keyless SYNTHETIC_TEST_ONLY actual-entry tests, not complete domain replay.

Run directly (-B -I -S), bypassing package __init__/conftest/old fixtures.
Real: strict parser/seals/ExactRef, D137/D139, G10 reducer, record emitter,
public auth guard and modified replay/persisted entry. Explicit upstream seams
replace historical/model/calendar/qualification/scientific source execution.
No private keys, signed messages/carriers, native backends or network.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'src' / 'forecast_trust_core'
NAMESPACE = '_public_ma3_observation_tests'
package = types.ModuleType(NAMESPACE)
package.__path__ = [str(SOURCE)]
sys.modules[NAMESPACE] = package


def load(name):
    spec = importlib.util.spec_from_file_location(f'{NAMESPACE}.{name}', SOURCE / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def seam(name, **members):
    mod = types.ModuleType(f'{NAMESPACE}.{name}')
    mod.__dict__.update(members)
    sys.modules[mod.__name__] = mod


def forbidden(*args, **kwargs):
    raise AssertionError('historical/model execution is outside these tests')


canonical = load('canonical')
core = load('core')
load('_checks')
authority = load('authority_primitives_v1')
g10 = load('g10_replay_v1')
records = load('replay_records_v1')
gate = load('claim_authority_contract_gate_v1')
bindings = load('architecture_compression_v1')
auth = load('initial_acceptance_public_auth_v1')

# Audited entry imports: preseed all history-bearing modules with explicit
# test-only seams. The real entry, native UNKNOWN guard and reducer still run.
seam('g10_requirements_v1', reconstruct_requirements=forbidden, _fixed_basis=lambda: 'NOT_A_TEST_BASIS')
seam('cycle_universe_v1', reconstruct_cycle_universe=forbidden)
seam('qualification_scope_v1', replay_qualification_scope=forbidden, consume_model_admissions=forbidden)
seam('confirmatory_replay_v1', replay_confirmatory_checks=forbidden)
seam('g10_external_evidence_v1', replay_external_evidence=forbidden,
     ExternalReplay=lambda events, measurements, checks, rows, overall, refs, **kw: types.SimpleNamespace(
         events=events, measurements=measurements, checks=checks, records=rows, overall=overall, input_refs=refs, **kw), SEAMS=())
seam('g10_acceptance_v1', replay_acceptance_bindings=forbidden, REPORT_CHECKS={}, _replay_findings=forbidden)
seam('integration_model_v1', observe_model_runtime=forbidden, replay_integration_checks=forbidden, read=forbidden, ASSUMPTIONS=())
seam('independent_replay_inputs_v1', CorpusResolver=forbidden)
component = load('independent_replay_v1')
Ref = authority.ExactRef


def ref(name, digest='a' * 64):
    return Ref('synthetic-test-only:' + name, digest)


def objref(obj):
    return Ref(obj['object_id'], obj['content_sha256'])


def seal(payload, kind='SyntheticObservationSubject', ident=None):
    return canonical.seal_object(payload, object_type=kind,
        stable_context='SYNTHETIC_TEST_ONLY', semantic_id=ident)


def reseal(obj, **changes):
    payload = {k: deepcopy(v) for k, v in obj.items()
               if k not in {'object_type', 'object_id', 'payload_sha256', 'content_sha256'}}
    payload.update(changes)
    return seal(payload, obj['object_type'])


def fixture():
    manifest = seal({'schema_version': 'SYNTHETIC_TEST_ONLY', 'value': 'manifest'})
    reports = [seal({'schema_version': 'SYNTHETIC_TEST_ONLY', 'value': str(n)}, ident=f'synthetic-test-only:report-{n}') for n in range(5)]
    report_refs = tuple(objref(o) for o in reports)
    root, rule = ref('root'), ref('rule')
    acceptance = seal({'schema_version': '3.0', 'candidate_manifest_ref': objref(manifest).to_dict(),
        'bootstrap_governance_root_ref': root.to_dict(), 'acceptance_rule_ref': rule.to_dict(),
        'authority_ref': root.to_dict(), 'signature_ref': ref('UNRESOLVED_REFERENCE_ONLY').to_dict(),
        'required_validation_report_refs': [r.to_dict() for r in report_refs],
        'decision': 'ACCEPT', 'reason_codes': [], 'blocking_finding_refs': []}, 'ManifestAcceptance')
    basis = g10.ReplayBasis('PUBLIC_EVIDENCE', 'SYNTHETIC_TEST_ONLY', 'INITIAL_ACCEPTANCE', 'TEST',
        objref(manifest), root, rule, ref('scope'), ref('effective'), ref('selection'), ref('history'), ref('workflow'), (ref('profile'),))
    data = {objref(o): canonical.canonical_json(o) for o in [manifest, acceptance, *reports]}
    return basis, {'acceptance_ref': objref(acceptance), 'required_report_refs': report_refs}, Resolver(data), acceptance


class Resolver:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def resolve_exact(self, rr):
        self.calls.append(rr)
        value = self.data.get(rr)
        if isinstance(value, Exception):
            raise value
        return value


def unknown_requirements(basis, resolver):
    # One explicitly incomplete test obligation. No source-universe PASS.
    key = g10.PredicateKey('SYNTHETIC_TEST_ONLY', ref('guard-subject'), 'MEMBER', 'TEST')
    clause = types.SimpleNamespace(check='public-authority', source_ref=ref('rule'),
        source_location='/test', requirement_id='TEST', keys=(key,))
    return types.SimpleNamespace(basis=basis, mandatory_keys=(key,), requirements=(clause,),
        required_sources=(ref('rule'),), diagnostics=(), overall='UNKNOWN',
        reducer_input=lambda rows: g10.G10ReducerInput(basis, (key,), None, None, None, rows))


class PublicMA3ObservationTests(unittest.TestCase):
    def setUp(self):
        for name, value in [('reconstruct_requirements', unknown_requirements),
            ('reconstruct_cycle_universe', lambda *a: types.SimpleNamespace(input_refs=())),
            ('replay_qualification_scope', lambda *a: types.SimpleNamespace(input_refs=())),
            ('replay_confirmatory_checks', lambda *a: types.SimpleNamespace(input_refs=()))]:
            p = patch.object(component, name, value); p.start(); self.addCleanup(p.stop)

    def run_entry(self, basis, request, resolver):
        result = component.replay_initial_acceptance(basis, resolver, public_inputs=request)
        self.assertFalse(result.prospective_eligible)
        self.assertEqual(result.real_genesis_readiness, 'NOT_ESTABLISHED')
        self.assertEqual(result.protocol_state_change, 'NONE')
        self.assertEqual(len(result.raw_results), 1)
        self.assertEqual(result.raw_results[0].normalized, 'UNKNOWN')
        self.assertEqual(result.raw_results[0].reason_codes, ('PUBLIC_CORE_AUTHORITY_NOT_ESTABLISHED',))
        return result

    def diagnostic(self, result):
        return component.stable_report(result)['public_input_observation']

    def has(self, result, reason, status):
        self.assertTrue(any(c['reason_code'] == reason and c['status'] == status
            for c in self.diagnostic(result)['checks']), (reason, self.diagnostic(result)))

    def put_acceptance(self, req, resolver, acceptance):
        req['acceptance_ref'] = objref(acceptance)
        resolver.data[req['acceptance_ref']] = canonical.canonical_json(acceptance)

    def test_none_preserves_old_public_output_shape_and_no_new_reads(self):
        basis, _, resolver, _ = fixture()
        result = component.replay_initial_acceptance(basis, resolver)
        self.assertEqual(result.overall, 'UNKNOWN')
        self.assertNotIn('public_input_observation', component.stable_report(result))
        self.assertEqual(resolver.calls, [])
        self.assertEqual(component.validate_persisted_independent_replay(basis, resolver,
            component.stable_report(result)).overall, 'UNKNOWN')

    def test_active_nonpublic_mode_is_rejected_before_any_work_or_reads(self):
        basis, request, resolver, _ = fixture()
        with patch.object(component, 'reconstruct_requirements', forbidden):
            for mode in ['SYNTHETIC_MODEL', 'OTHER']:
                with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'PUBLIC_INPUTS_REQUIRE_PUBLIC_EVIDENCE'):
                    component.replay_initial_acceptance(replace(basis, mode=mode), resolver, public_inputs=request)
        self.assertEqual(resolver.calls, [])

    def test_matching_local_inputs_reach_opaque_auth_but_remain_unknown(self):
        basis, request, resolver, acceptance = fixture()
        with patch.object(auth, 'verify_initial_acceptance_public', wraps=auth.verify_initial_acceptance_public) as spy:
            result = self.run_entry(basis, request, resolver)
        self.assertEqual(spy.call_args.kwargs['acceptance'], acceptance)
        self.assertEqual(result.overall, 'UNKNOWN')
        diag = self.diagnostic(result)
        self.assertTrue(all(c['status'] == 'PASS' for c in diag['checks']))
        self.assertIn('REPORT_IDENTITY_ONLY_NOT_CONTENT_OR_STRONG_REPLAY', diag['limitations'])
        self.assertTrue(all(c.status == 'UNKNOWN' for c in result.external.checks))
        self.assertEqual(Counter(resolver.calls), Counter([request['acceptance_ref'], basis.subject, *request['required_report_refs']]))
        self.assertNotIn(Ref.from_mapping(acceptance['signature_ref']), resolver.calls)
        self.assertEqual(auth.verify_initial_acceptance_public(basis=basis, acceptance=acceptance, resolver=resolver).message, None)

    def test_request_and_expected_set_reject_caller_results_and_malformed_values(self):
        basis, req, resolver, _ = fixture()
        invalid = [[], 'bad', 3, {'overall': 'PASS'}, {**req, 'eligibility': True}]
        for request in invalid:
            with self.subTest(request=request):
                result = self.run_entry(basis, request, resolver)
                self.has(result, 'PUBLIC_INPUT_REQUEST_INVALID', 'FAIL')
                self.assertEqual(result.overall, 'FAIL')
        reports = req['required_report_refs']
        for value in [[], reports[:4], (*reports, ref('sixth')), (reports[0], reports[0], *reports[2:]),
                      tuple(reversed(reports)), [None, *reports[1:]], {}, 'bad']:
            with self.subTest(value=value):
                result = self.run_entry(basis, {**req, 'required_report_refs': value}, resolver)
                self.has(result, 'PUBLIC_REQUIRED_REPORT_REFS_INVALID', 'FAIL')
        result = self.run_entry(basis, {**req, 'acceptance_ref': {}}, resolver)
        self.has(result, 'PUBLIC_REFERENCE_INVALID', 'FAIL')

    def test_missing_inputs_and_controls_are_unknown_not_empty_success(self):
        basis, req, resolver, _ = fixture()
        result = self.run_entry(replace(basis, subject=None, root_ref=None, rule_ref=None), {}, resolver)
        self.assertEqual(result.overall, 'UNKNOWN')
        self.has(result, 'PUBLIC_REFERENCE_MISSING', 'UNKNOWN')
        self.has(result, 'PUBLIC_REQUIRED_REPORT_REFS_MISSING', 'UNKNOWN')
        self.has(result, 'PUBLIC_BINDING_PREREQUISITES_UNAVAILABLE', 'UNKNOWN')
        self.assertEqual(resolver.calls, [])
        for field in ['subject', 'root_ref', 'rule_ref']:
            result = self.run_entry(replace(basis, **{field: 'invalid'}), req, resolver)
            self.has(result, 'PUBLIC_REFERENCE_INVALID', 'FAIL')

    def test_raw_input_parse_identity_and_resource_failures(self):
        cases = [(None, 'PUBLIC_SOURCE_UNAVAILABLE', 'UNKNOWN'),
            (RuntimeError('DO_NOT_PERSIST_EXCEPTION'), 'PUBLIC_SOURCE_UNAVAILABLE', 'UNKNOWN'),
            ('bad', 'PUBLIC_SOURCE_NOT_BYTES', 'FAIL'),
            (b'{}' * (512 * 1024 + 1), 'PUBLIC_LOCAL_SIZE_LIMIT', 'UNKNOWN'),
            (b'\xef\xbb\xbf{}', 'PUBLIC_JSON_INVALID', 'FAIL'),
            (b'{"x":1,"x":2}', 'PUBLIC_JSON_INVALID', 'FAIL'),
            (b'{"x":1.2}', 'PUBLIC_JSON_INVALID', 'FAIL'),
            (b'[]', 'PUBLIC_OBJECT_INVALID', 'FAIL'),
            (b'{}', 'PUBLIC_IDENTITY_INVALID', 'FAIL')]
        for raw, reason, status in cases:
            with self.subTest(reason=reason, kind=type(raw).__name__):
                basis, req, resolver, _ = fixture(); resolver.data[req['acceptance_ref']] = raw
                result = self.run_entry(basis, req, resolver)
                self.has(result, reason, status)
                self.assertNotIn('DO_NOT_PERSIST_EXCEPTION', repr(self.diagnostic(result)))
                self.assertEqual(len(set(resolver.calls)), 7)
        basis, req, resolver, acceptance = fixture()
        for bad in [seal({'value': 'other'}), {**acceptance, 'decision': 'REJECT'}]:
            resolver.data[req['acceptance_ref']] = canonical.canonical_json(bad)
            self.has(self.run_entry(basis, req, resolver), 'PUBLIC_IDENTITY_INVALID', 'FAIL')

    def test_contract_failures_do_not_forward_bad_acceptance_or_skip_reports(self):
        basis, req, resolver, acceptance = fixture()
        for change in [{'schema_version': '2.0'}, {'authority_ref': ref('other').to_dict()},
                       {'blocking_finding_refs': [ref('blocker').to_dict()]}]:
            self.put_acceptance(req, resolver, reseal(acceptance, **change))
            with patch.object(auth, 'verify_initial_acceptance_public', wraps=auth.verify_initial_acceptance_public) as spy:
                result = self.run_entry(basis, req, resolver)
            self.has(result, 'PUBLIC_MA3_CONTRACT_INVALID', 'FAIL')
            self.assertIsNone(spy.call_args.kwargs['acceptance'])
            for rr in req['required_report_refs']:
                self.assertIn(rr, resolver.calls)

    def test_actual_d139_bindings_detect_all_substitutions(self):
        basis, req, resolver, acceptance = fixture()
        changes = [('candidate_manifest_ref', ref('other').to_dict(), 'MANIFEST_HASH_MISMATCH'),
                   ('acceptance_rule_ref', ref('other').to_dict(), 'ACCEPTANCE_RULE_MISMATCH'),
                   ('required_validation_report_refs', [ref('replacement-' + str(i)).to_dict() for i in range(5)], 'VALIDATION_REPORT_SET_MISMATCH')]
        for field, value, reason in changes:
            with self.subTest(field=field):
                self.put_acceptance(req, resolver, reseal(acceptance, **{field: value}))
                self.has(self.run_entry(basis, req, resolver), reason, 'FAIL')
        wrong = ref('other-root').to_dict()
        self.put_acceptance(req, resolver, reseal(acceptance, authority_ref=wrong, bootstrap_governance_root_ref=wrong))
        self.has(self.run_entry(basis, req, resolver), 'BOOTSTRAP_ROOT_MISMATCH', 'FAIL')

    def test_reject_survives_missing_prerequisites_and_persisted_comparison(self):
        basis, req, resolver, acceptance = fixture()
        self.put_acceptance(req, resolver, reseal(acceptance, decision='REJECT'))
        cases = [(replace(basis, subject=None), req), (replace(basis, root_ref=None), req),
                 (replace(basis, rule_ref=None), req), (basis, {'acceptance_ref': req['acceptance_ref']})]
        for current_basis, request in cases:
            with self.subTest(basis=current_basis, request=request):
                fresh = self.run_entry(current_basis, request, resolver)
                self.assertEqual(fresh.reduced.overall, 'UNKNOWN')
                self.assertEqual(fresh.overall, 'FAIL')
                self.has(fresh, 'PUBLIC_MA3_DECISION_REJECT', 'FAIL')
                self.has(fresh, 'PUBLIC_BINDING_PREREQUISITES_UNAVAILABLE', 'UNKNOWN')
                cached = component.stable_report(fresh); cached['overall'] = 'PASS'
                compared = component.validate_persisted_independent_replay(current_basis, resolver, cached, public_inputs=request)
                self.assertEqual(compared.overall, 'FAIL')
                self.assertEqual(compared.comparison_checks[0].status, 'FAIL')
                self.has(compared, 'PUBLIC_MA3_DECISION_REJECT', 'FAIL')
                cached['overall'] = 'UNKNOWN'
                compared = component.validate_persisted_independent_replay(current_basis, resolver, cached, public_inputs=request)
                self.assertEqual(compared.comparison_checks[0].status, 'FAIL')

    def test_report_siblings_are_retained_with_missing_or_invalid_member(self):
        basis, req, resolver, _ = fixture()
        resolver.data[req['acceptance_ref']] = b'bad'
        resolver.data[req['required_report_refs'][0]] = None
        resolver.data[req['required_report_refs'][1]] = b'bad'
        result = self.run_entry(basis, req, resolver)
        observations = self.diagnostic(result)['observations']
        good = [o for o in observations if o['role'].startswith('report-') and o['status'] == 'PASS']
        self.assertEqual(len(good), 3)
        self.has(result, 'PUBLIC_SOURCE_UNAVAILABLE', 'UNKNOWN')
        self.assertEqual(result.overall, 'FAIL')
        self.assertEqual(Counter(resolver.calls), Counter([req['acceptance_ref'], basis.subject, *req['required_report_refs']]))

    def test_single_fetch_per_ref_and_observed_raw_bytes_bind_identity(self):
        basis, req, resolver, _ = fixture()
        first = self.run_entry(basis, req, resolver)
        self.assertEqual(set(Counter(resolver.calls).values()), {1})
        rr = req['required_report_refs'][0]
        raw = resolver.data[rr]; resolver.data[rr] = b' \n' + raw
        second = self.run_entry(basis, req, resolver)
        self.assertNotEqual(first.stable_identity, second.stable_identity)
        self.assertEqual(first.mandatory_set_identity, second.mandatory_set_identity)
        self.assertEqual(first.raw_results, second.raw_results)
        seen = next(o for o in self.diagnostic(second)['observations'] if o['role'] == 'report-0')
        self.assertEqual(seen['raw_sha256'], canonical.sha256_hex(b' \n' + raw))
        self.assertEqual(seen['raw_size'], len(raw) + 2)
        self.assertTrue({req['acceptance_ref'], basis.subject, *req['required_report_refs'], basis.root_ref, basis.rule_ref}.issubset(second.input_refs))
        # Reusing one full ref across roles must not obtain a second observation.
        resolver.calls.clear(); req['acceptance_ref'] = rr
        self.run_entry(basis, req, resolver)
        self.assertEqual(Counter(resolver.calls)[rr], 1)

    def test_persisted_replay_forwards_inputs_and_retains_fail_unknown(self):
        for bad in [False, True]:
            basis, req, resolver, _ = fixture()
            if bad: resolver.data[req['required_report_refs'][0]] = b'bad'
            fresh = self.run_entry(basis, req, resolver)
            report = component.stable_report(fresh)
            compared = component.validate_persisted_independent_replay(basis, resolver, report, public_inputs=req)
            self.assertEqual(compared.overall, 'FAIL' if bad else 'UNKNOWN')
            self.assertEqual(compared.stable_identity, fresh.stable_identity)
            self.assertEqual(compared.comparison_checks, ())
            report['overall'] = 'PASS'
            compared = component.validate_persisted_independent_replay(basis, resolver, report, public_inputs=req)
            self.assertEqual(compared.overall, 'FAIL' if bad else 'UNKNOWN')
            self.assertEqual(compared.comparison_checks[0].status, 'FAIL' if bad else 'UNKNOWN')
            report['protocol_state_change'] = 'ADOPT'
            compared = component.validate_persisted_independent_replay(basis, resolver, report, public_inputs=req)
            self.assertEqual(compared.overall, 'FAIL')

    def test_asserted_auth_pass_cannot_close_public_mandatory_authority(self):
        basis, req, resolver, _ = fixture()
        with patch.object(auth, 'verify_initial_acceptance_public', return_value=auth.InitialPublicAuthentication(status='PASS', reason_codes=('TEST_ASSERTION_ONLY',))):
            result = self.run_entry(basis, req, resolver)
        self.assertEqual(result.overall, 'UNKNOWN')
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.component_reports, {})


if __name__ == '__main__':
    unittest.main()
