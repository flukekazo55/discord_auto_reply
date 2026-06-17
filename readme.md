# Discord AI Chat Bot (Go + Vercel)

A Discord bot served as a **Vercel Go serverless function** over the Discord
Interactions HTTP API. It answers slash commands and chats via OpenRouter AI.

This is a Go port of the original Python bot, scoped to what can actually run on
Vercel. Gateway-only features (voice TTS, `@mention` auto-replies) were removed
because they need a long-lived process and `ffmpeg`, which serverless cannot
provide.

---

## Commands

| Command           | Description                                   |
|-------------------|-----------------------------------------------|
| `/fping`          | Ping test                                     |
| `/fhelp`          | Show command list                             |
| `/flimit`         | Show OpenRouter credit usage                  |
| `/fhistory`       | Show your recent chat history                 |
| `/fchat <message>`| Chat with AI via OpenRouter                   |
| `/ftts <text>`    | Returns a "not supported on Vercel" message   |

---

## Project structure

```
discord_auto_reply/
├── cmd/
│   ├── server/           # HTTP server entrypoint Vercel builds & runs
│   └── register/         # One-time slash-command registration CLI
├── internal/
│   ├── handler/          # HTTP handler: health page + Discord interactions
│   ├── discord/          # Ed25519 request verification + interaction types
│   ├── openrouter/       # OpenRouter chat-completion + usage API
│   ├── chatlog/          # JSONL chat history (ephemeral /tmp on Vercel)
│   └── envload/          # Minimal .env loader for local dev
└── go.mod
```

Vercel's Go runtime detects `cmd/server/main.go` as a web server, builds it, and
proxies all requests to it — no `vercel.json` is needed.

The bot uses only the Go standard library — there are no third-party
dependencies.

---

## Configuration

Set these environment variables (in Vercel project settings, or a local `.env`
file for development):

```bash
DISCORD_APPLICATION_ID=your_application_id
DISCORD_PUBLIC_KEY=your_public_key
DISCORD_BOT_TOKEN=your_bot_token
OPENROUTER_API_KEY=your_openrouter_key
```

---

## Deploying on Vercel

1. Import the repository into Vercel. Vercel auto-detects the Go web server at
   `cmd/server/main.go`.
2. Add the environment variables above in **Settings → Environment Variables**.
3. Deploy.
4. In the [Discord Developer Portal](https://discord.com/developers/applications),
   set the **Interactions Endpoint URL** to your deployment, e.g.
   `https://your-project.vercel.app/`. Discord sends a signed PING to verify it;
   the handler must already be deployed with `DISCORD_PUBLIC_KEY` set.
5. Register the slash commands once:

   ```bash
   go run ./cmd/register
   ```

### Health check

- `GET /`        → human-readable health page (shows missing env vars)
- `GET /health`  → JSON status payload

---

## Limitations on Vercel

- **No voice / TTS.** Discord voice connections and `ffmpeg` need a long-lived
  process. `/ftts` returns an explanatory message.
- **No `@mention` auto-replies.** Those require a persistent Discord gateway
  connection, which serverless cannot hold open.
- **Ephemeral history.** Chat logs are written to `/tmp` and are wiped on cold
  starts and redeploys. For durable history, move `internal/chatlog` to a
  database or Vercel KV/Blob.
- **`/fchat` timeouts.** Discord expects an interaction response within ~3s. A
  slow OpenRouter model can exceed that. For reliable long responses, use a
  deferred response with a follow-up webhook from a persistent worker.

---

## Local development

```bash
# Build everything
go build ./...

# Run tests
go test ./...

# Run the server locally (reads .env, listens on $PORT, default 3000)
go run ./cmd/server
```

---

## Stopping / removing

Delete the project from Vercel, or remove the Interactions Endpoint URL in the
Discord Developer Portal to stop routing interactions to it.
