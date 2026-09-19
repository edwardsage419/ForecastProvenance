//go:build !go1.27

package main

import "errors"

func buildRequestWithPinnedProtocol(provider frozenProvider, nonce []byte) ([]byte, error) {
	return nil, errors.New("pinned cryptographic adapter requires Go 1.27 or newer")
}

func verifyWithPinnedProtocol(provider frozenProvider, nonce, request, response []byte) (string, int64, error) {
	return "", 0, errors.New("pinned cryptographic adapter requires Go 1.27 or newer")
}
