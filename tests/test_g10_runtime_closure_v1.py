"""G10 inventory must notice changes in package initialization dependencies.

These exercise the real static observer on retained source bytes. No signing,
network, runtime-pin rewriting, public authority or protocol action occurs.
"""
from hashlib import sha256
from pathlib import Path

import pytest

from forecast_trust_core import integration_model_v1 as integration


@pytest.mark.parametrize("changed", ["policies", "governance", "policy_helper"])
def test_initializer_only_dependency_changes_observed_runtime(tmp_path, monkeypatch, changed):
    package = tmp_path / "src" / "forecast_trust_core"
    package.mkdir(parents=True)
    (package / "entry.py").write_text("VALUE = 1\n")
    (package / "__init__.py").write_text("from .policies import *\nfrom .governance import *\n")
    (package / "policies.py").write_text("from .policy_helper import VALUE\n")
    (package / "governance.py").write_text("VALUE = 1\n")
    (package / "policy_helper.py").write_text("VALUE = 1\n")
    cli = tmp_path / "scripts" / "development" / "replay_independent_genesis.py"
    cli.parent.mkdir(parents=True)
    cli.write_text("# retained CLI\n")
    monkeypatch.setattr(integration, "ROOT", tmp_path)
    monkeypatch.setattr(integration, "ROOT_MODULES", ("entry",))

    before = integration.observe_model_runtime()
    member = package / (changed + ".py")
    member.write_bytes(member.read_bytes() + b"# changed retained runtime bytes\n")
    after = integration.observe_model_runtime()

    assert before != after, "Initializer-only source substitution escaped runtime identity"
    assert after["modules"][changed] == sha256(member.read_bytes()).hexdigest()


def test_installed_package_initialization_dependencies_are_in_runtime_inventory():
    observed = integration.runtime_modules()
    package = Path(integration.__file__).parent
    for name in ("policies", "governance"):
        assert name in observed, "Package initialization dependency missing: " + name
        assert observed[name] == sha256((package / (name + ".py")).read_bytes()).hexdigest()
