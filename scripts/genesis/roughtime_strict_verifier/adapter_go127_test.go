//go:build go1.27

package main

import (
	"crypto/ed25519"
	"encoding/base64"
	"strings"
	"testing"
	"time"

	"forecastprovenance/roughtime_strict_verifier/pinned/roughtime/protocol"
)

func deterministicKey(fill byte) ed25519.PrivateKey {
	return ed25519.NewKeyFromSeed([]byte(strings.Repeat(string([]byte{fill}), ed25519.SeedSize)))
}

func syntheticProvider(t *testing.T, providerID string, requireTYPE bool, rootSK ed25519.PrivateKey) frozenProvider {
	t.Helper()
	original, ok := frozenProviders[providerID]
	if !ok {
		t.Fatalf("unknown frozen provider %q", providerID)
	}
	provider := original
	provider.RequireTYPE = requireTYPE
	provider.RequireSRV = true
	provider.RootBase64 = base64.StdEncoding.EncodeToString(rootSK.Public().(ed25519.PublicKey))
	frozenProviders[providerID] = provider
	t.Cleanup(func() { frozenProviders[providerID] = original })
	return provider
}

func signedFixture(t *testing.T, provider frozenProvider, rootSK ed25519.PrivateKey, nonce []byte, nodeFirst bool) ([]byte, []byte) {
	t.Helper()
	request, err := buildRequestWithPinnedProtocol(provider, nonce)
	if err != nil {
		t.Fatalf("build request: %v", err)
	}
	parsed, err := protocol.ParseRequest(request)
	if err != nil {
		t.Fatalf("parse request: %v", err)
	}
	onlineSK := deterministicKey(0x42)
	mint := time.Date(2026, 9, 12, 0, 0, 0, 0, time.UTC)
	maxt := mint.Add(24 * time.Hour)
	cert, err := protocol.NewCertificateWithVersions(
		mint,
		maxt,
		onlineSK,
		rootSK,
		[]protocol.Version{protocol.VersionDraft12},
	)
	if err != nil {
		t.Fatalf("create certificate: %v", err)
	}
	t.Cleanup(cert.Wipe)
	midpoint := mint.Add(12 * time.Hour)
	replies, err := protocol.CreateRepliesWithOptions(
		protocol.VersionDraft12,
		[]protocol.Request{*parsed},
		midpoint,
		2*time.Second,
		cert,
		protocol.ReplyOptions{Draft14NodeFirst: nodeFirst},
	)
	if err != nil {
		t.Fatalf("create reply: %v", err)
	}
	if len(replies) != 1 {
		t.Fatalf("got %d replies", len(replies))
	}
	return request, replies[0]
}

func verifyFixture(t *testing.T, provider frozenProvider, nonce, request, response []byte) {
	t.Helper()
	midpoint, radiusNS, err := verifyWithPinnedProtocol(provider, nonce, request, response)
	if err != nil {
		t.Fatalf("verify fixture: %v", err)
	}
	if midpoint == "" {
		t.Fatal("empty midpoint")
	}
	if radiusNS <= 0 {
		t.Fatalf("nonpositive radius %d", radiusNS)
	}
}

func TestGo127TypedHashFirstFixtures(t *testing.T) {
	for i, providerID := range []string{"roughtime.se", "time.txryan.com"} {
		t.Run(providerID, func(t *testing.T) {
			rootSK := deterministicKey(byte(0x10 + i))
			provider := syntheticProvider(t, providerID, true, rootSK)
			nonce := []byte(strings.Repeat(string([]byte{byte(0x20 + i)}), nonceSize))
			request, response := signedFixture(t, provider, rootSK, nonce, false)
			verifyFixture(t, provider, nonce, request, response)
		})
	}
}

func TestGo127TypedNodeFirstFixture(t *testing.T) {
	rootSK := deterministicKey(0x31)
	provider := syntheticProvider(t, "roughtime.se", true, rootSK)
	nonce := []byte(strings.Repeat("2", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, true)
	verifyFixture(t, provider, nonce, request, response)
}

func TestGo127UntypedDraft12Fixture(t *testing.T) {
	rootSK := deterministicKey(0x32)
	provider := syntheticProvider(t, "TimeNL-Roughtime", false, rootSK)
	nonce := []byte(strings.Repeat("3", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, false)
	verifyFixture(t, provider, nonce, request, response)
}

func TestGo127RejectsWrongRoot(t *testing.T) {
	rootSK := deterministicKey(0x33)
	provider := syntheticProvider(t, "roughtime.se", true, rootSK)
	nonce := []byte(strings.Repeat("4", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, false)
	wrongRoot := deterministicKey(0x34)
	provider.RootBase64 = base64.StdEncoding.EncodeToString(wrongRoot.Public().(ed25519.PublicKey))
	if _, _, err := verifyWithPinnedProtocol(provider, nonce, request, response); err == nil {
		t.Fatal("accepted response under wrong root")
	}
}

func TestGo127RejectsMutatedResponse(t *testing.T) {
	rootSK := deterministicKey(0x35)
	provider := syntheticProvider(t, "roughtime.se", true, rootSK)
	nonce := []byte(strings.Repeat("5", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, false)
	mutated := append([]byte(nil), response...)
	mutated[len(mutated)-1] ^= 0x01
	if _, _, err := verifyWithPinnedProtocol(provider, nonce, request, mutated); err == nil {
		t.Fatal("accepted mutated response")
	}
}

func TestGo127RejectsWrongNonce(t *testing.T) {
	rootSK := deterministicKey(0x36)
	provider := syntheticProvider(t, "roughtime.se", true, rootSK)
	nonce := []byte(strings.Repeat("6", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, false)
	wrongNonce := append([]byte(nil), nonce...)
	wrongNonce[0] ^= 0x01
	if _, _, err := verifyWithPinnedProtocol(provider, wrongNonce, request, response); err == nil {
		t.Fatal("accepted wrong nonce")
	}
}

func TestGo127RejectsPacketAndTypeProfileMismatch(t *testing.T) {
	rootSK := deterministicKey(0x37)
	provider := syntheticProvider(t, "roughtime.se", true, rootSK)
	nonce := []byte(strings.Repeat("7", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, false)
	legacySized := append([]byte(nil), request[:1024]...)
	if _, _, err := verifyWithPinnedProtocol(provider, nonce, legacySized, response); err == nil {
		t.Fatal("accepted legacy sized packet")
	}
	provider.RequireTYPE = false
	if _, _, err := verifyWithPinnedProtocol(provider, nonce, request, response); err == nil {
		t.Fatal("accepted typed request under untyped profile")
	}
}
