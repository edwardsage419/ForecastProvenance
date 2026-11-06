import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "genesis" / "ots_rehearsal.sh"


@unittest.skipIf(os.name == "nt", "POSIX shell fixture requires a POSIX execution environment")
class OTSRehearsalScriptTests(unittest.TestCase):
    def _write_fake_ots(self, bindir: Path) -> None:
        fake = bindir / "ots"
        fake.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --version ]]; then echo 'fake-ots 1.0'; exit 0; fi
cmd=${1:-}
shift || true
case "$cmd" in
  upgrade)
    proof="$1"
    if [[ ${FAKE_OTS_MODE:-success} == fail ]]; then
      printf 'CORRUPTED-BY-FAILED-UPGRADE' > "$proof"
      exit 9
    fi
    printf 'UPGRADED-PROOF' > "$proof"
    ;;
  info)
    echo 'fake-info'
    ;;
  stamp)
    subject="$1"
    printf 'STAMPED-PROOF' > "$subject.ots"
    ;;
  --bitcoin-node)
    shift
    [[ ${1:-} == verify ]]
    ;;
  *)
    echo "unexpected fake ots invocation: $cmd $*" >&2
    exit 8
    ;;
esac
""",
            encoding="utf-8",
        )
        fake.chmod(0o755)

    def _seed_retained_material(self, outdir: Path, subject: bytes, proof: bytes) -> None:
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "subject.bin").write_bytes(subject)
        (outdir / "subject.bin.ots").write_bytes(proof)
        digest = hashlib.sha256(subject).hexdigest()
        (outdir / "subject.sha256").write_text(f"{digest}  subject.bin\n", encoding="utf-8")

    def test_verify_disables_default_calendar_and_cache_without_failure_fallback(self):
        # Removing either option re-enables an implicit upstream input source.
        for verify_exit in (0, 17):
            with self.subTest(verify_exit=verify_exit), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                bindir = root / "bin"
                bindir.mkdir()
                fake = bindir / "ots"
                fake.write_text(
                    f"#!{sys.executable}\n" + """import json, os, sys
args = sys.argv[1:]
with open(os.environ['FP_TEST_OTS_ARGV'], 'a', encoding='utf-8') as log:
    log.write(json.dumps(args) + '\\n')
if args == ['--version']:
    print('fake-ots-test-only')
elif args and args[0] == 'info':
    print('fake-info-test-only')
elif 'verify' in args:
    sys.exit(int(os.environ['FP_TEST_VERIFY_EXIT']))
else:
    sys.exit(8)
""",
                    encoding="utf-8",
                )
                fake.chmod(0o755)
                outdir = root / "ots"
                original = b"NOT_AN_OTS_PROOF_TEST_ONLY"
                self._seed_retained_material(outdir, b"PUBLIC_TEST_ONLY", original)
                source = root / "unused.bin"
                source.write_bytes(b"UNUSED_TEST_ONLY")
                argv_file = root / "argv.jsonl"
                node = "http://127.0.0.1:18443/"
                env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}",
                           OTS_BITCOIN_NODE=node, FP_TEST_OTS_ARGV=str(argv_file),
                           FP_TEST_VERIFY_EXIT=str(verify_exit))
                result = subprocess.run(
                    ["bash", str(SCRIPT), "verify", str(source), str(outdir)],
                    cwd=ROOT, env=env, capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, verify_exit, result.stderr)
                calls = [json.loads(line) for line in argv_file.read_text().splitlines()]
                verify_calls = [args for args in calls if "verify" in args]
                self.assertEqual(len(verify_calls), 1)
                args = verify_calls[0]
                prefix = args[:args.index("verify")]
                self.assertIn("--no-default-whitelist", prefix)
                self.assertIn("--no-cache", prefix)
                self.assertNotIn("--whitelist", prefix)
                self.assertNotIn("--no-bitcoin", prefix)
                self.assertEqual(prefix[prefix.index("--bitcoin-node") + 1], node)
                events = list((outdir / "events").glob("*-verify"))
                self.assertEqual(len(events), 1)
                self.assertEqual(args[args.index("verify") + 1:], [str(events[0] / "subject.bin.ots")])
                self.assertEqual((events[0] / "subject.bin.ots").read_bytes(), original)
                self.assertEqual((outdir / "subject.bin.ots").read_bytes(), original)
                state = (events[0] / "state.txt").read_text()
                self.assertIn(f"exit_status={verify_exit}\n", state)
                self.assertIn("classification=NON_FORECAST_REHEARSAL\n", state)
                self.assertIn("prospective_eligible=false\n", state)
                if verify_exit:
                    self.assertFalse(any(args and args[0] == "info" for args in calls))

    def test_failed_upgrade_cannot_corrupt_last_good_canonical_proof(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bindir = root / "bin"
            bindir.mkdir()
            self._write_fake_ots(bindir)
            outdir = root / "ots"
            source = root / "unused-source.bin"
            source.write_bytes(b"unused")
            original = b"LAST-GOOD-PROOF"
            self._seed_retained_material(outdir, b"subject", original)

            env = dict(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
            env["FAKE_OTS_MODE"] = "fail"
            failed = subprocess.run(
                ["bash", str(SCRIPT), "upgrade", str(source), str(outdir)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual((outdir / "subject.bin.ots").read_bytes(), original)
            failed_events = sorted((outdir / "events").glob("*-upgrade"))
            self.assertEqual(len(failed_events), 1)
            self.assertEqual((failed_events[0] / "proof_before.ots").read_bytes(), original)
            self.assertEqual((failed_events[0] / "subject.bin.ots").read_bytes(), b"CORRUPTED-BY-FAILED-UPGRADE")

            env["FAKE_OTS_MODE"] = "success"
            succeeded = subprocess.run(
                ["bash", str(SCRIPT), "upgrade", str(source), str(outdir)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(succeeded.returncode, 0, succeeded.stderr)
            self.assertEqual((outdir / "subject.bin.ots").read_bytes(), b"UPGRADED-PROOF")
            events = sorted((outdir / "events").glob("*-upgrade"))
            self.assertEqual(len(events), 2)
            self.assertEqual((events[1] / "proof_before.ots").read_bytes(), original)
            self.assertEqual((events[1] / "proof_after.ots").read_bytes(), b"UPGRADED-PROOF")


if __name__ == "__main__":
    unittest.main()
