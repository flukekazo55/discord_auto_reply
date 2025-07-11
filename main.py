import discord
import httpx
import os

# === Setup ===
TARGET_USER_ID = int(os.environ["TARGET_USER_ID"])
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)


async def generate_reply(user_msg: str) -> str:
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
                        "role":
                        "system",
                        "content":
                        ("คุณเป็นแชทบอทที่พูดจาสั้นๆ ตรงประเด็น และกวนตีนเล็กน้อย "
                         "ไม่ต้องสุภาพมาก ตอบแบบคนอารมณ์ดี กวนแต่ไม่หยาบคาย ใช้ภาษาธรรมดาแบบวัยรุ่นไทย"
                         )
                    }, {
                        "role": "user",
                        "content": user_msg
                    }]
                })
            result = response.json()
            print("🔍 OpenRouter result:", result)
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("OpenRouter error:", e)
        return "ฉันตอบไม่ได้ตอนนี้ ลองใหม่อีกทีนะ"


@client.event
async def on_ready():
    print(f'Bot logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author.bot:
        return

    should_reply = any(m.id == TARGET_USER_ID for m in message.mentions)

    if message.reference and not should_reply:
        try:
            ref_msg = await message.channel.fetch_message(
                message.reference.message_id)
            should_reply = ref_msg.author.id == TARGET_USER_ID
        except:
            pass

    if should_reply:
        prompt = message.content
        print(f"[Trigger] {message.author.name}: {prompt}")

        try:
            async with message.channel.typing():
                reply = await generate_reply(prompt)
            await message.reply(reply)
        except Exception as e:
            print("Failed to send reply:", e)
            await message.reply("เกิดข้อผิดพลาดขณะตอบกลับ ลองใหม่อีกครั้งนะ")


client.run(DISCORD_BOT_TOKEN)
