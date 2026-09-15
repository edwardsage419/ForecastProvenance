package main

import (
    "bytes"
    "crypto/ed25519"
    "encoding/base64"
    "encoding/json"
    "errors"
    "fmt"
    "io"
    "os"
)

const (
    schemaVersion   = "1.0"
    requestType     = "Ed25519VerificationRequest"
    resultType      = "Ed25519VerificationResult"
    maxRequestBytes = 2 * 1024 * 1024
    maxMessageBytes = 1024 * 1024
)

type verifyInput struct {
    SchemaVersion      string `json:"schema_version"`
    ObjectType         string `json:"object_type"`
    PublicKeyBase64    string `json:"public_key_base64"`
    MessageBase64      string `json:"message_base64"`
    SignatureBase64    string `json:"signature_base64"`
}

type verifyOutput struct {
    SchemaVersion string `json:"schema_version"`
    ObjectType    string `json:"object_type"`
    Valid         bool   `json:"valid"`
}

func decodeStrictRequest(r io.Reader) (verifyInput, error) {
    var out verifyInput
    data, err := io.ReadAll(io.LimitReader(r, maxRequestBytes+1))
    if err != nil {
        return out, fmt.Errorf("read request: %w", err)
    }
    if len(data) > maxRequestBytes {
        return out, errors.New("request exceeds size limit")
    }

    dec := json.NewDecoder(bytes.NewReader(data))
    token, err := dec.Token()
    if err != nil {
        return out, fmt.Errorf("decode request: %w", err)
    }
    delim, ok := token.(json.Delim)
    if !ok || delim != '{' {
        return out, errors.New("request must be a JSON object")
    }

    seen := make(map[string]struct{}, 5)
    for dec.More() {
        token, err = dec.Token()
        if err != nil {
            return out, fmt.Errorf("decode field name: %w", err)
        }
        key, ok := token.(string)
        if !ok {
            return out, errors.New("request field name must be a string")
        }
        if _, exists := seen[key]; exists {
            return out, fmt.Errorf("duplicate request field: %s", key)
        }
        seen[key] = struct{}{}

        var raw json.RawMessage
        if err := dec.Decode(&raw); err != nil {
            return out, fmt.Errorf("decode %s: %w", key, err)
        }
        if len(raw) < 2 || raw[0] != '"' {
            return out, fmt.Errorf("request field %s must be a JSON string", key)
        }
        var value string
        if err := json.Unmarshal(raw, &value); err != nil {
            return out, fmt.Errorf("decode %s string: %w", key, err)
        }

        switch key {
        case "schema_version":
            out.SchemaVersion = value
        case "object_type":
            out.ObjectType = value
        case "public_key_base64":
            out.PublicKeyBase64 = value
        case "message_base64":
            out.MessageBase64 = value
        case "signature_base64":
            out.SignatureBase64 = value
        default:
            return out, fmt.Errorf("unknown request field: %s", key)
        }
    }

    token, err = dec.Token()
    if err != nil {
        return out, fmt.Errorf("decode object close: %w", err)
    }
    delim, ok = token.(json.Delim)
    if !ok || delim != '}' {
        return out, errors.New("request object did not close")
    }
    if token, err = dec.Token(); err != io.EOF {
        if err == nil {
            return out, fmt.Errorf("unexpected trailing JSON token: %v", token)
        }
        return out, fmt.Errorf("trailing request data: %w", err)
    }

    if len(seen) != 5 {
        return out, errors.New("request fields incomplete")
    }
    if out.SchemaVersion != schemaVersion {
        return out, errors.New("schema_version mismatch")
    }
    if out.ObjectType != requestType {
        return out, errors.New("object_type mismatch")
    }
    return out, nil
}

func decodeCanonicalBase64(value, name string, expectedLen int, allowEmpty bool) ([]byte, error) {
    if value == "" && !allowEmpty {
        return nil, fmt.Errorf("%s must be nonempty canonical base64", name)
    }
    decoded, err := base64.StdEncoding.DecodeString(value)
    if err != nil {
        return nil, fmt.Errorf("%s invalid base64", name)
    }
    if base64.StdEncoding.EncodeToString(decoded) != value {
        return nil, fmt.Errorf("%s noncanonical base64", name)
    }
    if expectedLen >= 0 && len(decoded) != expectedLen {
        return nil, fmt.Errorf("%s decoded length invalid", name)
    }
    return decoded, nil
}

func verifyRequest(input verifyInput) (bool, error) {
    publicKey, err := decodeCanonicalBase64(input.PublicKeyBase64, "public_key_base64", ed25519.PublicKeySize, false)
    if err != nil {
        return false, err
    }
    message, err := decodeCanonicalBase64(input.MessageBase64, "message_base64", -1, true)
    if err != nil {
        return false, err
    }
    if len(message) > maxMessageBytes {
        return false, errors.New("message exceeds size limit")
    }
    signature, err := decodeCanonicalBase64(input.SignatureBase64, "signature_base64", ed25519.SignatureSize, false)
    if err != nil {
        return false, err
    }
    return ed25519.Verify(ed25519.PublicKey(publicKey), message, signature), nil
}

func run(r io.Reader, w io.Writer) error {
    input, err := decodeStrictRequest(r)
    if err != nil {
        return err
    }
    valid, err := verifyRequest(input)
    if err != nil {
        return err
    }
    encoder := json.NewEncoder(w)
    encoder.SetEscapeHTML(false)
    return encoder.Encode(verifyOutput{
        SchemaVersion: schemaVersion,
        ObjectType:    resultType,
        Valid:         valid,
    })
}

func main() {
    if err := run(os.Stdin, os.Stdout); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(2)
    }
}
