// Package discord holds Discord Interactions request verification and the shared
// types used by the HTTP handler.
package discord

import (
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
)

// Interaction type and response type constants from the Discord API.
const (
	TypePing               = 1
	TypeApplicationCommand = 2

	ResponsePong                     = 1
	ResponseChannelMessageWithSource = 4
)

// Verify checks an incoming Discord interaction's Ed25519 signature. publicKeyHex
// is the application's public key; signatureHex and timestamp come from the
// request headers; body is the raw request body.
func Verify(publicKeyHex, signatureHex, timestamp string, body []byte) bool {
	pubKey, err := hex.DecodeString(publicKeyHex)
	if err != nil || len(pubKey) != ed25519.PublicKeySize {
		return false
	}
	sig, err := hex.DecodeString(signatureHex)
	if err != nil || len(sig) != ed25519.SignatureSize {
		return false
	}

	message := append([]byte(timestamp), body...)
	return ed25519.Verify(ed25519.PublicKey(pubKey), message, sig)
}

// User is a Discord user as it appears in an interaction payload.
type User struct {
	ID         string `json:"id"`
	Username   string `json:"username"`
	GlobalName string `json:"global_name"`
}

// CommandOption is one option supplied to a slash command.
type CommandOption struct {
	Name  string          `json:"name"`
	Value json.RawMessage `json:"value"`
}

// Interaction is the subset of the Discord interaction payload this bot uses.
type Interaction struct {
	Type int `json:"type"`
	Data struct {
		Name    string          `json:"name"`
		Options []CommandOption `json:"options"`
	} `json:"data"`
	Member struct {
		User User `json:"user"`
	} `json:"member"`
	User User `json:"user"`
}

// ResolvedUser returns the interaction's user, preferring the guild member's
// user (present in guilds) over the top-level user (present in DMs).
func (i *Interaction) ResolvedUser() (id, name string) {
	u := i.Member.User
	if u.ID == "" {
		u = i.User
	}
	name = u.GlobalName
	if name == "" {
		name = u.Username
	}
	if name == "" {
		name = "Unknown user"
	}
	return u.ID, name
}

// StringOption returns the string value of a named option, or "" if absent.
func (i *Interaction) StringOption(name string) string {
	for _, opt := range i.Data.Options {
		if opt.Name == name {
			var s string
			if err := json.Unmarshal(opt.Value, &s); err == nil {
				return s
			}
		}
	}
	return ""
}
