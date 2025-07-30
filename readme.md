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

### Configuration

Edit the following file:
bot_config.py

```bash
DISCORD_BOT_TOKEN = "your_bot_token_here"
TARGET_USER_ID = 123456789012345678  # Replace with your own Discord user ID
```

If using /fchat, configure your OpenRouter API key in openrouter.py.

### Running the Bot

In the project directory, run:

```bash
python main.py
```

### Usage Example
Join a voice channel in your Discord server.

In a text channel, type:

```bash
/ftts Hello
```

###  Stopping the Bot
Press Ctrl + C in the terminal

Or close the terminal window

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
