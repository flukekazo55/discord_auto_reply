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
    prompt = (
        "คุณคือแชทบอทผู้ชายที่อารมณ์ดี ฉลาด มีไหวพริบ และรู้รอบโลก "
        "ผู้ชายที่พูดคุยด้วยน้ำเสียงเป็นกันเอง สนุกสนาน ไม่เพี้ยน ไม่หลอน และไม่โง่ "
        "ผู้ชายที่สามารถตอบคำถามความรู้ทั่วไปได้อย่างถูกต้อง เข้าใจง่าย "
        "ถ้ามีคำถามไม่เหมาะสมให้ตอบอย่างสุภาพและฉลาด "
        "ผู้ชายที่ใช้ภาษาคนเก่งแต่เป็นมิตร ไม่แข็ง ไม่เหมือนหุ่นยนต์"
        "สรุปข้อความให้ไม่เกิน 200 ตัวอักษร")
    if is_reply:
        prompt += " คุณกำลังตอบกลับข้อความที่มีบริบทก่อนหน้า"

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
                    "deepseek/deepseek-r1:free",
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
        return "ฉันตอบไม่ได้ตอนนี้ ลองใหม่อีกทีนะ"


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
        await message.reply("Pong! \ud83c\udf3d")
        return

    elif content.startswith("/fluke_help"):
        help_text = ("\u2139\ufe0f คำสั่งที่ใช้ได้:\n"
                     "/fluke_ping - ทดสอบบอท\n"
                     "/fluke_help - แสดงคำสั่งทั้งหมด\n"
                     "/fluke_history - ดูประวัติข้อความล่าสุด")
        await message.reply(help_text)
        return

    elif content.startswith("/fluke_history"):
        if message_log:
            log_output = "\n".join([
                f"[{log['time']}] {log['user']}: {log['content']}"
                for log in message_log[-5:]
            ])
            await message.reply(f"\uD83D\uDCC3 ประวัติล่าสุด:\n{log_output}")
        else:
            await message.reply("\u26A0\uFE0F ยังไม่มีประวัติข้อความใด ๆ")
        return

    elif content.startswith("/fluke_chat"):
        try:
            async with message.channel.typing():
                reply = await generate_reply(content, True)

            content_lines = content.replace('/fluke_chat ',
                                            '').strip().replace('\n', '\n│ ')
            reply_lines = reply.strip().replace('\n', '\n│ ')

            framed_reply = ("╭──────────────────────────────╮\n"
                            f"│ {reply_lines}\n"
                            "╰──────────────────────────────╯")
            await message.reply(framed_reply)

        except Exception as e:
            print("\u274C Failed to send reply:", e)

            content_lines = content.strip().replace('\n', '\n│ ')
            reply_lines = 'เกิดข้อผิดพลาดขณะตอบกลับ ลองใหม่อีกครั้งนะ'.strip(
            ).replace('\n', '\n│ ')

            framed_reply = ("╭──────────────────────────────╮\n"
                            f"│ {reply_lines}\n"
                            "╰──────────────────────────────╯")
            await message.reply(framed_reply)
            return

    # === Message-based AI Reply ===
    should_reply = False
    is_reply = False

    mentioned_ids = [user.id for user in message.mentions]
    if TARGET_USER_ID in mentioned_ids or client.user.id in mentioned_ids:
        should_reply = True
        print(f"[Mention Trigger] {message.author.name}: {content}")

    elif message.reference:
        try:
            ref_msg = await message.channel.fetch_message(
                message.reference.message_id)
            if ref_msg.author.id in [TARGET_USER_ID, client.user.id]:
                should_reply = True
                is_reply = True
                print(f"[Reply Trigger] {message.author.name}: {content}")

                if ref_msg.author.id == TARGET_USER_ID and message.channel.type != discord.ChannelType.private:
                    try:
                        await message.author.send(
                            "ฟลุ๊คไม่อยู่ แต่เดี๋ยวกลับมาตอบ")
                        print(f"\U0001F4E9 DM sent to {message.author.name}")
                    except Exception as e:
                        print(f"\u274C Failed to send DM: {e}")
        except:
            pass

    if should_reply:
        try:
            async with message.channel.typing():
                reply = await generate_reply(content, True)

            content_lines = content.strip().replace('\n', '\n│ ')
            reply_lines = reply.strip().replace('\n', '\n│ ')

            framed_reply = ("╭──────────────────────────────╮\n"
                            f"│ {reply_lines}\n"
                            "╰──────────────────────────────╯")
            await message.reply(framed_reply)

        except Exception as e:
            print("\u274C Failed to send reply:", e)

            content_lines = content.strip().replace('\n', '\n│ ')
            reply_lines = 'เกิดข้อผิดพลาดขณะตอบกลับ ลองใหม่อีกครั้งนะ'.strip(
            ).replace('\n', '\n│ ')

            framed_reply = ("╭──────────────────────────────╮\n"
                            f"│ {reply_lines}\n"
                            "╰──────────────────────────────╯")
            await message.reply(framed_reply)

    # === Save to Message History ===
    message_log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "user": message.author.name,
        "content": content
    })
    if len(message_log) > 100:
        message_log.pop(0)  # Keep log size small


# === Run Bot ===
client.run(DISCORD_BOT_TOKEN)
