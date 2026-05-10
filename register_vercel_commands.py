import os

import httpx
from dotenv import load_dotenv


load_dotenv()


def build_commands():
    return [
        {
            "name": "fping",
            "description": "Ping test",
            "type": 1,
        },
        {
            "name": "fhelp",
            "description": "Show command list",
            "type": 1,
        },
        {
            "name": "flimit",
            "description": "Show token usage",
            "type": 1,
        },
        {
            "name": "fhistory",
            "description": "Show your chat history",
            "type": 1,
        },
        {
            "name": "fchat",
            "description": "Chat with AI via OpenRouter",
            "type": 1,
            "options": [
                {
                    "name": "message",
                    "description": "Your message to the AI bot",
                    "type": 3,
                    "required": True,
                }
            ],
        },
        {
            "name": "ftts",
            "description": "Explain Vercel voice limitation",
            "type": 1,
            "options": [
                {
                    "name": "text",
                    "description": "Text to speak",
                    "type": 3,
                    "required": True,
                }
            ],
        },
    ]


def main():
    application_id = os.getenv("DISCORD_APPLICATION_ID", "")
    bot_token = os.getenv("DISCORD_BOT_TOKEN", "")

    if not application_id or not bot_token:
        raise RuntimeError("DISCORD_APPLICATION_ID and DISCORD_BOT_TOKEN are required")

    url = f"https://discord.com/api/v10/applications/{application_id}/commands"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    }

    response = httpx.put(url, headers=headers, json=build_commands(), timeout=30.0)
    response.raise_for_status()
    print(f"Registered {len(response.json())} global command(s)")


if __name__ == "__main__":
    main()
