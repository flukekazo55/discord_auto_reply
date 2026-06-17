// Package handler implements the bot's HTTP surface:
//   - GET /        a human-readable health page;  GET /health  the same as JSON.
//   - POST /       the Discord Interactions endpoint (verified, then routed).
//
// It is mounted by the server entrypoint in cmd/server. Gateway-only features
// from the original bot (voice TTS, @mention auto-replies) are intentionally
// absent: they require a long-lived gateway connection and ffmpeg, which this
// HTTP-only deployment does not provide.
package handler

import (
	"context"
	"encoding/json"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/flukekazo55/discord_auto_reply/internal/chatlog"
	"github.com/flukekazo55/discord_auto_reply/internal/discord"
	"github.com/flukekazo55/discord_auto_reply/internal/envload"
	"github.com/flukekazo55/discord_auto_reply/internal/openrouter"
)

var requiredEnvVars = []string{
	"DISCORD_APPLICATION_ID",
	"DISCORD_PUBLIC_KEY",
	"DISCORD_BOT_TOKEN",
}

func init() {
	// On Vercel env vars come from project settings; locally we fall back to .env.
	envload.Load(".env")
}

// Handler routes every incoming HTTP request by method.
func Handler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		handleGet(w, r)
	case http.MethodPost:
		handleInteractions(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// ---- Health ----

type healthPayload struct {
	Status      string   `json:"status"`
	Ready       bool     `json:"ready"`
	Mode        string   `json:"mode"`
	MissingVars []string `json:"missing_env_vars"`
}

func missingEnvVars() []string {
	var missing []string
	for _, name := range requiredEnvVars {
		if os.Getenv(name) == "" {
			missing = append(missing, name)
		}
	}
	return missing
}

func buildHealthPayload() healthPayload {
	missing := missingEnvVars()
	status := "ready"
	if len(missing) > 0 {
		status = "config-incomplete"
	}
	return healthPayload{
		Status:      status,
		Ready:       len(missing) == 0,
		Mode:        "vercel-discord-interactions",
		MissingVars: missing,
	}
}

func handleGet(w http.ResponseWriter, r *http.Request) {
	payload := buildHealthPayload()

	if r.URL.Path == "/health" {
		writeJSON(w, http.StatusOK, payload)
		return
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := healthTemplate.Execute(w, payload); err != nil {
		http.Error(w, "template error", http.StatusInternalServerError)
	}
}

// ---- Discord Interactions ----

func handleInteractions(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	body, err := io.ReadAll(r.Body)
	if err != nil {
		log.Printf("interaction: read body failed: %v", err)
		http.Error(w, "cannot read body", http.StatusBadRequest)
		return
	}

	publicKey := os.Getenv("DISCORD_PUBLIC_KEY")
	signature := r.Header.Get("X-Signature-Ed25519")
	timestamp := r.Header.Get("X-Signature-Timestamp")

	hasSig := signature != "" && timestamp != ""
	log.Printf("interaction: received bodyLen=%d hasSig=%t pubKeyLen=%d",
		len(body), hasSig, len(publicKey))

	if publicKey == "" || !hasSig || !discord.Verify(publicKey, signature, timestamp, body) {
		log.Printf("interaction: REJECTED invalid signature (took %s)", time.Since(start))
		http.Error(w, "invalid request signature", http.StatusUnauthorized)
		return
	}

	var interaction discord.Interaction
	if err := json.Unmarshal(body, &interaction); err != nil {
		log.Printf("interaction: bad payload: %v", err)
		http.Error(w, "invalid interaction payload", http.StatusBadRequest)
		return
	}

	if interaction.Type == discord.TypePing {
		log.Printf("interaction: PING -> PONG (took %s)", time.Since(start))
		writeJSON(w, http.StatusOK, map[string]int{"type": discord.ResponsePong})
		return
	}

	if interaction.Type != discord.TypeApplicationCommand {
		log.Printf("interaction: unsupported type=%d (took %s)", interaction.Type, time.Since(start))
		respond(w, "Unsupported interaction type.")
		return
	}

	reply := routeCommand(r.Context(), &interaction)
	log.Printf("interaction: command=%q replyLen=%d (took %s)",
		interaction.Data.Name, len(reply), time.Since(start))
	respond(w, reply)
}

// routeCommand dispatches a slash command to its handler and returns the reply
// content.
func routeCommand(ctx context.Context, interaction *discord.Interaction) string {
	userID, username := interaction.ResolvedUser()

	switch interaction.Data.Name {
	case "fping":
		return "Pong!"

	case "fhelp":
		return "คำสั่ง: /fping /fchat /flimit /fhistory /ftts"

	case "flimit":
		return openrouter.GetUsage(ctx)

	case "fhistory":
		return joinLines(chatlog.GetUserHistory(userID, 5))

	case "fchat":
		message := interaction.StringOption("message")
		reply := openrouter.GenerateReply(ctx, message, false)
		if err := chatlog.Save(userID, username, message, reply); err != nil {
			// Logging is best-effort; don't fail the reply over it.
			os.Stderr.WriteString("chatlog save error: " + err.Error() + "\n")
		}
		return reply

	case "ftts":
		return "TTS/voice is not supported on Vercel. Use a persistent host for /ftts."

	default:
		return "Unknown command: " + interaction.Data.Name
	}
}

// ---- helpers ----

func respond(w http.ResponseWriter, content string) {
	writeJSON(w, http.StatusOK, map[string]any{
		"type": discord.ResponseChannelMessageWithSource,
		"data": map[string]string{"content": content},
	})
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func joinLines(lines []string) string {
	out := ""
	for i, line := range lines {
		if i > 0 {
			out += "\n"
		}
		out += line
	}
	return out
}

var healthTemplate = template.Must(template.New("health").Parse(healthHTML))

const healthHTML = `<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Discord Bot Health</title>
        <style>
            :root {
                color-scheme: light;
                --bg: #f4efe6;
                --panel: #fffaf2;
                --text: #1e1e1e;
                --muted: #625d52;
                --ok: #1f7a4d;
                --warn: #b25d00;
                --border: #dccfb8;
            }
            body {
                margin: 0;
                font-family: Georgia, "Times New Roman", serif;
                background: radial-gradient(circle at top, #fff7ea, var(--bg));
                color: var(--text);
            }
            .wrap { max-width: 760px; margin: 48px auto; padding: 0 20px; }
            .panel {
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 28px;
                box-shadow: 0 16px 40px rgba(70, 52, 24, 0.08);
            }
            h1 { margin: 0 0 10px; font-size: 2rem; }
            p { color: var(--muted); line-height: 1.5; }
            .badge { display: inline-block; margin: 12px 0 18px; padding: 8px 12px; border-radius: 999px; font-weight: 700; }
            .badge.ok { background: rgba(31, 122, 77, 0.12); color: var(--ok); }
            .badge.warn { background: rgba(178, 93, 0, 0.12); color: var(--warn); }
            ul { padding-left: 20px; }
            li { margin: 8px 0; }
            code { background: rgba(30, 30, 30, 0.06); padding: 2px 6px; border-radius: 6px; }
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="panel">
                <h1>Discord Bot Health Check</h1>
                <div class="badge {{if .Ready}}ok{{else}}warn{{end}}">{{if .Ready}}READY{{else}}CONFIG INCOMPLETE{{end}}</div>
                <p>This Vercel app serves Discord Interactions over HTTP. It does not run the long-lived Discord gateway or voice features.</p>
                <p><strong>Mode:</strong> {{.Mode}}</p>
                <p><strong>Health endpoint:</strong> <code>/health</code></p>
                {{if .MissingVars}}
                <p><strong>Missing environment variables:</strong></p>
                <ul>
                    {{range .MissingVars}}<li>{{.}}</li>{{end}}
                </ul>
                {{else}}
                <p>Required Discord environment variables are present.</p>
                {{end}}
            </div>
        </div>
    </body>
</html>`
