package main

import (
    "bytes"
    "encoding/base64"
    "encoding/hex"
    "encoding/json"
    "strings"
    "testing"
)

func mustHex(t *testing.T, value string) []byte {
    t.Helper()
    out, err := hex.DecodeString(value)
    if err != nil {
        t.Fatal(err)
    }
    return out
}

func requestFor(publicKey, message, signature []byte) verifyInput {
    return verifyInput{
        SchemaVersion:   schemaVersion,
        ObjectType:      requestType,
        PublicKeyBase64: base64.StdEncoding.EncodeToString(publicKey),
        MessageBase64:   base64.StdEncoding.EncodeToString(message),
        SignatureBase64: base64.StdEncoding.EncodeToString(signature),
    }
}

func marshalRequest(t *testing.T, input verifyInput) []byte {
    t.Helper()
    data, err := json.Marshal(input)
    if err != nil {
        t.Fatal(err)
    }
    return data
}

func vector1(t *testing.T) verifyInput {
    return requestFor(
        mustHex(t, "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"),
        []byte{},
        mustHex(t, "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    )
}

func vector2(t *testing.T) verifyInput {
    return requestFor(
        mustHex(t, "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"),
        mustHex(t, "72"),
        mustHex(t, "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    )
}

func TestRFC8032Vectors(t *testing.T) {
    for index, input := range []verifyInput{vector1(t), vector2(t)} {
        valid, err := verifyRequest(input)
        if err != nil {
            t.Fatalf("vector %d error: %v", index+1, err)
        }
        if !valid {
            t.Fatalf("vector %d rejected", index+1)
        }
    }
}

func TestMutationsReject(t *testing.T) {
    base := vector2(t)
    tests := map[string]func(*verifyInput){
        "message": func(v *verifyInput) {
            msg, _ := base64.StdEncoding.DecodeString(v.MessageBase64)
            msg[0] ^= 1
            v.MessageBase64 = base64.StdEncoding.EncodeToString(msg)
        },
        "public_key": func(v *verifyInput) {
            key, _ := base64.StdEncoding.DecodeString(v.PublicKeyBase64)
            key[0] ^= 1
            v.PublicKeyBase64 = base64.StdEncoding.EncodeToString(key)
        },
        "signature": func(v *verifyInput) {
            sig, _ := base64.StdEncoding.DecodeString(v.SignatureBase64)
            sig[0] ^= 1
            v.SignatureBase64 = base64.StdEncoding.EncodeToString(sig)
        },
    }
    for name, mutate := range tests {
        t.Run(name, func(t *testing.T) {
            input := base
            mutate(&input)
            valid, err := verifyRequest(input)
            if err != nil {
                t.Fatalf("unexpected parse error: %v", err)
            }
            if valid {
                t.Fatal("mutated vector accepted")
            }
        })
    }
}

func TestJSONTagsMatchProtocol(t *testing.T) {
    data := string(marshalRequest(t, vector1(t)))
    for _, name := range []string{"schema_version", "object_type", "public_key_base64", "message_base64", "signature_base64"} {
        if !strings.Contains(data, `"`+name+`"`) {
            t.Fatalf("missing protocol field %s in %s", name, data)
        }
    }
    if strings.Contains(data, "SchemaVersion") {
        t.Fatalf("Go field names leaked into JSON: %s", data)
    }
}

func TestStrictRequestRoundTrip(t *testing.T) {
    data := marshalRequest(t, vector1(t))
    parsed, err := decodeStrictRequest(bytes.NewReader(data))
    if err != nil {
        t.Fatal(err)
    }
    valid, err := verifyRequest(parsed)
    if err != nil || !valid {
        t.Fatalf("valid request failed: valid=%v err=%v", valid, err)
    }
}

func TestDuplicateFieldRejected(t *testing.T) {
    raw := marshalRequest(t, vector1(t))
    duplicate := bytes.Replace(raw, []byte(`{"schema_version":"1.0"`), []byte(`{"schema_version":"1.0","schema_version":"1.0"`), 1)
    if _, err := decodeStrictRequest(bytes.NewReader(duplicate)); err == nil {
        t.Fatal("duplicate field accepted")
    }
}

func TestUnknownFieldRejected(t *testing.T) {
    raw := marshalRequest(t, vector1(t))
    mutated := bytes.Replace(raw, []byte(`}`), []byte(`,"extra":"x"}`), 1)
    if _, err := decodeStrictRequest(bytes.NewReader(mutated)); err == nil {
        t.Fatal("unknown field accepted")
    }
}

func TestNullAndTrailingDataRejected(t *testing.T) {
    raw := marshalRequest(t, vector1(t))
    nullValue := bytes.Replace(raw, []byte(`"message_base64":""`), []byte(`"message_base64":null`), 1)
    if _, err := decodeStrictRequest(bytes.NewReader(nullValue)); err == nil {
        t.Fatal("null accepted")
    }
    trailing := append(append([]byte{}, raw...), []byte(` {}`)...)
    if _, err := decodeStrictRequest(bytes.NewReader(trailing)); err == nil {
        t.Fatal("trailing JSON accepted")
    }
}

func TestOversizeRequestRejected(t *testing.T) {
    data := bytes.Repeat([]byte{' '}, maxRequestBytes+1)
    if _, err := decodeStrictRequest(bytes.NewReader(data)); err == nil {
        t.Fatal("oversize request accepted")
    }
}

func TestNoncanonicalAndWrongLengthBase64Rejected(t *testing.T) {
    input := vector1(t)
    input.PublicKeyBase64 = strings.TrimRight(input.PublicKeyBase64, "=")
    if _, err := verifyRequest(input); err == nil {
        t.Fatal("unpadded public key accepted")
    }
    input = vector1(t)
    input.SignatureBase64 = base64.StdEncoding.EncodeToString([]byte{1, 2, 3})
    if _, err := verifyRequest(input); err == nil {
        t.Fatal("wrong length signature accepted")
    }
}

func TestRunOutputIsClosedResult(t *testing.T) {
    var out bytes.Buffer
    if err := run(bytes.NewReader(marshalRequest(t, vector2(t))), &out); err != nil {
        t.Fatal(err)
    }
    var result map[string]any
    if err := json.Unmarshal(out.Bytes(), &result); err != nil {
        t.Fatal(err)
    }
    if len(result) != 3 || result["schema_version"] != schemaVersion || result["object_type"] != resultType || result["valid"] != true {
        t.Fatalf("unexpected result: %#v", result)
    }
}
