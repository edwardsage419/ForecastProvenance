from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from forecast_trust_core._ed25519_verifier import PinnedEd25519Verifier


def _hx(value: str) -> bytes:
    return bytes.fromhex(value)


@pytest.fixture(scope="session")
def ed25519_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    go = shutil.which("go")
    if go is None:
        pytest.skip("Go toolchain is unavailable")
    repo_root = Path(__file__).resolve().parents[1]
    source_dir = repo_root / "scripts" / "genesis" / "ed25519_verify"
    output = tmp_path_factory.mktemp("ed25519_verify") / ("ed25519_verify.exe" if os.name == "nt" else "ed25519_verify")
    env = os.environ.copy()
    env.update({
        "GOTOOLCHAIN": "local",
        "CGO_ENABLED": "0",
        "GOENV": "off",
        "GOWORK": "off",
        "GOPROXY": "off",
        "GOSUMDB": "off",
    })
    subprocess.run([go, "test", "-count=1", "./..."], cwd=source_dir, env=env, check=True, capture_output=True)
    subprocess.run([go, "build", "-trimpath", "-o", str(output), "."], cwd=source_dir, env=env, check=True, capture_output=True)
    return output


def _verifier(binary: Path) -> PinnedEd25519Verifier:
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    return PinnedEd25519Verifier(binary, digest)


def test_rfc8032_vector_1_through_pinned_adapter(ed25519_binary: Path) -> None:
    verifier = _verifier(ed25519_binary)
    public_key = _hx("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    signature = _hx("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")
    assert verifier(public_key, b"", signature) is True


def test_mutated_signature_returns_false(ed25519_binary: Path) -> None:
    verifier = _verifier(ed25519_binary)
    public_key = _hx("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    signature = bytearray(_hx("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"))
    signature[0] ^= 1
    assert verifier(public_key, b"", bytes(signature)) is False


def test_binary_hash_substitution_fails_closed(ed25519_binary: Path) -> None:
    verifier = PinnedEd25519Verifier(ed25519_binary, "0" * 64)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        verifier(b"x" * 32, b"", b"y" * 64)


def test_invalid_input_lengths_fail_before_process(ed25519_binary: Path) -> None:
    verifier = _verifier(ed25519_binary)
    with pytest.raises(ValueError, match="public_key"):
        verifier(b"x" * 31, b"", b"y" * 64)
    with pytest.raises(ValueError, match="signature"):
        verifier(b"x" * 32, b"", b"y" * 63)
    with pytest.raises(ValueError, match="size limit"):
        verifier(b"x" * 32, b"z" * (1024 * 1024 + 1), b"y" * 64)
