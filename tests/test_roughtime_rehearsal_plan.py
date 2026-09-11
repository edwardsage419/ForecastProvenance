import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forecast_trust_core.roughtime_rehearsal import PROVIDER_ORDER, validate_authorization_record, validate_plan


ROOT = Path(__file__).resolve().parents[1]
PLAN_SCRIPT = ROOT / "scripts" / "genesis" / "prepare_roughtime_rehearsal.py"
AUTH_SCRIPT = ROOT / "scripts" / "genesis" / "prepare_roughtime_authorization.py"


def env():
    value = dict(os.environ)
    value["PYTHONPATH"] = str(ROOT / "src")
    return value


class RoughtimeRehearsalPlanTests(unittest.TestCase):
    def test_offline_plan_freezes_deadline_and_has_no_network_authority(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "plan.json"
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
                    "--verifier-build-profile-sha256",
                    "c" * 64,
                    "--retry-state-snapshot-sha256",
                    "d" * 64,
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
            make_plan = subprocess.run(
                [
                    sys.executable, str(PLAN_SCRIPT),
                    "--subject-sha256", "38" * 32,
                    "--subject-label", "SYNTHETIC_TEST_ONLY",
                    "--frozen-deadline-utc", "2026-09-12T00:00:00Z",
                    "--verifier-build-profile-sha256", "c" * 64,
                    "--retry-state-snapshot-sha256", "d" * 64,
                    "--output", str(plan_path),
                ],
                cwd=ROOT, env=env(), capture_output=True, text=True, check=False,
            )
            self.assertEqual(make_plan.returncode, 0, make_plan.stderr)
            denied = subprocess.run(
                [
                    sys.executable, str(AUTH_SCRIPT),
                    "--plan", str(plan_path),
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
