// Command register performs a one-time global registration of the bot's slash
// commands with Discord. Run it after deploying or whenever the command set
// changes:
//
//	go run ./cmd/register
//
// It reads DISCORD_APPLICATION_ID and DISCORD_BOT_TOKEN from the environment
// (or a local .env file).
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/flukekazo55/discord_auto_reply/internal/envload"
)

type commandOption struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Type        int    `json:"type"`
	Required    bool   `json:"required,omitempty"`
}

type command struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	Type        int             `json:"type"`
	Options     []commandOption `json:"options,omitempty"`
}

func buildCommands() []command {
	return []command{
		{Name: "fping", Description: "Ping test", Type: 1},
		{Name: "fhelp", Description: "Show command list", Type: 1},
		{Name: "flimit", Description: "Show token usage", Type: 1},
		{Name: "fhistory", Description: "Show your chat history", Type: 1},
		{
			Name:        "fchat",
			Description: "Chat with AI via OpenRouter",
			Type:        1,
			Options: []commandOption{
				{Name: "message", Description: "Your message to the AI bot", Type: 3, Required: true},
			},
		},
		{
			Name:        "ftts",
			Description: "Explain Vercel voice limitation",
			Type:        1,
			Options: []commandOption{
				{Name: "text", Description: "Text to speak", Type: 3, Required: true},
			},
		},
	}
}

func main() {
	envload.Load(".env")

	appID := os.Getenv("DISCORD_APPLICATION_ID")
	botToken := os.Getenv("DISCORD_BOT_TOKEN")
	if appID == "" || botToken == "" {
		log.Fatal("DISCORD_APPLICATION_ID and DISCORD_BOT_TOKEN are required")
	}

	body, err := json.Marshal(buildCommands())
	if err != nil {
		log.Fatalf("encode commands: %v", err)
	}

	url := fmt.Sprintf("https://discord.com/api/v10/applications/%s/commands", appID)
	req, err := http.NewRequest(http.MethodPut, url, bytes.NewReader(body))
	if err != nil {
		log.Fatalf("build request: %v", err)
	}
	req.Header.Set("Authorization", "Bot "+botToken)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		log.Fatalf("request failed: %v", err)
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= http.StatusBadRequest {
		log.Fatalf("Discord returned %d: %s", resp.StatusCode, respBody)
	}

	var registered []json.RawMessage
	if err := json.Unmarshal(respBody, &registered); err != nil {
		log.Fatalf("decode response: %v", err)
	}
	fmt.Printf("Registered %d global command(s)\n", len(registered))
}
