package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
)

const (
	actionBuildRequest   = "build-request"
	actionVerifyResponse = "verify-response"
	packetSize           = 1036
	nonceSize            = 32
	wireVersion          = "0x8000000c"
)

type frozenProvider struct {
	ProviderID  string
	RootBase64  string
	RequireTYPE bool
	RequireSRV  bool
	WireProfile string
}

var frozenProviders = map[string]frozenProvider{
	"roughtime.se": {
		ProviderID:  "roughtime.se",
		RootBase64:  "S3AzfZJ5CjSdkJ21ZJGbxqdYP/SoE8fXKY0+aicsehI=",
		RequireTYPE: true,
		RequireSRV:  true,
		WireProfile: "IETF_D14_D19_TYPED_SHARED_WIRE_ACCEPT_BOTH_MERKLE_ORDERS",
	},
	"time.txryan.com": {
		ProviderID:  "time.txryan.com",
		RootBase64:  "iBVjxg/1j7y1+kQUTBYdTabxCppesU/07D4PMDJk2WA=",
		RequireTYPE: true,
		RequireSRV:  true,
		WireProfile: "IETF_D14_D19_TYPED_SHARED_WIRE_ACCEPT_BOTH_MERKLE_ORDERS",
	},
	"TimeNL-Roughtime": {
		ProviderID:  "TimeNL-Roughtime",
		RootBase64:  "v2CievhgKsxzlWPwIkYFUXeA51Akhkv5uhJCj1/kbiY=",
		RequireTYPE: false,
		RequireSRV:  true,
		WireProfile: "IETF_D12_D13_UNTYPED_SHARED_WIRE_NODE_FIRST",
	},
}

type actionInput struct {
	SchemaVersion  string `json:"schema_version"`
	Action         string `json:"action"`
	ProviderID     string `json:"provider_id"`
	NonceHex       string `json:"nonce_hex"`
	RequestBase64  string `json:"request_base64,omitempty"`
	ResponseBase64 string `json:"response_base64,omitempty"`
}

type buildOutput struct {
	SchemaVersion string `json:"schema_version"`
	Action        string `json:"action"`
	ProviderID    string `json:"provider_id"`
	WireVersion   string `json:"wire_version"`
	WireProfile   string `json:"wire_profile"`
	RequireTYPE   bool   `json:"require_type"`
	RequireSRV    bool   `json:"require_srv"`
	PacketProfile string `json:"packet_profile"`
	PacketSize    int    `json:"packet_size"`
	NonceHex      string `json:"nonce_hex"`
	RequestBase64 string `json:"request_base64"`
	RequestSHA256 string `json:"request_sha256"`
}

type verifyOutput struct {
	SchemaVersion     string `json:"schema_version"`
	Action            string `json:"action"`
	ProviderID        string `json:"provider_id"`
	Verified          bool   `json:"verified"`
	WireVersion       string `json:"wire_version"`
	WireProfile       string `json:"wire_profile"`
	RequireTYPE       bool   `json:"require_type"`
	RequireSRV        bool   `json:"require_srv"`
	NonceHex          string `json:"nonce_hex"`
	RequestSHA256     string `json:"request_sha256"`
	ResponseSHA256    string `json:"response_sha256"`
	MidpointUTC       string `json:"midpoint_utc"`
	RadiusNanoseconds int64  `json:"radius_nanoseconds"`
}

func rejectTopLevelDuplicateKeys(raw []byte) error {
	dec := json.NewDecoder(bytes.NewReader(raw))
	first, err := dec.Token()
	if err != nil {
		return err
	}
	delim, ok := first.(json.Delim)
	if !ok || delim != '{' {
		return errors.New("top-level JSON value must be an object")
	}
	seen := make(map[string]struct{})
	for dec.More() {
		tok, err := dec.Token()
		if err != nil {
			return err
		}
		key, ok := tok.(string)
		if !ok {
			return errors.New("JSON object key is not a string")
		}
		if _, exists := seen[key]; exists {
			return fmt.Errorf("duplicate JSON key %q", key)
		}
		seen[key] = struct{}{}
		var value json.RawMessage
		if err := dec.Decode(&value); err != nil {
			return err
		}
	}
	if _, err := dec.Token(); err != nil {
		return err
	}
	if tok, err := dec.Token(); err != io.EOF {
		if err == nil {
			return fmt.Errorf("trailing JSON token %v", tok)
		}
		return fmt.Errorf("trailing JSON data: %w", err)
	}
	return nil
}

func decodeStrictJSON(r io.Reader, dst any) error {
	raw, err := io.ReadAll(r)
	if err != nil {
		return err
	}
	if err := rejectTopLevelDuplicateKeys(raw); err != nil {
		return err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	if err := dec.Decode(dst); err != nil {
		return err
	}
	return nil
}

func validateInput(in actionInput, expectedAction string) (frozenProvider, []byte, error) {
	if in.SchemaVersion != "1.0" {
		return frozenProvider{}, nil, errors.New("schema_version must be 1.0")
	}
	if in.Action != expectedAction {
		return frozenProvider{}, nil, fmt.Errorf("action must be %q", expectedAction)
	}
	provider, ok := frozenProviders[in.ProviderID]
	if !ok {
		return frozenProvider{}, nil, errors.New("provider_id is outside the frozen provider pool")
	}
	if len(in.NonceHex) != 64 {
		return frozenProvider{}, nil, errors.New("nonce_hex must contain exactly 32 bytes")
	}
	nonce, err := hex.DecodeString(in.NonceHex)
	if err != nil || len(nonce) != nonceSize || hex.EncodeToString(nonce) != in.NonceHex {
		return frozenProvider{}, nil, errors.New("nonce_hex must be exactly 64 lowercase hexadecimal characters")
	}
	if expectedAction == actionBuildRequest {
		if in.RequestBase64 != "" || in.ResponseBase64 != "" {
			return frozenProvider{}, nil, errors.New("build-request input must not contain request_base64 or response_base64")
		}
	} else {
		if in.RequestBase64 == "" || in.ResponseBase64 == "" {
			return frozenProvider{}, nil, errors.New("verify-response requires request_base64 and response_base64")
		}
	}
	return provider, nonce, nil
}

func decodeB64(s, field string) ([]byte, error) {
	b, err := base64.StdEncoding.Strict().DecodeString(s)
	if err != nil || len(b) == 0 {
		return nil, fmt.Errorf("%s is invalid strict base64", field)
	}
	return b, nil
}

func sha256hex(b []byte) string {
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

func ensureStandardPacket(request []byte) error {
	if len(request) != packetSize {
		return fmt.Errorf("request packet length %d, want %d for STANDARD_1024_BODY", len(request), packetSize)
	}
	if len(request) < 12 || !bytes.Equal(request[:8], []byte("ROUGHTIM")) {
		return errors.New("request is missing ROUGHTIM framing")
	}
	return nil
}

func writeNewFile(path string, payload []byte) error {
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o644)
	if err != nil {
		if os.IsExist(err) {
			return fmt.Errorf("refusing to overwrite existing output: %s", path)
		}
		return err
	}
	ok := false
	defer func() {
		_ = f.Close()
		if !ok {
			_ = os.Remove(path)
		}
	}()
	if _, err := f.Write(payload); err != nil {
		return err
	}
	if err := f.Sync(); err != nil {
		return err
	}
	ok = true
	return f.Close()
}
