"""Fail-closed boundary for legacy full claims without independent initial basis.

Narrow temporal/Bitcoin computations remain useful facts. These APIs cannot
establish full initial acceptance or obtain the unresolved real signing contract.
"""
from .core import Check,Validation,Result,aggregate

def require_complete_initial_replay(validation:Validation)->Validation:
    checks=tuple(validation.checks)
    if validation.result==Result.INVALID and not any(c.status=='FAIL' for c in checks):
        checks+=(Check('LOCAL_INITIAL_VALIDATION','FAIL','LOCAL_INITIAL_VALIDATION_INVALID'),)
    gate=Check('G10_FULL_INDEPENDENT_REPLAY','UNKNOWN','INDEPENDENT_INITIAL_BASIS_NOT_ESTABLISHED')
    if gate not in checks:checks+=(gate,)
    return aggregate(checks)
