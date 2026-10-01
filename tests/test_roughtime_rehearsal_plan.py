import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forecast_trust_core.canonical import canonical_json
from forecast_trust_core._roughtime_control import BUILD_COMMAND, VERIFIER_TAG_OBJECT_SHA, compute_source_bundle_sha256, make_initial_retry_state
from forecast_trust_core._roughtime_profile import VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG
from forecast_trust_core.roughtime_rehearsal import PROVIDER_ORDER, validate_authorization_record, validate_plan


ROOT = Path(__file__).resolve().parents[1]
PLAN_SCRIPT = ROOT / "scripts" / "genesis" / "prepare_roughtime_rehearsal.py"
AUTH_SCRIPT = ROOT / "scripts" / "genesis" / "prepare_roughtime_authorization.py"


def env():
    value = dict(os.environ)
    value["PYTHONPATH"] = str(ROOT / "src")
    return value


def write_control_artifacts(directory: Path) -> tuple[Path, Path]:
    """Create syntactically valid, non-production control inputs for CLI tests."""
    profile_path = directory / "verifier-build-profile.json"
    retry_path = directory / "retry-state.json"
    upstream = "11" * 32
    wrapper = "22" * 32
    profile = {
        "schema_version": "1.2",
        "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG,
        "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "go_version": "go1.27.1",
        "goos": "linux",
        "goarch": "amd64",
        "go_toolchain_tree_sha256": "77" * 32,
        "go_toolchain_distribution_source": "test-only",
        "go_toolchain_distribution_sha256": "88" * 32,
        "go_toolchain_carrier_sha256": "99" * 32,
        "cgo_enabled": False,
        "dependency_lock_sha256": "33" * 32,
        "wrapper_source_tree_sha256": wrapper,
        "upstream_source_tree_sha256": upstream,
        "verifier_source_bundle_sha256": compute_source_bundle_sha256(upstream, wrapper),
        "build_command": BUILD_COMMAND,
        "binary_sha256": "44" * 32,
        "fixture_report_sha256": "55" * 32,
    }
    profile["profile_sha256"] = hashlib.sha256(canonical_json(profile)).hexdigest()
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    retry_path.write_text(json.dumps(make_initial_retry_state()), encoding="utf-8")
    return profile_path, retry_path


class RoughtimeRehearsalPlanTests(unittest.TestCase):
    def test_offline_plan_freezes_deadline_and_has_no_network_authority(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            output = Path(tmpdir) / "plan.json"
            profile_path, retry_path = write_control_artifacts(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(PLAN_SCRIPT),
                    "--subject-sha256",
                    "38" * 32,
                    "--subject-label",
                    "SYNTHETIC_TEST_ONLY",
                    "--frozen-deadline-utc",
                    "2026-09-12T00:00:00Z",
                    "--verifier-build-profile", str(profile_path),
                    "--retry-state", str(retry_path),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                env=env(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(output.read_text(encoding="utf-8"))
        validate_plan(plan)
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            Draft202012Validator = None
        if Draft202012Validator is not None:
            schema = json.loads((ROOT / "schemas" / "roughtime_rehearsal_plan.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator(schema).validate(plan)
        self.assertIs(plan["network_authorized"], False)
        self.assertEqual(plan["frozen_deadline_utc"], "2026-09-12T00:00:00Z")
        self.assertEqual([p["provider_id"] for p in plan["providers"]], list(PROVIDER_ORDER))
        self.assertEqual(len({p["client_random_hex"] for p in plan["providers"]}), 3)
        self.assertEqual(plan["packet_profile"], "STANDARD_1024_BODY")
        self.assertEqual(plan["transport_profile"], "UDP_ONLY")

    def test_authorization_tool_requires_explicit_flag_and_binds_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            plan_path = tmp / "plan.json"
            auth_path = tmp / "auth.json"
            profile_path, retry_path = write_control_artifacts(tmp)
            make_plan = subprocess.run(
                [
                    sys.executable, str(PLAN_SCRIPT),
                    "--subject-sha256", "38" * 32,
                    "--subject-label", "SYNTHETIC_TEST_ONLY",
                    "--frozen-deadline-utc", "2026-09-12T00:00:00Z",
                    "--verifier-build-profile", str(profile_path),
                    "--retry-state", str(retry_path),
                    "--output", str(plan_path),
                ],
                cwd=ROOT, env=env(), capture_output=True, text=True, check=False,
            )
            self.assertEqual(make_plan.returncode, 0, make_plan.stderr)
            denied = subprocess.run(
                [
                    sys.executable, str(AUTH_SCRIPT),
                    "--plan", str(plan_path),
                    "--verifier-build-profile", str(profile_path),
                    "--retry-state", str(retry_path),
                    "--authorized-by", "test:operator",
                    "--authorized-at-utc", "2026-09-11T23:00:00Z",
                    "--output", str(auth_path),
                ],
                cwd=ROOT, env=env(), capture_output=True, text=True, check=False,
            )
            self.assertEqual(denied.returncode, 2)
            allowed = subprocess.run(
                [
                    sys.executable, str(AUTH_SCRIPT),
                    "--plan", str(plan_path),
                    "--verifier-build-profile", str(profile_path),
                    "--retry-state", str(retry_path),
                    "--authorized-by", "test:operator",
                    "--authorized-at-utc", "2026-09-11T23:00:00Z",
                    "--explicit-operator-authorization",
                    "--output", str(auth_path),
                ],
                cwd=ROOT, env=env(), capture_output=True, text=True, check=False,
            )
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            auth = json.loads(auth_path.read_text(encoding="utf-8"))
        validate_authorization_record(auth, plan)
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            Draft202012Validator = None
        if Draft202012Validator is not None:
            schema = json.loads((ROOT / "schemas" / "roughtime_rehearsal_authorization.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator(schema).validate(auth)
        self.assertIs(auth["network_authorized"], True)
        self.assertEqual(auth["rehearsal_plan_sha256"], plan["plan_sha256"])

    def test_all_roughtime_schemas_are_valid_json_schema(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("jsonschema is not a project runtime dependency")
        for name in (
            "roughtime_rehearsal_plan.schema.json",
            "roughtime_rehearsal_authorization.schema.json",
            "roughtime_receipt.schema.json",
            "roughtime_rehearsal_report.schema.json",
        ):
            schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)


if __name__ == "__main__":
    unittest.main()
