import os
import json
from datetime import datetime
from pathlib import Path


def _resolve_log_file_path():
    configured_path = os.getenv("CHAT_LOG_PATH")
    if configured_path:
        return Path(configured_path)

    if os.getenv("VERCEL"):
        return Path("/tmp/chat_log.jsonl")

    return Path(__file__).resolve().with_name("chat_log.jsonl")


LOG_FILE_PATH = _resolve_log_file_path()
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

def save_chat_log(user_id, username, user_msg, bot_reply):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": str(user_id),
        "username": username,
        "user_message": user_msg,
        "bot_reply": bot_reply,
    }
    with LOG_FILE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_chat_history_for_prompt(max_messages=20):
    history = []
    try:
        with LOG_FILE_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                history.extend([
                    {"role": "user", "content": entry["user_message"]},
                    {"role": "assistant", "content": entry["bot_reply"]}
                ])
    except Exception as e:
        print(f"Failed to load chat history: {e}")
    # Only keep the most recent messages so the prompt stays small (fewer tokens,
    # less chance of hitting provider rate limits).
    return history[-max_messages:]

def get_user_history(user_id, max_entries=5):
    history = []
    normalized_user_id = str(user_id)
    try:
        with LOG_FILE_PATH.open("r", encoding="utf-8") as f:
            for line in reversed(f.readlines()):
                entry = json.loads(line)
                if str(entry["user_id"]) == normalized_user_id:
                    history.append(f"- {entry['user_message']} ➜ {entry['bot_reply']}")
                    if len(history) >= max_entries:
                        break
    except Exception as e:
        print(f"❌ Failed to get user history: {e}")
    return history or ["No chat history found."]
