import os
import json
import asyncio
import httpx
from dotenv import load_dotenv
from log_utils import load_chat_history_for_prompt


load_dotenv()


# --- AI provider config (OpenAI-compatible) ---
# Defaults target Groq (free). Override any of these in .env to switch providers
# without touching code:
#   AI_BASE_URL  e.g. https://generativelanguage.googleapis.com/v1beta/openai
#   AI_API_KEY   the provider's API key
#   AI_MODEL     a model id valid for that provider
def _base_url():
    return os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")


def _api_key():
    return os.getenv("AI_API_KEY", "")


def _model():
    return os.getenv("AI_MODEL", "llama-3.3-70b-versatile")


# The bot persona / system prompt. Edit system_prompt.txt to change how the bot
# talks — no code change and no restart needed (it is re-read on every message).
# This constant is only the fallback used if that file is missing.
DEFAULT_SYSTEM_PROMPT = (
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

# system_prompt.txt lives next to this file, so it's found regardless of CWD.
# Override the path with SYSTEM_PROMPT_FILE if you want.
_DEFAULT_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")


def _load_system_prompt():
    path = os.getenv("SYSTEM_PROMPT_FILE", _DEFAULT_PROMPT_PATH)
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
            if text:
                return text
    except OSError:
        pass
    return DEFAULT_SYSTEM_PROMPT


# Most recent rate-limit info, captured from response headers so /flimit can show
# it without spending an extra request.
_RATE_LIMIT_HEADERS = (
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
)
_last_rate_limit = {}


def _capture_rate_limit(headers):
    for key in _RATE_LIMIT_HEADERS:
        if key in headers:
            _last_rate_limit[key] = headers[key]


def _search_enabled():
    return os.getenv("ENABLE_WEB_SEARCH", "true").strip().lower() not in ("0", "false", "no")


def _web_search(query, max_results=4):
    """Free web search via DuckDuckGo (no API key). Returns a compact text block.
    Snippets are kept short to limit tokens (Groq free-tier TPM is small)."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        print("web_search error:", e)
        return "ค้นเว็บไม่สำเร็จ"
    if not results:
        return "ไม่พบผลการค้นหา"
    return "\n\n".join(
        f"{r.get('title', '')}\n{(r.get('body', '') or '')[:200]}\n{r.get('href', '')}"
        for r in results
    )


# Tool the model can call to look things up on the web.
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "ค้นหาข้อมูลปัจจุบันจากอินเทอร์เน็ต เช่น ข่าว ราคา ผลกีฬา สภาพอากาศ "
            "หรือเหตุการณ์ล่าสุด ใช้เมื่อผู้ใช้ถามสิ่งที่ต้องใช้ข้อมูลอัปเดตหรือหลังปี 2024"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "คำค้นหา (ภาษาไทยหรืออังกฤษ)"}
            },
            "required": ["query"],
        },
    },
}


def _error_message(status):
    if status == 429:
        return "AI โดนจำกัดอัตราการใช้ (429) รอสักครู่แล้วลองใหม่"
    if status in (401, 403):
        return "AI auth ไม่ผ่าน (ตรวจสอบ AI_API_KEY ใน .env)"
    if status == 404:
        return "AI ไม่พบโมเดล (404) ตรวจสอบ AI_MODEL ใน .env"
    if status == 413:
        return "คำขอใหญ่เกินไป (413) — ลด system_prompt/ประวัติ หรือเปลี่ยนโมเดล"
    return f"AI error ({status})"


async def generate_reply(user_msg, is_reply=False):
    prompt = _load_system_prompt()
    if is_reply:
        prompt += " คุณกำลังตอบกลับข้อความที่มีบริบทก่อนหน้า"
    if _search_enabled():
        # Force the model to actually search for current info instead of replying
        # "ไม่ชัวร์" or telling the user to look it up themselves.
        prompt += (
            "\n\nเมื่อผู้ใช้ถามข้อมูลปัจจุบัน ข่าว ราคา ผลกีฬา สภาพอากาศ หรือเหตุการณ์ล่าสุด "
            "ให้เรียกเครื่องมือ web_search ค้นหาก่อนตอบเสมอ ห้ามบอกให้ผู้ใช้ไปค้นเอง "
            "และห้ามตอบว่าไม่รู้ถ้ายังไม่ได้ค้น"
        )

    api_key = _api_key()
    if not api_key:
        return "ยังไม่ได้ตั้ง AI_API_KEY ใน .env"

    model = _model()
    messages = [{"role": "system", "content": prompt}]
    messages += load_chat_history_for_prompt()
    messages.append({"role": "user", "content": user_msg})

    tools = [WEB_SEARCH_TOOL] if _search_enabled() else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as http:
            # The model may ask to web-search; loop so we can run the tool and let
            # it answer with the results.
            msg = {}
            for _ in range(4):
                payload = {"model": model, "messages": messages}
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

                resp = await http.post(
                    f"{_base_url()}/chat/completions", headers=headers, json=payload
                )
                _capture_rate_limit(resp.headers)
                if resp.status_code >= 400:
                    print(f"AI error {resp.status_code} for model '{model}': {resp.text[:500]}")
                    return _error_message(resp.status_code)

                msg = resp.json()["choices"][0]["message"]
                tool_calls = msg.get("tool_calls")
                if not tool_calls:
                    return msg.get("content") or "ตอบไม่ได้ตอนนี้"

                # Record the assistant's tool request, then run each tool call.
                messages.append(msg)
                for call in tool_calls:
                    fn = call.get("function", {})
                    if fn.get("name") == "web_search":
                        try:
                            args = json.loads(fn.get("arguments") or "{}")
                        except json.JSONDecodeError:
                            args = {}
                        result = await asyncio.to_thread(_web_search, args.get("query", ""))
                    else:
                        result = "unknown tool"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "content": result,
                    })

            return msg.get("content") or "ตอบไม่ได้ตอนนี้"
    except Exception as e:
        print("AI error:", e)
        return "AI error"


async def get_usage():
    """Report the provider's remaining rate limit (Groq and other OpenAI-compatible
    providers return it in x-ratelimit-* response headers)."""
    api_key = _api_key()
    if not api_key:
        return "ยังไม่ได้ตั้ง AI_API_KEY ใน .env"

    # If no chat has happened yet, make a tiny request just to read the headers.
    if not _last_rate_limit:
        try:
            async with httpx.AsyncClient(timeout=30.0) as http:
                resp = await http.post(
                    f"{_base_url()}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": _model(),
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    },
                )
            _capture_rate_limit(resp.headers)
        except Exception as e:
            print("Usage check error:", e)
            return "เช็คโควต้าไม่สำเร็จ"

    rl = _last_rate_limit
    if not rl:
        return "ผู้ให้บริการไม่ได้ส่งข้อมูลโควต้า"

    parts = []
    if "x-ratelimit-remaining-requests" in rl:
        parts.append(
            f"Requests เหลือ {rl['x-ratelimit-remaining-requests']}/"
            f"{rl.get('x-ratelimit-limit-requests', '?')}"
        )
    if "x-ratelimit-remaining-tokens" in rl:
        parts.append(
            f"Tokens เหลือ {rl['x-ratelimit-remaining-tokens']}/"
            f"{rl.get('x-ratelimit-limit-tokens', '?')}"
        )
    if "x-ratelimit-reset-requests" in rl:
        parts.append(f"reset requests ใน {rl['x-ratelimit-reset-requests']}")
    return " | ".join(parts) if parts else "ไม่พบข้อมูลโควต้า"
