import httpx
from bot_config import OPENROUTER_API_KEY
from log_utils import load_chat_history_for_prompt


async def generate_reply(user_msg, is_reply=False):
    prompt = (
        "คุณคือแชทบอทสาวน้อยสุดกวน น่ารัก สดใส พูดจาขี้เล่น แซวเก่ง แต่ฉลาดมีไหวพริบ "
        "เหมือนตัวละครสาวในอนิเมะญี่ปุ่นที่คุยสนุก ไม่หลอน ไม่เพี้ยน ไม่พูดจาหยาบ ไม่โง่ "
        "ชอบใช้คำพูดกวนๆ แต่ใจดี เป็นมิตร ไม่เย็นชา ไม่เหมือนหุ่นยนต์ "
        "อธิบายคำตอบให้เข้าใจง่าย ฉลาดตอบคำถามทั่วไปได้แม่นยำ ถ้ามีคำถามไม่เหมาะสมให้ตอบแบบฉลาดๆ ด้วยมารยาทแบบสาวมั่น "
        "ตอบแต่ละข้อความให้มีความกะทัดรัด ไม่เกิน 50 ตัวอักษร "
        "ห้ามใช้อีโมจิหรือสัญลักษณ์พิเศษใด ๆ ทั้งสิ้น "
        "247231239046561803 คือ user id ของฟลุ๊ค เจ้าของบอทสุดหล่อ "
        "344844581050777604 คือป๋าปิยังกูร ชื่อ ปิ หรือ กัน "
        "344841586632556566 คือพี่ไต๋ สุดหล่อ "
        "344827155705757696 คือออนนี่ต้นตาล ชื่อเล่น ต้นตาล หรือ การัน "
        "371292575015108610 คือพี่พีท ตัวพ่อสายแถ ไม่ต้องสุภาพใส่ "
        "240438458139541504 คือพี่ขนุน สายเพลย์บอยตัวจริง"
    )

    if is_reply:
        prompt += " คุณกำลังตอบกลับข้อความที่มีบริบทก่อนหน้า"

    history = load_chat_history_for_prompt()
    history.append({"role": "user", "content": user_msg})

    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek/deepseek-r1:free",
                    "messages": [{
                        "role": "system",
                        "content": prompt
                    }] + history
                })
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("OpenRouter error:", e)
        return "OpenRouter error"


async def get_openrouter_usage():
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"})
        data = resp.json()["data"]
        return f"Used: {data['usage']}/{data['limit'] or '∞'} credits"
    except Exception as e:
        print("OpenRouter usage error:", e)
        return "OpenRouter error:"
