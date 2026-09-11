import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "genesis" / "ots_rehearsal.sh"


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
            env["PATH"] = f"{bindir}:{env['PATH']}"
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
