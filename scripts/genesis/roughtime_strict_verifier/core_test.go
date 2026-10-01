package main

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func validInput(action, provider string) actionInput {
	return actionInput{SchemaVersion: "1.0", Action: action, ProviderID: provider, NonceHex: strings.Repeat("0a", 32)}
}

func TestFrozenProviderPool(t *testing.T) {
	if len(frozenProviders) != 3 {
		t.Fatalf("got %d providers", len(frozenProviders))
	}
	if frozenProviders["TimeNL-Roughtime"].RequireTYPE {
		t.Fatal("TimeNL must be untyped")
	}
	if !frozenProviders["roughtime.se"].RequireTYPE || !frozenProviders["time.txryan.com"].RequireTYPE {
		t.Fatal("typed provider profile changed")
	}
}

func TestStrictJSONRejectsUnknownAndTrailing(t *testing.T) {
	cases := []string{
		`{"schema_version":"1.0","action":"build-request","provider_id":"roughtime.se","nonce_hex":"` + strings.Repeat("00", 32) + `","extra":1}`,
		`{"schema_version":"1.0","action":"build-request","provider_id":"roughtime.se","nonce_hex":"` + strings.Repeat("00", 32) + `"}{}`,
		`{"schema_version":"1.0","action":"build-request","provider_id":"roughtime.se","provider_id":"time.txryan.com","nonce_hex":"` + strings.Repeat("00", 32) + `"}`,
	}
	for _, raw := range cases {
		var in actionInput
		if decodeStrictJSON(bytes.NewBufferString(raw), &in) == nil {
			t.Fatalf("accepted invalid JSON %q", raw)
		}
	}
}

func TestValidateInputRejectsUppercaseNonce(t *testing.T) {
	in := validInput(actionBuildRequest, "roughtime.se")
	in.NonceHex = strings.Repeat("AA", 32)
	if _, _, err := validateInput(in, actionBuildRequest); err == nil {
		t.Fatal("accepted uppercase nonce")
	}
}

func TestValidateInputRejectsUnknownProvider(t *testing.T) {
	in := validInput(actionBuildRequest, "unknown")
	if _, _, err := validateInput(in, actionBuildRequest); err == nil {
		t.Fatal("accepted provider substitution")
	}
}

func TestBuildInputRejectsEvidenceFields(t *testing.T) {
	in := validInput(actionBuildRequest, "roughtime.se")
	in.RequestBase64 = "AA=="
	if _, _, err := validateInput(in, actionBuildRequest); err == nil {
		t.Fatal("accepted request bytes in build action")
	}
}

func TestVerifyInputRequiresBothPackets(t *testing.T) {
	in := validInput(actionVerifyResponse, "roughtime.se")
	in.RequestBase64 = "AA=="
	if _, _, err := validateInput(in, actionVerifyResponse); err == nil {
		t.Fatal("accepted missing response")
	}
}

func TestStandardPacketGuard(t *testing.T) {
	legacy := make([]byte, 1024)
	copy(legacy, []byte("ROUGHTIM"))
	if ensureStandardPacket(legacy) == nil {
		t.Fatal("accepted legacy 1024-byte total packet")
	}
	standard := make([]byte, packetSize)
	copy(standard, []byte("ROUGHTIM"))
	if err := ensureStandardPacket(standard); err != nil {
		t.Fatalf("rejected standard framed size: %v", err)
	}
}

func TestRefuseOutputOverwrite(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "out.json")
	if err := os.WriteFile(path, []byte("old"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := writeNewFile(path, []byte("new")); err == nil {
		t.Fatal("overwrote existing output")
	}
	got, _ := os.ReadFile(path)
	if string(got) != "old" {
		t.Fatalf("existing output changed: %q", got)
	}
}
