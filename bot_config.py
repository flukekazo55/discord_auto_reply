import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

# Load .env file
load_dotenv()

# Load tokens
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.voice_states = True  # Important for TTS/voice features

# Create bot client and tree
client = commands.Bot(command_prefix="/", intents=intents)
tree = client.tree
