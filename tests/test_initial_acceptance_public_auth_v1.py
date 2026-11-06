"""T08 no-formula public interface: missing independent G02 contract is UNKNOWN."""
import importlib
import importlib.util
import pytest


def api():
    assert importlib.util.find_spec('forecast_trust_core.initial_acceptance_public_auth_v1'),'T08 fail-closed interface missing'
    return importlib.import_module('forecast_trust_core.initial_acceptance_public_auth_v1')

@pytest.mark.parametrize('contract',[None,{}, {'status':'CLOSED'}, {'projection':'QualificationDecision'}, {'domain':'SC-A01'}, {'model_only':True}])
def test_unsupplied_independent_contract_never_constructs_message_or_calls_backend(contract):
    calls=[]
    def backend(*args,**kwargs):calls.append((args,kwargs));raise AssertionError('must not be called')
    result=api().verify_initial_acceptance_public(basis=None,acceptance=None,resolver=None,signing_contract=contract,backend=backend)
    assert result.status=='UNKNOWN' and 'BLOCKED_BY_G02' in result.reason_codes
    assert result.message_digest is None and result.message is None and not calls
    assert result.prospective_eligible is False


def test_blocked_interface_does_not_inspect_opaque_inputs():
    class Opaque:
        def __getattr__(self,name):raise AssertionError('blocked input inspected')
        def __getitem__(self,name):raise AssertionError('blocked input inspected')
        def resolve_exact(self,*args):raise AssertionError('blocked resolver called')
        def __call__(self,*args):raise AssertionError('blocked backend called')
    opaque=Opaque()
    result=api().verify_initial_acceptance_public(basis=opaque,acceptance=opaque,resolver=opaque,signing_contract=opaque,backend=opaque)
    assert result.status=='UNKNOWN' and result.message is None and result.message_digest is None
