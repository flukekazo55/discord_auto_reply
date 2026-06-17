# Discord TTS Bot with AI Chat and Voice

A Python Discord bot (discord.py) that runs as an **always-on gateway bot**:

- Shows **online** in your server
- Speaks Thai text in voice channels via Google TTS + ffmpeg (`/ftts`)
- Chats with users via AI (`/fchat`, and `@mention` auto-reply) — Groq by default, any OpenAI-compatible provider
- Dota meta / counter lookups (`/fdm`, `/fdc`)
- Token usage and per-user chat history

> Hosting note: this is a long-lived gateway bot, so it needs an **always-on
> host** (here: Render via Docker). It cannot run on serverless platforms like
> Vercel — those can't keep the persistent Discord connection or run ffmpeg.

---

## Commands

| Command            | Description                              |
|--------------------|------------------------------------------|
| `/fping`           | Ping test                                |
| `/fhelp`           | Show command list                        |
| `/fchat <message>` | Chat with AI (also speaks)                |
| `/ftts <text>`     | Speak Thai text in your voice channel    |
| `/flimit`          | Show AI provider rate-limit / quota       |
| `/fhistory`        | Show your chat history                   |
| `/fdm`             | Dota meta picks by position              |
| `/fdc <hero>`      | Dota counters for a hero                 |
| `@mention` the bot | AI auto-reply                            |

---

## Configuration

Set these environment variables (a local `.env` file for development, or the
Render dashboard for deployment — see `.env.example`):

```bash
DISCORD_BOT_TOKEN=your_bot_token_here
TARGET_USER_ID=123456789012345678   # user whose @mentions trigger auto-reply
AI_API_KEY=your_ai_api_key          # Groq key from https://console.groq.com/keys
AI_MODEL=llama-3.3-70b-versatile
AI_BASE_URL=https://api.groq.com/openai/v1
```

Enable the **Message Content Intent** for your bot in the
[Discord Developer Portal](https://discord.com/developers/applications)
(Bot → Privileged Gateway Intents) — required for `@mention` auto-replies.

---

## Run locally

Requires Python 3.11+ and **ffmpeg** on your PATH (for voice).

```bash
pip install -r requirements.txt
python main.py
```

Or with Docker (ffmpeg included):

```bash
docker build -t discord-bot .
docker run --env-file .env discord-bot
```

---

## Deploy on Render

This repo ships a `Dockerfile` (installs ffmpeg + Opus) and `render.yaml`.

1. Push the repo to GitHub.
2. On [Render](https://render.com): **New → Web Service** → connect this repo.
   Render detects the `Dockerfile` / `render.yaml` automatically (Runtime:
   Docker, Plan: Free).
3. In **Environment**, add the three variables above.
4. Deploy. When it boots you'll see `Bot logged in as ...` in the logs and the
   bot goes **online** in Discord.

### Keep it awake (free tier)

Render's **free web service sleeps after ~15 minutes** of no inbound traffic,
which would disconnect the bot. The included keep-alive HTTP server (it answers
`GET /`) lets an external pinger hold it open:

1. Copy your Render service URL, e.g. `https://discord-auto-reply.onrender.com`.
2. Create a free monitor at [UptimeRobot](https://uptimerobot.com) (or
   cron-job.org) that does an **HTTP(s)** request to that URL every **5 minutes**.

That keeps the service — and therefore the bot — running 24/7 for free.

> Prefer not to use a pinger? Switch the service to a **Background Worker**
> (in `render.yaml` set `type: worker` and remove `healthCheckPath`). Workers
> never sleep, but are a paid plan.

---

## Notes

- Voice playback writes a temporary `tts_<guild>.mp3` and deletes it after
  playing.
- Chat history is stored in `chat_log.jsonl`. On Render's ephemeral disk this
  resets on each deploy/restart; attach a Render Disk or use a database if you
  need it to persist.

---

## Project structure

```
discord_auto_reply/
├── main.py            # Entry point: keep-alive server + run bot
├── bot_config.py      # Env loading + Discord client/intents
├── commands.py        # Slash commands + on_message auto-reply
├── tts_command.py     # Voice TTS (gTTS + ffmpeg)
├── ai.py              # AI provider integration (OpenAI-compatible)
├── system_prompt.txt  # Bot persona / system prompt (edit freely)
├── dota_commands.py   # Dota meta/counter scraping
├── log_utils.py       # Chat log + history
├── keep_alive.py      # Tiny Flask server for host health check / uptime ping
├── requirements.txt
├── Dockerfile         # ffmpeg + Opus + deps (for Render)
└── render.yaml        # Render service definition
```
