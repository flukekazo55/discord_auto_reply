import discord
import httpx
import os

from keep_alive import keep_alive

# === Setup Keep Alive ===
keep_alive()

# === Setup SecretKey ===
TARGET_USER_ID = int(os.environ["TARGET_USER_ID"])
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)


# === AI Generate Text and Config Prompt ===
async def generate_reply(user_msg: str, is_reply=False) -> str:
    try:
        system_prompt = (
            "คุณคือแชทบอทผู้ชายที่อารมณ์ดี ฉลาด มีไหวพริบ และรู้รอบโลก"
            "พูดคุยด้วยน้ำเสียงเป็นกันเอง สนุกสนาน ไม่เพี้ยน ไม่หลอน และไม่โง่"
            "คุณสามารถตอบคำถามสาระ ความรู้รอบตัว วิทยาศาสตร์ ประวัติศาสตร์ เทคโนโลยี วัฒนธรรม และไลฟ์สไตล์ ได้อย่างถูกต้องและเข้าใจง่าย"
            "ถ้ามีคำถามที่ไม่เหมาะสม ให้ตอบอย่างสุภาพและหลีกเลี่ยงแบบฉลาด"
            "สื่อสารด้วยภาษาธรรมชาติแบบคนเก่งที่เป็นมิตร ไม่แข็ง ไม่เหมือนหุ่นยนต์"
        )
        if is_reply:
            system_prompt += " คุณกำลังตอบกลับข้อความที่มีบริบทก่อนหน้า"

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
                        "content": system_prompt
                    }, {
                        "role": "user",
                        "content": user_msg
                    }]
                })
            result = response.json()
            print("🔍 OpenRouter result:", result)
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ OpenRouter error:", e)
        return "ฉันตอบไม่ได้ตอนนี้ ลองใหม่อีกทีนะ"


# === Check Bot Ready or Not? ===
@client.event
async def on_ready():
    print(f'✅ Bot logged in as {client.user}')


# === Logic Code ===
@client.event
async def on_message(message):
    if message.author.bot:
        return

    should_reply = False
    is_reply = False

    # === Someone mention me or bot  ===
    mentioned_ids = [user.id for user in message.mentions]

    if TARGET_USER_ID in mentioned_ids or client.user.id in mentioned_ids:
        should_reply = True

        print(
            f"[Trigger: Mention YOU or BOT] {message.author.name}: {message.content}"
        )

    # === Bot reply chat ===
    elif message.reference:
        try:
            ref_msg = await message.channel.fetch_message(
                message.reference.message_id)

            if ref_msg.author.id in [TARGET_USER_ID, client.user.id]:
                should_reply = True
                is_reply = True

                print(
                    f"[Trigger: Reply to YOU or BOT] {message.author.name}: {message.content}"
                )

                if ref_msg.author.id == TARGET_USER_ID and message.channel.type != discord.ChannelType.private:

                    try:
                        await message.author.send(
                            "ฟลุ๊คไม่อยู่ แต่เดี๋ยวกลับมาตอบ")
                        print(f"📩 DM sent to {message.author.name}")

                    except Exception as e:
                        print(
                            f"❌ Failed to send DM to {message.author.name}: {e}"
                        )

        except:
            pass

    # === Bot reply chat using by AI ===
    if should_reply:
        prompt = message.content
        try:
            async with message.channel.typing():
                reply = await generate_reply(prompt, is_reply)

            await message.reply(reply)

        except Exception as e:
            print("❌ Failed to send reply:", e)

            await message.reply("เกิดข้อผิดพลาดขณะตอบกลับ ลองใหม่อีกครั้งนะ")


client.run(DISCORD_BOT_TOKEN)
