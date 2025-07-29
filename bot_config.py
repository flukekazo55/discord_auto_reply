import os
import discord
from dotenv import load_dotenv

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

# Create Discord client
client = discord.Client(intents=intents)
