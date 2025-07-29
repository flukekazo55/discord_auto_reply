import os
import json
from datetime import datetime

LOG_FILE_PATH = "./chat_log.jsonl"
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

def save_chat_log(user_id, username, user_msg, bot_reply):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "username": username,
        "user_message": user_msg,
        "bot_reply": bot_reply,
    }
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_chat_history_for_prompt():
    history = []
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                history.extend([
                    {"role": "user", "content": entry["user_message"]},
                    {"role": "assistant", "content": entry["bot_reply"]}
                ])
    except Exception as e:
        print(f"⚠️ Failed to load chat history: {e}")
    return history

def get_user_history(user_id, max_entries=5):
    history = []
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            for line in reversed(f.readlines()):
                entry = json.loads(line)
                if entry["user_id"] == user_id:
                    history.append(f"- {entry['user_message']} ➜ {entry['bot_reply']}")
                    if len(history) >= max_entries:
                        break
    except Exception as e:
        print(f"❌ Failed to get user history: {e}")
    return history or ["ไม่พบประวัติสำหรับผู้ใช้นี้"]
