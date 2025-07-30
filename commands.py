from bot_config import client, TARGET_USER_ID
from openrouter import generate_reply, get_openrouter_usage
from log_utils import save_chat_log, get_user_history
from dota_commands import handle_dota_command
from tts_command import handle_tts

def register_commands():

    @client.event
    async def on_ready():
        print(f"Bot logged in as {client.user}")

    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        if await handle_dota_command(message):
            return

        content = message.content.strip()
        user_id = message.author.id
        username = str(message.author)

        mentioned_ids = [user.id for user in message.mentions]
        bot_id = getattr(client.user, 'id', None)

        # Ping Test
        if content.startswith("/fping"):
            await message.reply("Pong!")

        # Help
        elif content.startswith("/fhelp"):
            await message.reply(
                "คำสั่ง: /fping /fchat /flimit /fhistory /ftts <message>")

        # Token usage limit
        elif content.startswith("/flimit"):
            usage = await get_openrouter_usage()
            await message.reply(usage)

        # Chat history
        elif content.startswith("/fhistory"):
            history = get_user_history(user_id)
            await message.reply("\n".join(history))

        # AI Chat
        elif content.startswith("/fchat"): 
            await handle_reply(message, user_id, username, content)

        # Text-to-Speech (Replit-safe: sends .mp3 instead of speaking)
        elif content.startswith("/ftts"):
            await handle_tts(message)
            
        # Handle mentions
        elif bot_id is not None and (TARGET_USER_ID in mentioned_ids or bot_id in mentioned_ids):
            await handle_reply(message, user_id, username, content)


async def handle_reply(message, user_id, username, content):
    print("handle_reply")
    async with message.channel.typing():
        reply = await generate_reply(content, is_reply=True)
        save_chat_log(user_id, username, content, reply)
        await message.reply(reply)
