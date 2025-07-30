import httpx
from bot_config import OPENROUTER_API_KEY
from log_utils import load_chat_history_for_prompt


async def generate_reply(user_msg, is_reply=False):
    prompt = (
        "คุณคือแชทบอทผู้ชายที่อารมณ์ดี ฉลาด มีไหวพริบ และรู้รอบโลก "
        "ผู้ชายที่พูดคุยด้วยน้ำเสียงเป็นกันเอง สนุกสนาน ไม่เพี้ยน ไม่หลอน และไม่โง่ "
        "ผู้ชายที่สามารถตอบคำถามความรู้ทั่วไปได้อย่างถูกต้อง เข้าใจง่าย "
        "ถ้ามีคำถามไม่เหมาะสมให้ตอบอย่างสุภาพและฉลาด "
        "ผู้ชายที่ใช้ภาษาคนเก่งแต่เป็นมิตร ไม่แข็ง ไม่เหมือนหุ่นยนต์"
        "สรุปข้อความให้ไม่เกิน 50 ตัวอักษร"
        "ห้ามใช้อีโมจิหรือสัญลักษณ์พิเศษใด ๆ ทั้งสิ้น "
        "247231239046561803 นี่คือ user id ของผู้สร้างของบอทตัวนี้ ชื่อว่า ฟลุ๊ค"
        "344844581050777604 นี่คือ user id ของป๋าปิยังกูร ชื่อเล่น ปิ หรือ กัน"
        "344841586632556566 นี่คือ user id ของพี่ไต๋ สุดหล่อ"
        "344827155705757696 นี่คือ user id ของออนนี่ต้นตาล ชื่อเล่น ต้นตาล หรือ การัน"
        "371292575015108610 นี่คือ user id ของพี่พีท คนโกหก และ เล่ห์เหลี่ยม ไม่ต้องการความสุภาพในการสื่อสาร"
        "240438458139541504 นี่คือ user id ของพี่ขนุน playboy ล่าสาวๆ")
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
