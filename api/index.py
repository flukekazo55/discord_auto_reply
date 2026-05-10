import asyncio
import json
import os

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template_string, request
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from log_utils import get_user_history, save_chat_log
from openrouter import generate_reply, get_openrouter_usage


load_dotenv()

app = Flask(__name__)

PING = 1
APPLICATION_COMMAND = 2
PONG = 1
CHANNEL_MESSAGE_WITH_SOURCE = 4

REQUIRED_ENV_VARS = [
        "DISCORD_APPLICATION_ID",
        "DISCORD_PUBLIC_KEY",
        "DISCORD_BOT_TOKEN",
]

HEALTHCHECK_TEMPLATE = """
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Discord Bot Health</title>
        <style>
            :root {
                color-scheme: light;
                --bg: #f4efe6;
                --panel: #fffaf2;
                --text: #1e1e1e;
                --muted: #625d52;
                --ok: #1f7a4d;
                --warn: #b25d00;
                --border: #dccfb8;
            }
            body {
                margin: 0;
                font-family: Georgia, "Times New Roman", serif;
                background: radial-gradient(circle at top, #fff7ea, var(--bg));
                color: var(--text);
            }
            .wrap {
                max-width: 760px;
                margin: 48px auto;
                padding: 0 20px;
            }
            .panel {
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 28px;
                box-shadow: 0 16px 40px rgba(70, 52, 24, 0.08);
            }
            h1 {
                margin: 0 0 10px;
                font-size: 2rem;
            }
            p {
                color: var(--muted);
                line-height: 1.5;
            }
            .badge {
                display: inline-block;
                margin: 12px 0 18px;
                padding: 8px 12px;
                border-radius: 999px;
                font-weight: 700;
            }
            .badge.ok {
                background: rgba(31, 122, 77, 0.12);
                color: var(--ok);
            }
            .badge.warn {
                background: rgba(178, 93, 0, 0.12);
                color: var(--warn);
            }
            ul {
                padding-left: 20px;
            }
            li {
                margin: 8px 0;
            }
            code {
                background: rgba(30, 30, 30, 0.06);
                padding: 2px 6px;
                border-radius: 6px;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="panel">
                <h1>Discord Bot Health Check</h1>
                <div class="badge {{ 'ok' if ready else 'warn' }}">{{ 'READY' if ready else 'CONFIG INCOMPLETE' }}</div>
                <p>This Vercel app serves Discord Interactions over HTTP. It does not run the long-lived Discord gateway or voice features.</p>
                <p><strong>Mode:</strong> {{ mode }}</p>
                <p><strong>Health endpoint:</strong> <code>/health</code></p>
                {% if missing_vars %}
                <p><strong>Missing environment variables:</strong></p>
                <ul>
                    {% for item in missing_vars %}
                    <li>{{ item }}</li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>Required Discord environment variables are present.</p>
                {% endif %}
            </div>
        </div>
    </body>
</html>
"""


def get_missing_env_vars():
        return [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]


def build_health_payload():
        missing_vars = get_missing_env_vars()
        return {
                "status": "ready" if not missing_vars else "config-incomplete",
                "ready": not missing_vars,
                "mode": "vercel-discord-interactions",
                "missing_env_vars": missing_vars,
        }


def get_public_key():
    public_key = os.getenv("DISCORD_PUBLIC_KEY", "")
    if not public_key:
        raise RuntimeError("Missing DISCORD_PUBLIC_KEY")
    return public_key


def verify_discord_request(req):
    signature = req.headers.get("X-Signature-Ed25519")
    timestamp = req.headers.get("X-Signature-Timestamp")

    if not signature or not timestamp:
        abort(401)

    verify_key = VerifyKey(bytes.fromhex(get_public_key()))
    body = req.get_data(cache=False, as_text=False)

    try:
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
    except BadSignatureError:
        abort(401)

    return json.loads(body.decode("utf-8"))


def get_option_value(interaction, option_name, default=""):
    options = interaction.get("data", {}).get("options", [])
    for option in options:
        if option.get("name") == option_name:
            return option.get("value", default)
    return default


def get_interaction_user(interaction):
    member_user = interaction.get("member", {}).get("user", {})
    user = interaction.get("user", {})
    resolved_user = member_user or user
    user_id = resolved_user.get("id", "")
    username = resolved_user.get("global_name") or resolved_user.get("username") or "Unknown user"
    return user_id, username


def respond(content):
    return jsonify(
        {
            "type": CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": content,
            },
        }
    )


@app.route("/", methods=["GET"])
def healthcheck():
    payload = build_health_payload()
    return render_template_string(HEALTHCHECK_TEMPLATE, **payload)


@app.route("/health", methods=["GET"])
def healthcheck_json():
    return jsonify(build_health_payload())


@app.route("/", methods=["POST"])
def discord_interactions():
    interaction = verify_discord_request(request)

    if interaction.get("type") == PING:
        return jsonify({"type": PONG})

    if interaction.get("type") != APPLICATION_COMMAND:
        return respond("Unsupported interaction type.")

    command_name = interaction.get("data", {}).get("name")
    user_id, username = get_interaction_user(interaction)

    if command_name == "fping":
        return respond("Pong!")

    if command_name == "fhelp":
        return respond("คำสั่ง: /fping /fchat /flimit /fhistory /ftts")

    if command_name == "flimit":
        usage = asyncio.run(get_openrouter_usage())
        return respond(usage)

    if command_name == "fhistory":
        history = get_user_history(user_id)
        return respond("\n".join(history))

    if command_name == "fchat":
        message = get_option_value(interaction, "message")
        reply = asyncio.run(generate_reply(message))
        save_chat_log(user_id, username, message, reply)
        return respond(reply)

    if command_name == "ftts":
        return respond("TTS/voice is not supported on Vercel. Use a persistent host for /ftts.")

    return respond(f"Unknown command: {command_name}")
