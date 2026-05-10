# Discord TTS Bot with AI Chat and Voice Support

This is a Python-based Discord bot that can:
- Speak Thai text in voice channels using Google TTS (gTTS)
- Chat with users via OpenRouter AI
- Show token usage statistics
- Display individual user chat history

---

## Features

| Command           | Description                             |
|------------------|-----------------------------------------|
| /fping       | Ping test                               |
| /fchat       | Chat with AI via OpenRouter             |
| /flimit      | Show current token usage                |
| /fhistory    | Show chat history for the current user  |
| /ftts <text> | Speak the given Thai text in voice      |

---

## Requirements

- Python 3.10 or higher
- Discord bot token
- ffmpeg installed and in PATH
- Libraries: `discord.py`, `gTTS`, `PyNaCl`

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/discord_auto_reply.git
cd discord_auto_reply
```

### 2. Install Python dependencies

```bash
pip install -U "discord.py[voice]" gTTS PyNaCl
```

### 3. Install ffmpeg (Windows)

1. Download the static zip build from: https://www.gyan.dev/ffmpeg/builds/
2. Choose ffmpeg-release-essentials.zip
3. Extract to: C:\ffmpeg
4. Add C:\ffmpeg\bin to your system environment variable PATH
5. Open a new terminal and test with:

```bash
ffmpeg -version
```

You should see version information printed if installation is successful.

---

### Configuration

Configure these environment variables:

```bash
DISCORD_BOT_TOKEN="your_bot_token_here"
DISCORD_APPLICATION_ID="your_application_id"
DISCORD_PUBLIC_KEY="your_public_key"
OPENROUTER_API_KEY="your_openrouter_key"
TARGET_USER_ID=123456789012345678
```

You can place those values in a local `.env` file for development, or configure them as environment variables in Vercel.

---

### Running the Bot

In the project directory, run:

```bash
python main.py
```

---

## Deploying on Vercel

This repository now supports a Vercel deployment through Discord Interactions at the HTTP endpoint served by [api/index.py](api/index.py).

### Important limitations on Vercel

- Mention-based auto replies will not run on Vercel because `on_message` requires a persistent Discord gateway connection.
- Voice and `/ftts` playback will not run on Vercel because Discord voice connections and `ffmpeg` need a long-lived process.
- Chat history stored in `chat_log.jsonl` becomes temporary on Vercel because serverless file storage is ephemeral. For persistent history, move logs to a database or Vercel Blob.
- `/fchat` can still time out on Vercel if OpenRouter responds too slowly for Discord's interaction timeout window. For reliable long AI responses, use a background worker or a persistent host.

### Vercel setup

1. Import the repository into Vercel.
2. Set these environment variables in the Vercel project:

```bash
DISCORD_APPLICATION_ID=your_application_id
DISCORD_PUBLIC_KEY=your_public_key
DISCORD_BOT_TOKEN=your_bot_token
OPENROUTER_API_KEY=your_openrouter_key
TARGET_USER_ID=123456789012345678
```

3. Deploy.
4. Set the Discord Interactions URL in the Discord Developer Portal to your Vercel URL, for example `https://your-project.vercel.app/`.
5. Register slash commands once with:

```bash
python register_vercel_commands.py
```

### Commands available on Vercel

- `/fping`
- `/fhelp`
- `/flimit`
- `/fhistory`
- `/fchat`

`/ftts` returns a limitation message on Vercel instead of joining voice.

---

### Usage Example
Join a voice channel in your Discord server.

In a text channel, type:

```bash
/ftts Hello
```

---

###  Stopping the Bot
Press Ctrl + C in the terminal

Or close the terminal window

---

### Project Structure

```bash
discord_auto_reply/
├── bot_config.py        # Token and bot instance config
├── main.py              # Entry point for running the bot
├── commands.py          # Event and command registration
├── tts_command.py       # Voice TTS handler
├── openrouter.py        # AI integration via OpenRouter
├── log_utils.py         # Chat log saving and history
├── requirements.txt     # Optional dependency list
```
