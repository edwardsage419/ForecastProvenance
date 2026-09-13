from __future__ import annotations

import hashlib
import json
import socket
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from forecast_trust_core.canonical import canonical_json, seal_object
from forecast_trust_core._roughtime_control import (
    BUILD_COMMAND, VERIFIER_TAG_OBJECT_SHA, compute_source_bundle_sha256,
    make_initial_retry_state, record_failure, validate_report_control_binding, validate_retry_state,
)
from forecast_trust_core._roughtime_execution import (
    PreparedDestination, QualifiedVerifierBackend, RealUDPTransport, TransportOutcome, VerifyResult,
    execute_rehearsal,
)
from forecast_trust_core._roughtime_profile import (
    PACKET_PROFILE, PROVIDERS, PROVIDER_ORDER, TRANSPORT_PROFILE,
    VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG,
)
from forecast_trust_core._roughtime_support import derive_nonce_v2_hex
from forecast_trust_core._roughtime_report import validate_rehearsal_report


@pytest.fixture(autouse=True)
def forbid_real_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("test attempted real DNS or socket use")
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)


def _rehash(value: dict, field: str) -> dict:
    core = {key: item for key, item in value.items() if key != field}
    value[field] = hashlib.sha256(canonical_json(core)).hexdigest()
    return value


def profile() -> dict:
    upstream, wrapper = "11" * 32, "22" * 32
    return _rehash({
        "schema_version": "1.2", "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG, "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA, "upstream_tag_signature_verified": True,
        "go_version": "go1.27.1", "goos": "linux", "goarch": "amd64",
        "go_toolchain_tree_sha256": "77" * 32,
        "go_toolchain_distribution_source": "test-only offline fixture",
        "go_toolchain_distribution_sha256": "88" * 32, "go_toolchain_carrier_sha256": "99" * 32,
        "cgo_enabled": False, "dependency_lock_sha256": "33" * 32,
        "wrapper_source_tree_sha256": wrapper, "upstream_source_tree_sha256": upstream,
        "verifier_source_bundle_sha256": compute_source_bundle_sha256(upstream, wrapper),
        "build_command": BUILD_COMMAND, "binary_sha256": "44" * 32,
        "fixture_report_sha256": "55" * 32,
    }, "profile_sha256")


def plan_and_auth(retry=None):
    retry = retry or make_initial_retry_state()
    build = profile()
    subject = "38" * 32
    providers = []
    for number, provider in enumerate(PROVIDERS, 1):
        random_hex = (bytes([number]) * 32).hex()
        providers.append({
            **provider.__dict__, "packet_profile": PACKET_PROFILE,
            "transport_profile": TRANSPORT_PROFILE, "client_random_hex": random_hex,
            "nonce_profile": "FPP_ROUGHTIME_NONCE_V2",
            "nonce_hex": derive_nonce_v2_hex(subject, random_hex), "maximum_attempts": 2,
            "timeout_per_attempt_seconds": 2, "retry_backoff_initial_seconds": 1,
            "retry_backoff_factor": "1.5", "retry_backoff_max_seconds": 86400,
            "retry_request_rule": "same_exact_request_bytes", "network_authorized": False,
        })
    plan = _rehash({
        "schema_version": "1.1", "classification": "NON_FORECAST_REHEARSAL",
        "prospective_eligible": False, "network_authorized": False,
        "subject_label": "SYNTHETIC_TEST_ONLY", "subject_sha256": subject,
        "frozen_deadline_utc": "2026-09-14T00:00:00Z", "nonce_profile": "FPP_ROUGHTIME_NONCE_V2",
        "packet_profile": PACKET_PROFILE, "transport_profile": TRANSPORT_PROFILE,
        "provider_attempt_rule": "evaluate_all_three_frozen_providers_in_frozen_order_attempt_each_when_retry_eligible",
        "quorum_threshold": 2, "retry_state_rule": "persist_per_root_until_properly_signed_response",
        "backoff_block_rule": "backoff_active_counts_nonqualifying_no_network_attempt",
        "verifier_repository": VERIFIER_REPOSITORY, "verifier_tag": VERIFIER_TAG,
        "verifier_commit": VERIFIER_COMMIT, "verifier_build_profile_sha256": build["profile_sha256"],
        "retry_state_snapshot_sha256": retry["state_sha256"], "providers": providers,
    }, "plan_sha256")
    auth = _rehash({
        "schema_version": "1.0", "classification": "NON_FORECAST_REHEARSAL",
        "prospective_eligible": False, "network_authorized": True,
        "rehearsal_plan_sha256": plan["plan_sha256"], "subject_sha256": subject,
        "frozen_deadline_utc": plan["frozen_deadline_utc"], "provider_order": list(PROVIDER_ORDER),
        "verifier_commit": VERIFIER_COMMIT, "verifier_build_profile_sha256": build["profile_sha256"],
        "retry_state_snapshot_sha256": retry["state_sha256"], "authorized_by": "test:operator",
        "authorized_at_utc": "2026-09-12T00:00:00Z",
        "authorization_scope": "exact_plan_only_no_prospective_use",
    }, "authorization_sha256")
    return plan, auth, build, retry


class Clock:
    def __init__(self):
        self.value = datetime(2026, 9, 13, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += timedelta(seconds=seconds)


class FakeVerifier:
    binary_sha256 = "44" * 32

    def __init__(self, codes=None):
        self.codes = codes or {}
        self.requests = {}

    def build_request(self, provider):
        raw = bytes([PROVIDER_ORDER.index(provider["provider_id"]) + 1]) * 1036
        self.requests[provider["provider_id"]] = raw
        return raw, {"action": "build-request", "provider_id": provider["provider_id"],
                     "request_sha256": hashlib.sha256(raw).hexdigest()}

    def verify_response(self, provider, request_bytes, response_bytes):
        code = self.codes.get(provider["provider_id"])
        transcript = {"action": "verify-response", "provider_id": provider["provider_id"],
                      "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
                      "response_sha256": hashlib.sha256(response_bytes).hexdigest()}
        if code:
            if code == "RADIUS_INVALID":
                return VerifyResult(True, None, "", transcript, "2026-09-13T00:00:00.1Z", 2**53)
            if code == "UPPER_BOUND_AFTER_DEADLINE":
                return VerifyResult(True, None, "", transcript, "2026-09-13T23:59:59.5Z", 1_000_000_000)
            return VerifyResult(False, code, code, {**transcript, "failure_code": code})
        return VerifyResult(True, None, "", transcript, "2026-09-13T00:00:00.123456789Z", 1_500_000_000)


class FakeTransport:
    def __init__(self, script=None):
        self.script = list(script or ["success"] * 3)
        self.calls = []
        self.prepares = []

    def prepare_destination(self, host, port):
        self.prepares.append((host, port))
        return PreparedDestination(socket.AF_INET, f"192.0.2.{len(self.prepares)}", port)

    def send_and_receive(self, destination, request_bytes, timeout_seconds):
        self.calls.append((destination, request_bytes, timeout_seconds))
        action = self.script.pop(0)
        common = dict(destination=destination, sent=True, send_utc="2026-09-13T00:00:00Z")
        if action == "timeout":
            return TransportOutcome("TIMEOUT", detail="timeout", **common)
        if action == "error":
            return TransportOutcome("ERROR", detail="socket error", **common)
        if action == "empty":
            return TransportOutcome("RESPONSE", response_bytes=b"", receive_utc="2026-09-13T00:00:01Z",
                                    source_address=destination.address, source_port=destination.port, **common)
        if action == "source":
            return TransportOutcome("SOURCE_MISMATCH", response_bytes=b"wrong source", receive_utc="2026-09-13T00:00:01Z",
                                    source_address="203.0.113.9", source_port=9999, detail="source mismatch", **common)
        return TransportOutcome("RESPONSE", response_bytes=(b"response:" + bytes([len(self.calls)])),
                                receive_utc="2026-09-13T00:00:01Z", source_address=destination.address,
                                source_port=destination.port, **common)


class OutputVerifier(QualifiedVerifierBackend):
    def __init__(self, output):
        self.output = output
        self.binary_sha256 = "44" * 32

    def _run(self, action, payload):
        return self.output


def verifier_success_output(provider, request, response):
    return {
        "schema_version": "1.0", "action": "verify-response", "provider_id": provider["provider_id"],
        "verified": True, "wire_version": provider["wire_version_hex"],
        "wire_profile": provider["wire_profile"], "require_type": provider["require_type"],
        "require_srv": provider["require_srv"], "nonce_hex": provider["nonce_hex"],
        "request_sha256": hashlib.sha256(request).hexdigest(),
        "response_sha256": hashlib.sha256(response).hexdigest(),
        "midpoint_utc": "2026-09-13T00:00:00.123456789Z", "radius_nanoseconds": 1_500_000_000,
    }


def reseal_report(report, *, schema_version=None):
    payload = deepcopy(report)
    for key in ("object_type", "object_id", "payload_sha256", "content_sha256"):
        payload.pop(key)
    if schema_version is not None:
        payload["schema_version"] = schema_version
    return seal_object(payload, object_type="RoughtimeRehearsalReport", stable_context="test-version")


def run(tmp_path, *, plan=None, auth=None, build=None, retry=None, transport=None, verifier=None, fault=None, clock=None):
    if plan is None:
        plan, auth, build, retry = plan_and_auth(retry)
    clock = clock or Clock()
    return execute_rehearsal(
        plan=plan, authorization=auth, build_profile=build, retry_state_before=retry,
        evidence_root=tmp_path / "evidence", verifier=verifier or FakeVerifier(),
        transport=transport or FakeTransport(), now=clock.now, sleeper=clock.sleep, fault_hook=fault,
    )


def test_success_evaluates_all_providers_and_materializes_valid_report(tmp_path):
    transport = FakeTransport()
    report, state, event = run(tmp_path, transport=transport)
    assert report["final_rehearsal_status"] == "REHEARSAL_VERIFIED"
    assert report["qualifying_provider_count"] == 3
    assert [p[0] for p in transport.prepares] == [p.host for p in PROVIDERS]
    assert len(transport.calls) == 3
    assert (event / "report.json").is_file() and (event / "execution-transcript.json").is_file()
    assert validate_retry_state(state) == state["state_sha256"]


def test_success_invokes_final_report_control_binding(tmp_path, monkeypatch):
    import forecast_trust_core._roughtime_execution as execution
    original = execution.validate_report_control_binding
    calls = []

    def observe(*args):
        calls.append(args)
        return original(*args)

    monkeypatch.setattr(execution, "validate_report_control_binding", observe)
    report, state, _ = run(tmp_path)
    assert len(calls) == 1
    assert calls[0][0] == report and calls[0][5] == state


def test_final_report_control_binding_failure_prevents_report_publication(tmp_path, monkeypatch):
    import forecast_trust_core._roughtime_execution as execution

    def reject(*args):
        raise ValueError("synthetic final control mismatch")

    monkeypatch.setattr(execution, "validate_report_control_binding", reject)
    plan, auth, build, retry = plan_and_auth()
    with pytest.raises(ValueError, match="synthetic final control mismatch"):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry)
    event = tmp_path / "evidence" / "events" / auth["authorization_sha256"]
    assert not (event / "report.json").exists()


def test_report_control_binding_accepts_complete_valid_binding_without_transport():
    plan, auth, build, before = plan_and_auth()
    report = {
        "verifier_build_profile_sha256": build["profile_sha256"],
        "retry_state_before_sha256": before["state_sha256"],
        "retry_state_after_sha256": before["state_sha256"],
        "provider_results": [],
    }
    transport = FakeTransport()
    validate_report_control_binding(report, plan, auth, build, before, before)
    assert transport.prepares == [] and transport.calls == []


@pytest.mark.parametrize("target", ["plan", "authorization", "profile", "retry_before", "retry_after", "report"])
def test_report_control_binding_mismatches_fail_without_transport(target):
    plan, auth, build, before = plan_and_auth()
    after = before
    report = {
        "verifier_build_profile_sha256": build["profile_sha256"],
        "retry_state_before_sha256": before["state_sha256"],
        "retry_state_after_sha256": after["state_sha256"],
        "provider_results": [],
    }
    if target == "plan":
        plan = {**plan, "verifier_build_profile_sha256": "aa" * 32}
    elif target == "authorization":
        auth = {**auth, "verifier_build_profile_sha256": "aa" * 32}
    elif target == "profile":
        build = {**build, "profile_sha256": "aa" * 32}
    elif target == "retry_before":
        before = {**before, "state_sha256": "aa" * 32}
    elif target == "retry_after":
        after = {**after, "state_sha256": "aa" * 32}
    else:
        report["retry_state_after_sha256"] = "aa" * 32
    transport = FakeTransport()
    with pytest.raises(ValueError):
        validate_report_control_binding(report, plan, auth, build, before, after)
    assert transport.prepares == [] and transport.calls == []


def test_qualified_verifier_accepts_only_exact_success_output():
    provider = plan_and_auth()[0]["providers"][0]
    request, response = b"request", b"response"
    output = verifier_success_output(provider, request, response)
    result = OutputVerifier(output).verify_response(provider, request, response)
    assert result.verified is True and result.failure_code is None


@pytest.mark.parametrize("mutation", ["one_extra", "multiple_extra", "missing", "wrong_type", "duplicate_semantic"])
def test_qualified_verifier_rejects_non_exact_success_output(mutation):
    provider = plan_and_auth()[0]["providers"][0]
    request, response = b"request", b"response"
    output = verifier_success_output(provider, request, response)
    if mutation == "one_extra":
        output["unexpected"] = True
    elif mutation == "multiple_extra":
        output.update({"unexpected_one": 1, "unexpected_two": 2})
    elif mutation == "missing":
        output.pop("midpoint_utc")
    elif mutation == "wrong_type":
        output["verified"] = 1
    else:
        output["radius_seconds"] = 2
    result = OutputVerifier(output).verify_response(provider, request, response)
    assert result.verified is False and result.failure_code == "VERIFIER_ERROR"


def test_srv_verifier_failure_reuses_root_key_mismatch_code():
    class ErrorVerifier(OutputVerifier):
        def _run(self, action, payload):
            raise ValueError("SRV does not match frozen root key")

    provider = plan_and_auth()[0]["providers"][0]
    result = ErrorVerifier({}).verify_response(provider, b"request", b"response")
    assert result.verified is False and result.failure_code == "ROOT_KEY_MISMATCH"


@pytest.mark.parametrize("field,value", [
    ("network_authorized", False), ("rehearsal_plan_sha256", "00" * 32),
    ("subject_sha256", "00" * 32), ("verifier_build_profile_sha256", "00" * 32),
    ("retry_state_snapshot_sha256", "00" * 32),
])
def test_authorization_mutations_fail_before_transport(tmp_path, field, value):
    plan, auth, build, retry = plan_and_auth()
    auth[field] = value
    _rehash(auth, "authorization_sha256")
    transport = FakeTransport()
    with pytest.raises(ValueError):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=transport)
    assert transport.calls == [] and transport.prepares == []


def test_missing_authorization_and_expired_deadline_fail_without_send(tmp_path):
    plan, auth, build, retry = plan_and_auth()
    transport = FakeTransport()
    with pytest.raises((TypeError, ValueError)):
        run(tmp_path, plan=plan, auth=None, build=build, retry=retry, transport=transport)
    plan["frozen_deadline_utc"] = "2026-09-12T00:00:00Z"
    _rehash(plan, "plan_sha256")
    auth["rehearsal_plan_sha256"] = plan["plan_sha256"]
    auth["frozen_deadline_utc"] = plan["frozen_deadline_utc"]
    auth["authorized_at_utc"] = "2026-09-11T00:00:00Z"
    _rehash(auth, "authorization_sha256")
    with pytest.raises(ValueError, match="expired"):
        run(tmp_path / "expired", plan=plan, auth=auth, build=build, retry=retry, transport=transport)
    assert transport.calls == []


@pytest.mark.parametrize("field,value", [
    ("provider_id", "unknown"), ("host", "evil.example"), ("port", 9), ("transport", "tcp"),
    ("root_public_key_base64", "AA=="), ("wire_profile", "fallback"),
    ("wire_version_hex", "0x00000000"), ("offered_version_hex", "0x00000000"),
    ("packet_profile", "fallback"), ("transport_profile", "TCP"), ("maximum_attempts", 3),
    ("require_type", False), ("require_srv", False),
])
def test_provider_profile_drift_fails_before_send(tmp_path, field, value):
    plan, auth, build, retry = plan_and_auth()
    plan["providers"][0][field] = value
    _rehash(plan, "plan_sha256")
    auth["rehearsal_plan_sha256"] = plan["plan_sha256"]
    _rehash(auth, "authorization_sha256")
    transport = FakeTransport()
    with pytest.raises(ValueError):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=transport)
    assert transport.calls == [] and transport.prepares == []


@pytest.mark.parametrize("actions,final_code", [
    (["timeout", "success", "success", "success"], None),
    (["error", "error", "success", "success"], "TRANSPORT_ERROR"),
    (["empty", "empty", "success", "success"], "MALFORMED_RESPONSE"),
    (["source", "source", "success", "success"], "RESPONSE_SOURCE_MISMATCH"),
])
def test_transport_failures_retry_with_identical_request(tmp_path, actions, final_code):
    transport = FakeTransport(actions)
    report, _, event = run(tmp_path, transport=transport)
    first = report["provider_results"][0]
    assert len(first["attempts"]) == 2
    assert first["attempts"][0]["request_base64"] == first["attempts"][1]["request_base64"]
    assert first["attempts"][0]["request_sha256"] == first["attempts"][1]["request_sha256"]
    if final_code:
        assert first["final_failure_code"] == final_code
    if actions[0] in {"empty", "source"}:
        assert (event / "providers" / PROVIDER_ORDER[0] / "attempt-1" / "response.bin").exists()


def test_dns_failure_is_distinct_and_never_calls_send(tmp_path):
    class DNSFailure(FakeTransport):
        def prepare_destination(self, host, port):
            self.prepares.append((host, port))
            raise OSError("synthetic DNS failure")
    transport = DNSFailure()
    report, _, _ = run(tmp_path, transport=transport)
    assert report["provider_results"][0]["final_failure_code"] == "DNS_FAILURE"
    assert transport.calls == []


@pytest.mark.parametrize("code", [
    "SIGNATURE_INVALID", "NONCE_MISMATCH", "MERKLE_PROOF_INVALID", "WIRE_VERSION_MISMATCH",
    "ROOT_KEY_MISMATCH", "DELEGATION_INVALID", "MALFORMED_RESPONSE", "TYPE_MISMATCH",
])
def test_verifier_failures_are_retained_and_retried(tmp_path, code):
    verifier = FakeVerifier({PROVIDER_ORDER[0]: code})
    transport = FakeTransport(["success", "success", "success", "success"])
    report, _, event = run(tmp_path, verifier=verifier, transport=transport)
    result = report["provider_results"][0]
    assert result["final_failure_code"] == code and len(result["attempts"]) == 2
    assert (event / "providers" / PROVIDER_ORDER[0] / "attempt-1" / "response.bin").is_file()


@pytest.mark.parametrize("code", ["RADIUS_INVALID", "UPPER_BOUND_AFTER_DEADLINE"])
def test_verified_nonqualifying_is_terminal_and_resets_backoff(tmp_path, code):
    verifier = FakeVerifier({PROVIDER_ORDER[0]: code})
    transport = FakeTransport()
    report, state, _ = run(tmp_path, verifier=verifier, transport=transport)
    result = report["provider_results"][0]
    assert len(result["attempts"]) == 1
    assert result["attempts"][0]["outcome"] == "VERIFIED_NONQUALIFYING_RESPONSE"
    assert result["final_failure_code"] == code
    assert state["root_states"][0]["consecutive_failures"] == 0 or any(
        item["consecutive_failures"] == 0 for item in state["root_states"]
    )


@pytest.mark.parametrize("successes,status", [(3, "REHEARSAL_VERIFIED"), (2, "REHEARSAL_VERIFIED"),
                                                (1, "REHEARSAL_FAILED"), (0, "REHEARSAL_FAILED")])
def test_quorum_matrix(tmp_path, successes, status):
    codes = {provider: "SIGNATURE_INVALID" for provider in PROVIDER_ORDER[successes:]}
    verifier = FakeVerifier(codes)
    failed = 3 - successes
    transport = FakeTransport(["success"] * (successes + failed * 2))
    report, _, _ = run(tmp_path, verifier=verifier, transport=transport)
    assert report["qualifying_provider_count"] == successes
    assert report["final_rehearsal_status"] == status


def test_backoff_active_skips_only_that_provider_and_sends_zero_for_it(tmp_path):
    retry = make_initial_retry_state()
    import base64
    root = hashlib.sha256(base64.b64decode(PROVIDERS[0].root_public_key_base64)).hexdigest()
    retry = record_failure(retry, root, int(Clock().now().timestamp() * 1000))
    plan, auth, build, _ = plan_and_auth(retry)
    transport = FakeTransport()
    report, _, _ = run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=transport)
    assert report["provider_results"][0]["final_failure_code"] == "BACKOFF_ACTIVE"
    assert len(transport.calls) == 2


def test_same_authorization_cannot_execute_twice(tmp_path):
    plan, auth, build, retry = plan_and_auth()
    run(tmp_path, plan=plan, auth=auth, build=build, retry=retry)
    transport = FakeTransport()
    with pytest.raises(FileExistsError):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=transport)
    assert transport.calls == []


@pytest.mark.parametrize("phase,max_sends", [
    ("authorization_consumed", 0), ("request_persisted", 0), ("send_reserved", 0),
    ("send_returned", 1), ("response_persisted", 1), ("verification_persisted", 1),
    ("before_retry_state_after", 3),
])
def test_crash_points_burn_authorization_and_prevent_duplicate_send(tmp_path, phase, max_sends):
    plan, auth, build, retry = plan_and_auth()
    transport = FakeTransport()
    def crash(current):
        if current == phase:
            raise KeyboardInterrupt(phase)
    with pytest.raises(KeyboardInterrupt):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=transport, fault=crash)
    assert len(transport.calls) == max_sends
    retry_transport = FakeTransport()
    with pytest.raises(FileExistsError):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=retry_transport)
    assert retry_transport.calls == []


def test_request_or_metadata_persistence_failure_prevents_send(tmp_path, monkeypatch):
    import forecast_trust_core._roughtime_execution as execution
    original = execution._write_bytes_exclusive
    def fail_request(path, payload):
        if path.name == "request.bin":
            raise OSError("synthetic write failure")
        return original(path, payload)
    monkeypatch.setattr(execution, "_write_bytes_exclusive", fail_request)
    transport = FakeTransport()
    with pytest.raises(OSError):
        run(tmp_path, transport=transport)
    assert transport.calls == []


@pytest.mark.parametrize("target", ["send-reservation.json", "retry-state-reserved.json"])
def test_send_metadata_persistence_failure_prevents_send(tmp_path, monkeypatch, target):
    import forecast_trust_core._roughtime_execution as execution
    original = execution._write_json_exclusive
    def fail_metadata(path, payload):
        if path.name == target:
            raise OSError("synthetic metadata failure")
        return original(path, payload)
    monkeypatch.setattr(execution, "_write_json_exclusive", fail_metadata)
    transport = FakeTransport()
    with pytest.raises(OSError):
        run(tmp_path, transport=transport)
    assert transport.calls == []


def test_crash_during_verification_retains_response_and_burns_authorization(tmp_path):
    class CrashingVerifier(FakeVerifier):
        def verify_response(self, provider, request_bytes, response_bytes):
            raise KeyboardInterrupt("synthetic verifier crash")
    plan, auth, build, retry = plan_and_auth()
    transport = FakeTransport()
    with pytest.raises(KeyboardInterrupt):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry,
            transport=transport, verifier=CrashingVerifier())
    event = tmp_path / "evidence" / "events" / auth["authorization_sha256"]
    assert (event / "providers" / PROVIDER_ORDER[0] / "attempt-1" / "response.bin").is_file()
    second = FakeTransport()
    with pytest.raises(FileExistsError):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=second)
    assert second.calls == []


def test_crash_immediately_after_transport_send_cannot_be_replayed(tmp_path):
    class CrashingTransport(FakeTransport):
        def send_and_receive(self, destination, request_bytes, timeout_seconds):
            self.calls.append((destination, request_bytes, timeout_seconds))
            raise KeyboardInterrupt("synthetic crash immediately after send")
    plan, auth, build, retry = plan_and_auth()
    transport = CrashingTransport()
    with pytest.raises(KeyboardInterrupt):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=transport)
    assert len(transport.calls) == 1
    event = tmp_path / "evidence" / "events" / auth["authorization_sha256"]
    assert (event / "providers" / PROVIDER_ORDER[0] / "attempt-1" / "send-reservation.json").is_file()
    assert (event / "providers" / PROVIDER_ORDER[0] / "attempt-1" / "retry-state-reserved.json").is_file()
    second = FakeTransport()
    with pytest.raises(FileExistsError):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=second)
    assert second.calls == []


def test_real_transport_uses_one_resolved_destination_and_checks_source(monkeypatch):
    class SocketDouble:
        def settimeout(self, value): self.timeout = value
        def connect(self, value): self.destination = value
        def send(self, value): self.request = value; return len(value)
        def recvfrom(self, size): return b"response", ("192.0.2.1", 2002)
        def close(self): pass
    sock = SocketDouble()
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [
        (socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP, "", ("192.0.2.2", 2002)),
        (socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP, "", ("192.0.2.1", 2002)),
    ])
    monkeypatch.setattr(socket, "socket", lambda *a, **k: sock)
    transport = RealUDPTransport(now=Clock().now)
    destination = transport.prepare_destination("example.invalid", 2002)
    outcome = transport.send_and_receive(destination, b"request", 2)
    assert destination.address == "192.0.2.1"
    assert sock.destination == ("192.0.2.1", 2002)
    assert outcome.status == "RESPONSE" and outcome.source_address == "192.0.2.1"


def test_event_directory_creation_failure_prevents_send(tmp_path):
    plan, auth, build, retry = plan_and_auth()
    root = tmp_path / "evidence"
    (root / "events" / auth["authorization_sha256"]).mkdir(parents=True)
    (root / "consumed").mkdir()
    transport = FakeTransport()
    with pytest.raises(FileExistsError):
        run(tmp_path, plan=plan, auth=auth, build=build, retry=retry, transport=transport)
    assert transport.calls == []


def test_evidence_root_creation_failure_prevents_send(tmp_path):
    (tmp_path / "evidence").write_bytes(b"not a directory")
    transport = FakeTransport()
    with pytest.raises((FileExistsError, NotADirectoryError)):
        run(tmp_path, transport=transport)
    assert transport.calls == []


def test_deadline_is_rechecked_after_durable_send_reservation(tmp_path):
    clock = Clock()
    transport = FakeTransport()
    def expire(phase):
        if phase == "send_reserved":
            clock.value = datetime(2026, 9, 14, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="deadline expired"):
        run(tmp_path, transport=transport, fault=expire, clock=clock)
    assert transport.calls == []


def test_generated_report_and_precise_receipts_validate_against_json_schema(tmp_path):
    import jsonschema
    report, _, _ = run(tmp_path)
    schema_root = Path(__file__).resolve().parents[1] / "schemas"
    report_schema = json.loads((schema_root / "roughtime_rehearsal_report.schema.json").read_text(encoding="utf-8"))
    receipt_schema = json.loads((schema_root / "roughtime_receipt.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(receipt_schema).validate(report["provider_results"][0]["receipt"])
    report_schema["properties"]["provider_results"]["items"]["properties"]["receipt"] = receipt_schema
    jsonschema.Draft202012Validator(report_schema).validate(report)


def test_report_failure_code_version_boundary_in_semantic_and_json_schema(tmp_path):
    import jsonschema

    schema_root = Path(__file__).resolve().parents[1] / "schemas"
    report_schema = json.loads((schema_root / "roughtime_rehearsal_report.schema.json").read_text(encoding="utf-8"))
    receipt_schema = json.loads((schema_root / "roughtime_receipt.schema.json").read_text(encoding="utf-8"))
    report_schema["properties"]["provider_results"]["items"]["properties"]["receipt"] = receipt_schema
    validator = jsonschema.Draft202012Validator(report_schema)

    plan, auth, build, retry = plan_and_auth()
    v12, _, _ = run(
        tmp_path / "v12", plan=plan, auth=auth, build=build, retry=retry,
        verifier=FakeVerifier({PROVIDER_ORDER[0]: "TYPE_MISMATCH"}),
        transport=FakeTransport(["success"] * 4),
    )
    assert v12["schema_version"] == "1.2"
    validate_rehearsal_report(v12, plan=plan, authorization=auth)
    validator.validate(v12)

    v11_new_code = reseal_report(v12, schema_version="1.1")
    with pytest.raises(ValueError, match="invalid failure code"):
        validate_rehearsal_report(v11_new_code, plan=plan, authorization=auth)
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(v11_new_code)

    old_plan, old_auth, old_build, old_retry = plan_and_auth()
    v11_old_code, _, _ = run(
        tmp_path / "v11-old", plan=old_plan, auth=old_auth, build=old_build, retry=old_retry,
        verifier=FakeVerifier({PROVIDER_ORDER[0]: "SIGNATURE_INVALID"}),
        transport=FakeTransport(["success"] * 4),
    )
    v11_old_code = reseal_report(v11_old_code, schema_version="1.1")
    validate_rehearsal_report(v11_old_code, plan=old_plan, authorization=old_auth)
    validator.validate(v11_old_code)

    unknown = deepcopy(v12)
    unknown["provider_results"][0]["attempts"][-1]["failure_code"] = "UNRECOGNIZED_FAILURE"
    unknown["provider_results"][0]["final_failure_code"] = "UNRECOGNIZED_FAILURE"
    unknown = reseal_report(unknown)
    with pytest.raises(ValueError, match="invalid failure code"):
        validate_rehearsal_report(unknown, plan=plan, authorization=auth)
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(unknown)


def test_receipt_json_schema_keeps_v11_whole_second_boundary(tmp_path):
    import jsonschema

    report, _, _ = run(tmp_path)
    receipt = deepcopy(report["provider_results"][0]["receipt"])
    schema_root = Path(__file__).resolve().parents[1] / "schemas"
    schema = json.loads((schema_root / "roughtime_receipt.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    validator.validate(receipt)

    receipt["schema_version"] = "1.1"
    receipt.pop("radius_nanoseconds")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(receipt)
    receipt["midpoint_utc"] = "2026-09-13T00:00:00Z"
    receipt["verified_receipt_upper_bound_utc"] = "2026-09-13T00:00:02Z"
    validator.validate(receipt)
