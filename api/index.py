import asyncio
import json
import os

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request
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
    return jsonify(
        {
            "status": "ok",
            "mode": "vercel-discord-interactions",
        }
    )


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
