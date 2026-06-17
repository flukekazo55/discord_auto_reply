import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

# Load .env file
load_dotenv()

def _get_int_env(name, default=None):
	value = os.getenv(name)
	if value in (None, ""):
		return default
	return int(value)


# Load runtime configuration from environment variables.
TARGET_USER_ID = _get_int_env("TARGET_USER_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID", "")
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "")

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.voice_states = True  # Important for TTS/voice features

# Create bot client and tree
client = commands.Bot(command_prefix="/", intents=intents)
tree = client.tree
