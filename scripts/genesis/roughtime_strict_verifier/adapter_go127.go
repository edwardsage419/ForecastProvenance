//go:build go1.27

package main

import (
	"bytes"
	"encoding/base64"
	"errors"
	"fmt"

	"github.com/tannerryan/roughtime/protocol"
)

func frozenRoot(provider frozenProvider) ([]byte, error) {
	root, err := base64.StdEncoding.Strict().DecodeString(provider.RootBase64)
	if err != nil || len(root) != 32 {
		return nil, errors.New("frozen provider root is invalid")
	}
	return root, nil
}

func validateBuiltRequest(provider frozenProvider, nonce, request []byte) error {
	if err := ensureStandardPacket(request); err != nil {
		return err
	}
	parsed, err := protocol.ParseRequest(request)
	if err != nil {
		return fmt.Errorf("parse retained request: %w", err)
	}
	if !bytes.Equal(parsed.Nonce, nonce) {
		return errors.New("retained request nonce mismatch")
	}
	if len(parsed.Versions) != 1 || parsed.Versions[0] != protocol.VersionDraft12 {
		return errors.New("retained request must offer exactly wire version 0x8000000c")
	}
	if parsed.HasType != provider.RequireTYPE {
		return errors.New("retained request TYPE profile mismatch")
	}
	root, err := frozenRoot(provider)
	if err != nil {
		return err
	}
	expectedSRV := protocol.ComputeSRV(root)
	if provider.RequireSRV && !bytes.Equal(parsed.SRV, expectedSRV) {
		return errors.New("retained request SRV does not match frozen root")
	}
	return nil
}

func buildRequestWithPinnedProtocol(provider frozenProvider, nonce []byte) ([]byte, error) {
	root, err := frozenRoot(provider)
	if err != nil {
		return nil, err
	}
	srv := protocol.ComputeSRV(root)
	opts := protocol.RequestOptions{OmitTYPE: !provider.RequireTYPE, LegacyPacketSize: false}
	request, err := protocol.CreateRequestWithNonceOptions(
		[]protocol.Version{protocol.VersionDraft12}, nonce, srv, opts,
	)
	if err != nil {
		return nil, fmt.Errorf("build request with pinned protocol: %w", err)
	}
	if err := validateBuiltRequest(provider, nonce, request); err != nil {
		return nil, err
	}
	return request, nil
}

func validateResponseTypeProfile(provider frozenProvider, response []byte) error {
	if len(response) < protocol.PacketHeaderSize {
		return errors.New("response is shorter than ROUGHTIM header")
	}
	bodyLen, err := protocol.ParsePacketHeader(response[:protocol.PacketHeaderSize])
	if err != nil {
		return fmt.Errorf("response framing: %w", err)
	}
	if int(bodyLen) != len(response)-protocol.PacketHeaderSize {
		return errors.New("response framing length mismatch")
	}
	msg, err := protocol.Decode(response[protocol.PacketHeaderSize:])
	if err != nil {
		return fmt.Errorf("decode response for TYPE profile: %w", err)
	}
	_, hasTYPE := msg[protocol.TagTYPE]
	if provider.RequireTYPE != hasTYPE {
		return errors.New("response TYPE profile mismatch")
	}
	return nil
}

func verifyWithPinnedProtocol(provider frozenProvider, nonce, request, response []byte) (string, int64, error) {
	if err := validateBuiltRequest(provider, nonce, request); err != nil {
		return "", 0, err
	}
	if err := validateResponseTypeProfile(provider, response); err != nil {
		return "", 0, err
	}
	root, err := frozenRoot(provider)
	if err != nil {
		return "", 0, err
	}
	midpoint, radius, err := protocol.VerifyReplyWithOptions(
		[]protocol.Version{protocol.VersionDraft12},
		response,
		root,
		nonce,
		request,
		protocol.VerifyOptions{RequireTYPE: provider.RequireTYPE},
	)
	if err != nil {
		return "", 0, fmt.Errorf("pinned protocol verification failed: %w", err)
	}
	if radius <= 0 {
		return "", 0, errors.New("authenticated radius must be positive")
	}
	return midpoint.UTC().Format("2006-01-02T15:04:05.999999999Z"), radius.Nanoseconds(), nil
}
