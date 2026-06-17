package handler

import (
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// signedRequest builds a POST request signed with priv so the handler accepts it.
func signedRequest(t *testing.T, priv ed25519.PrivateKey, body string) *http.Request {
	t.Helper()
	timestamp := "1700000000"
	sig := ed25519.Sign(priv, []byte(timestamp+body))

	req := httptest.NewRequest(http.MethodPost, "/", strings.NewReader(body))
	req.Header.Set("X-Signature-Ed25519", hex.EncodeToString(sig))
	req.Header.Set("X-Signature-Timestamp", timestamp)
	return req
}

func TestHandlePingPong(t *testing.T) {
	pub, priv, _ := ed25519.GenerateKey(nil)
	t.Setenv("DISCORD_PUBLIC_KEY", hex.EncodeToString(pub))

	req := signedRequest(t, priv, `{"type":1}`)
	rr := httptest.NewRecorder()
	Handler(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rr.Code)
	}
	var resp map[string]int
	if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if resp["type"] != 1 {
		t.Fatalf("type = %d, want 1 (PONG)", resp["type"])
	}
}

func TestHandleRejectsBadSignature(t *testing.T) {
	pub, _, _ := ed25519.GenerateKey(nil)
	t.Setenv("DISCORD_PUBLIC_KEY", hex.EncodeToString(pub))

	req := httptest.NewRequest(http.MethodPost, "/", strings.NewReader(`{"type":1}`))
	req.Header.Set("X-Signature-Ed25519", hex.EncodeToString(make([]byte, ed25519.SignatureSize)))
	req.Header.Set("X-Signature-Timestamp", "1700000000")

	rr := httptest.NewRecorder()
	Handler(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("status = %d, want 401", rr.Code)
	}
}

func TestRouteFping(t *testing.T) {
	pub, priv, _ := ed25519.GenerateKey(nil)
	t.Setenv("DISCORD_PUBLIC_KEY", hex.EncodeToString(pub))

	body := `{"type":2,"data":{"name":"fping"},"member":{"user":{"id":"1","username":"u"}}}`
	rr := httptest.NewRecorder()
	Handler(rr, signedRequest(t, priv, body))

	if rr.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rr.Code)
	}
	var resp struct {
		Type int `json:"type"`
		Data struct {
			Content string `json:"content"`
		} `json:"data"`
	}
	if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if resp.Type != 4 || resp.Data.Content != "Pong!" {
		t.Fatalf("got type=%d content=%q, want type=4 content=Pong!", resp.Type, resp.Data.Content)
	}
}

func TestHealthJSON(t *testing.T) {
	t.Setenv("DISCORD_APPLICATION_ID", "")
	t.Setenv("DISCORD_PUBLIC_KEY", "")
	t.Setenv("DISCORD_BOT_TOKEN", "")

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rr := httptest.NewRecorder()
	Handler(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rr.Code)
	}
	body, _ := io.ReadAll(rr.Body)
	if !strings.Contains(string(body), "config-incomplete") {
		t.Fatalf("expected config-incomplete status, got %s", body)
	}
}
