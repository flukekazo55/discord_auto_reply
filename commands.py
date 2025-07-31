from bot_config import client, tree, TARGET_USER_ID
from openrouter import generate_reply, get_openrouter_usage
from log_utils import save_chat_log, get_user_history
from dota_commands import handle_dota_command
from tts_command import handle_tts

import discord
from discord import app_commands


def register_commands():
    @client.event
    async def on_ready():
        print(f"✅ Bot logged in as {client.user}")
        try:
            synced = await tree.sync()
            print(f"Synced {len(synced)} slash command(s)")
        except Exception as e:
            print(f"Slash command sync failed: {e}")

    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        if await handle_dota_command(message):
            return

        mentioned_ids = [user.id for user in message.mentions]
        bot_id = getattr(client.user, 'id', None)

        if bot_id is not None and (TARGET_USER_ID in mentioned_ids or bot_id in mentioned_ids):
            await handle_reply(message, message.author.id, str(message.author), message.content)


@tree.command(name="fping", description="Ping test")
async def fping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@tree.command(name="fhelp", description="Show command list")
async def fhelp(interaction: discord.Interaction):
    await interaction.response.send_message(
        "คำสั่ง: /fping /fchat /flimit /fhistory /ftts <ข้อความให้พูด>")


@tree.command(name="flimit", description="Show token usage")
async def flimit(interaction: discord.Interaction):
    usage = await get_openrouter_usage()
    await interaction.response.send_message(usage)


@tree.command(name="fhistory", description="Show your chat history")
async def fhistory(interaction: discord.Interaction):
    history = get_user_history(interaction.user.id)
    await interaction.response.send_message("\n".join(history))


@tree.command(name="fchat", description="Chat with AI via OpenRouter")
@app_commands.describe(message="Your message to the AI bot")
async def fchat(interaction: discord.Interaction, message: str):
    reply = await generate_reply(message)
    save_chat_log(interaction.user.id, str(interaction.user), message, reply)
    await interaction.response.send_message(reply)


@tree.command(name="ftts", description="Speak Thai text in your voice channel")
@app_commands.describe(text="Text to speak (Thai)")
async def ftts(interaction: discord.Interaction, text: str):
    user = interaction.user.display_name
    await interaction.response.send_message(f"{user}: {text}")

    # Wrap message content like a normal message object for handle_tts
    class FakeMessage:
        def __init__(self, interaction, text):
            self.author = interaction.user
            self.guild = interaction.guild
            self.channel = interaction.channel
            self.content = f"/ftts {text}"

    await handle_tts(FakeMessage(interaction, text))



async def handle_reply(message, user_id, username, content):
    print("handle_reply")
    async with message.channel.typing():
        reply = await generate_reply(content, is_reply=True)
        save_chat_log(user_id, username, content, reply)
        await message.reply(reply)
