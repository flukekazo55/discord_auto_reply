import os
import discord
import httpx

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

# === AI Response Function ===
async def generate_reply(user_msg: str, is_reply: bool = False) -> str:
    prompt = (
        "คุณคือแชทบอทผู้ชายที่อารมณ์ดี ฉลาด มีไหวพริบ และรู้รอบโลก "
        "พูดคุยด้วยน้ำเสียงเป็นกันเอง สนุกสนาน ไม่เพี้ยน ไม่หลอน และไม่โง่ "
        "สามารถตอบคำถามความรู้ทั่วไปได้อย่างถูกต้อง เข้าใจง่าย "
        "ถ้ามีคำถามไม่เหมาะสมให้ตอบอย่างสุภาพและฉลาด "
        "ใช้ภาษาคนเก่งแต่เป็นมิตร ไม่แข็ง ไม่เหมือนหุ่นยนต์"
    )
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
                    "model": "deepseek/deepseek-r1:free",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_msg}
                    ]
                }
            )
            result = response.json()
            print("🔍 OpenRouter result:", result)
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ OpenRouter error:", e)
        return "ฉันตอบไม่ได้ตอนนี้ ลองใหม่อีกทีนะ"

# === On Bot Ready ===
@client.event
async def on_ready():
    print(f"✅ Bot logged in as {client.user}")

# === Main Bot Logic ===
@client.event
async def on_message(message):
    if message.author.bot:
        return

    should_reply = False
    is_reply = False
    mentioned_ids = [user.id for user in message.mentions]

    # === If Mentioned ===
    if TARGET_USER_ID in mentioned_ids or client.user.id in mentioned_ids:
        should_reply = True
        print(f"[Mention Trigger] {message.author.name}: {message.content}")

    # === If Reply to Message ===
    elif message.reference:
        try:
            ref_msg = await message.channel.fetch_message(message.reference.message_id)
            if ref_msg.author.id in [TARGET_USER_ID, client.user.id]:
                should_reply = True
                is_reply = True
                print(f"[Reply Trigger] {message.author.name}: {message.content}")

                # Send DM if replying to you (not bot)
                if ref_msg.author.id == TARGET_USER_ID and message.channel.type != discord.ChannelType.private:
                    try:
                        await message.author.send("ฟลุ๊คไม่อยู่ แต่เดี๋ยวกลับมาตอบ")
                        print(f"📩 DM sent to {message.author.name}")
                    except Exception as e:
                        print(f"❌ Failed to send DM: {e}")
        except:
            pass

    # === Send AI Reply ===
    if should_reply:
        try:
            async with message.channel.typing():
                reply = await generate_reply(message.content, is_reply)
            await message.reply(reply)
        except Exception as e:
            print("❌ Failed to send reply:", e)
            await message.reply("เกิดข้อผิดพลาดขณะตอบกลับ ลองใหม่อีกครั้งนะ")

# === Run the Bot ===
client.run(DISCORD_BOT_TOKEN)
