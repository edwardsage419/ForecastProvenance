package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"os"
)

func usage() error {
	return fmt.Errorf("usage: fpp-roughtime-strict {build-request|verify-response} --input INPUT.json --output OUTPUT.json")
}

func paths(args []string) (string, string, error) {
	if len(args) != 4 || args[0] != "--input" || args[2] != "--output" || args[1] == "" || args[3] == "" {
		return "", "", usage()
	}
	return args[1], args[3], nil
}

func run(action string, args []string) error {
	if action != actionBuildRequest && action != actionVerifyResponse {
		return usage()
	}
	inputPath, outputPath, err := paths(args)
	if err != nil {
		return err
	}
	inFile, err := os.Open(inputPath)
	if err != nil {
		return err
	}
	defer inFile.Close()
	var in actionInput
	if err := decodeStrictJSON(inFile, &in); err != nil {
		return fmt.Errorf("strict input JSON: %w", err)
	}
	provider, nonce, err := validateInput(in, action)
	if err != nil {
		return err
	}

	var out any
	if action == actionBuildRequest {
		request, err := buildRequestWithPinnedProtocol(provider, nonce)
		if err != nil {
			return err
		}
		if err := ensureStandardPacket(request); err != nil {
			return err
		}
		out = buildOutput{
			SchemaVersion: "1.0", Action: actionBuildRequest, ProviderID: provider.ProviderID,
			WireVersion: wireVersion, WireProfile: provider.WireProfile,
			RequireTYPE: provider.RequireTYPE, RequireSRV: provider.RequireSRV,
			PacketProfile: "STANDARD_1024_BODY", PacketSize: len(request), NonceHex: in.NonceHex,
			RequestBase64: base64.StdEncoding.EncodeToString(request), RequestSHA256: sha256hex(request),
		}
	} else {
		request, err := decodeB64(in.RequestBase64, "request_base64")
		if err != nil {
			return err
		}
		response, err := decodeB64(in.ResponseBase64, "response_base64")
		if err != nil {
			return err
		}
		if err := ensureStandardPacket(request); err != nil {
			return err
		}
		midpoint, radiusNS, err := verifyWithPinnedProtocol(provider, nonce, request, response)
		if err != nil {
			return err
		}
		out = verifyOutput{
			SchemaVersion: "1.0", Action: actionVerifyResponse, ProviderID: provider.ProviderID,
			Verified: true, WireVersion: wireVersion, WireProfile: provider.WireProfile,
			RequireTYPE: provider.RequireTYPE, RequireSRV: provider.RequireSRV, NonceHex: in.NonceHex,
			RequestSHA256: sha256hex(request), ResponseSHA256: sha256hex(response),
			MidpointUTC: midpoint, RadiusNanoseconds: radiusNS,
		}
	}
	payload, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return err
	}
	payload = append(payload, '\n')
	return writeNewFile(outputPath, payload)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, usage())
		os.Exit(2)
	}
	if err := run(os.Args[1], os.Args[2:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
}
