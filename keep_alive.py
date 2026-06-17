from flask import Flask
from threading import Thread
import os

app = Flask('')


@app.route('/')
def home():
    return "Keepalive started!"


def run():
    # Render (and most hosts) inject the port to bind via $PORT.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    # daemon=True so this thread never keeps the process alive on its own. If the
    # bot (main thread) crashes, the process exits and the supervisor (Docker
    # --restart / systemd) can restart it, instead of hanging with a dead bot.
    t = Thread(target=run, daemon=True)
    t.start()
