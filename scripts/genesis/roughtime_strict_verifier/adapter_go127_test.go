//go:build go1.27

package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/sha512"
	"encoding/base64"
	"encoding/binary"
	"errors"
	"strings"
	"testing"
	"time"

	"forecastprovenance/roughtime_strict_verifier/pinned/roughtime/protocol"
)

const fixtureHashSize = 32

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

func signedFixture(t *testing.T, provider frozenProvider, rootSK ed25519.PrivateKey, nonce []byte, nodeFirst bool, leafIndex int) ([]byte, []byte) {
	t.Helper()
	if leafIndex < 0 || leafIndex > 1 {
		t.Fatalf("invalid selected leaf index %d", leafIndex)
	}
	request, err := buildRequestWithPinnedProtocol(provider, nonce)
	if err != nil {
		t.Fatalf("build request: %v", err)
	}
	parsed, err := protocol.ParseRequest(request)
	if err != nil {
		t.Fatalf("parse request: %v", err)
	}
	companionNonce := append([]byte(nil), nonce...)
	companionNonce[0] ^= 0xff
	companionRequest, err := buildRequestWithPinnedProtocol(provider, companionNonce)
	if err != nil {
		t.Fatalf("build companion request: %v", err)
	}
	companionParsed, err := protocol.ParseRequest(companionRequest)
	if err != nil {
		t.Fatalf("parse companion request: %v", err)
	}
	requests := []protocol.Request{*parsed, *companionParsed}
	if leafIndex == 1 {
		requests[0], requests[1] = requests[1], requests[0]
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
		requests,
		midpoint,
		2*time.Second,
		cert,
		protocol.ReplyOptions{Draft14NodeFirst: nodeFirst},
	)
	if err != nil {
		t.Fatalf("create reply: %v", err)
	}
	if len(replies) != 2 {
		t.Fatalf("got %d replies", len(replies))
	}
	return request, replies[leafIndex]
}

func responseMessage(t *testing.T, response []byte) map[uint32][]byte {
	t.Helper()
	if len(response) < protocol.PacketHeaderSize {
		t.Fatal("response is shorter than ROUGHTIM header")
	}
	bodyLen, err := protocol.ParsePacketHeader(response[:protocol.PacketHeaderSize])
	if err != nil {
		t.Fatalf("parse response header: %v", err)
	}
	if int(bodyLen) != len(response)-protocol.PacketHeaderSize {
		t.Fatalf("response body length %d, want %d", bodyLen, len(response)-protocol.PacketHeaderSize)
	}
	msg, err := protocol.Decode(response[protocol.PacketHeaderSize:])
	if err != nil {
		t.Fatalf("decode response: %v", err)
	}
	return msg
}

func requirePathHashes(t *testing.T, response []byte, want int) {
	t.Helper()
	path, ok := responseMessage(t, response)[protocol.TagPATH]
	if !ok {
		t.Fatal("response has no PATH")
	}
	if got := len(path) / fixtureHashSize; len(path)%fixtureHashSize != 0 || got != want {
		t.Fatalf("PATH contains %d bytes, want %d hashes", len(path), want)
	}
}

func merkleHash(left, right []byte) []byte {
	h := sha512.New()
	_, _ = h.Write([]byte{0x01})
	_, _ = h.Write(left)
	_, _ = h.Write(right)
	return h.Sum(nil)[:fixtureHashSize]
}

func leafHash(request []byte) []byte {
	h := sha512.New()
	_, _ = h.Write([]byte{0x00})
	_, _ = h.Write(request)
	return h.Sum(nil)[:fixtureHashSize]
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
			request, response := signedFixture(t, provider, rootSK, nonce, false, 0)
			requirePathHashes(t, response, 1)
			verifyFixture(t, provider, nonce, request, response)
		})
	}
}

func TestGo127TypedNodeFirstFixture(t *testing.T) {
	rootSK := deterministicKey(0x31)
	provider := syntheticProvider(t, "roughtime.se", true, rootSK)
	nonce := []byte(strings.Repeat("2", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, true, 0)
	requirePathHashes(t, response, 1)
	verifyFixture(t, provider, nonce, request, response)
}

func TestGo127UntypedDraft12Fixture(t *testing.T) {
	rootSK := deterministicKey(0x32)
	provider := syntheticProvider(t, "TimeNL-Roughtime", false, rootSK)
	nonce := []byte(strings.Repeat("3", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, false, 0)
	requirePathHashes(t, response, 1)
	verifyFixture(t, provider, nonce, request, response)
}

func TestGo127RejectsWrongMerkleOrder(t *testing.T) {
	rootSK := deterministicKey(0x38)
	provider := syntheticProvider(t, "TimeNL-Roughtime", false, rootSK)
	nonce := []byte(strings.Repeat("8", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, false, 1)
	msg := responseMessage(t, response)
	path := msg[protocol.TagPATH]
	if len(path) != fixtureHashSize {
		t.Fatalf("PATH contains %d bytes, want one hash", len(path))
	}
	index := msg[protocol.TagINDX]
	if len(index) != 4 || binary.LittleEndian.Uint32(index) != 1 {
		t.Fatalf("unexpected original INDX %x", index)
	}
	binary.LittleEndian.PutUint32(index, 0)

	srep, err := protocol.Decode(msg[protocol.TagSREP])
	if err != nil {
		t.Fatalf("decode SREP: %v", err)
	}
	root := srep[protocol.TagROOT]
	leaf := leafHash(request)
	if !bytes.Equal(merkleHash(leaf, path), root) {
		t.Fatal("constructed proof is not valid under hash-first ordering")
	}
	if bytes.Equal(merkleHash(path, leaf), root) {
		t.Fatal("constructed proof unexpectedly remains valid under node-first ordering")
	}

	if _, _, err := verifyWithPinnedProtocol(provider, nonce, request, response); !errors.Is(err, protocol.ErrMerkleMismatch) {
		t.Fatalf("wrong-order response rejection = %v, want %v", err, protocol.ErrMerkleMismatch)
	}
}

func TestGo127RejectsWrongRoot(t *testing.T) {
	rootSK := deterministicKey(0x33)
	provider := syntheticProvider(t, "roughtime.se", true, rootSK)
	nonce := []byte(strings.Repeat("4", nonceSize))
	request, response := signedFixture(t, provider, rootSK, nonce, false, 0)
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
	request, response := signedFixture(t, provider, rootSK, nonce, false, 0)
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
	request, response := signedFixture(t, provider, rootSK, nonce, false, 0)
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
	request, response := signedFixture(t, provider, rootSK, nonce, false, 0)
	legacySized := append([]byte(nil), request[:1024]...)
	if _, _, err := verifyWithPinnedProtocol(provider, nonce, legacySized, response); err == nil {
		t.Fatal("accepted legacy sized packet")
	}
	provider.RequireTYPE = false
	if _, _, err := verifyWithPinnedProtocol(provider, nonce, request, response); err == nil {
		t.Fatal("accepted typed request under untyped profile")
	}
}
