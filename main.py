import os
import discord
import httpx
from datetime import datetime

from keep_alive import keep_alive

# === Start Flask Keep-Alive Server ===
keep_alive()

# === Load Environment Variables ===
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# === Discord Intents Setup ===
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)

# === Message History Log ===
message_log = []


# === AI Response Function ===
async def generate_reply(user_msg: str, is_reply: bool = False) -> str:
    prompt = ("[PROMPT]")
    if is_reply:
        prompt += "[REPLY CHAT BEFORE]"

    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://discord.com",
                    "Content-Type": "application/json",
                },
                json={
                    "model":
                    "[YOUR AI MODEL]",
                    "messages": [{
                        "role": "system",
                        "content": prompt
                    }, {
                        "role": "user",
                        "content": user_msg
                    }]
                })
            result = response.json()
            print("\U0001F50D OpenRouter result:", result)
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("\u274C OpenRouter error:", e)
        return "[OPENROUTER HANDLE ERROR]"


# === On Bot Ready ===
@client.event
async def on_ready():
    print(f"\u2705 Bot logged in as {client.user}")


# === Main Bot Logic ===
@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()

    # === Command Handling ===
    if content.startswith("/fluke_ping"):
        await message.reply("Pong!")
        return

    elif content.startswith("/fluke_help"):
        help_text = ("\u2139\ufe0f command:\n"
                     "/fluke_ping - testing bot\n"
                     "/fluke_help - show all command\n"
                     "/fluke_chat - chat with this bot\n")

        await message.reply(help_text)
        return

    elif content.startswith("/fluke_chat"):
        try:
            async with message.channel.typing():
                reply = await generate_reply(content, True)
            await message.reply(reply)

        except Exception as e:
            print("\u274C Failed at /fluke_chat:", e)
            err = '[AI HANDLE ERROR]'
            await message.reply(err)
            return

    # === Message-based AI Reply ===
    should_reply = False
    is_reply = False

    mentioned_ids = [user.id for user in message.mentions]
    # Check if the bot is mentioned
    if TARGET_USER_ID in mentioned_ids or client.user.id in mentioned_ids:
        should_reply = True
        print(f"[Mention Trigger] {message.author.name}: {content}")

    if should_reply:
        try:
            async with message.channel.typing():
                reply = await generate_reply(content, True)
            await message.reply(reply)

        except Exception as e:
            print("\u274C Failed at reply chat:", e)
             err = '[AI HANDLE ERROR]'
            await message.reply(err)


# === Run Bot ===
client.run(DISCORD_BOT_TOKEN)
