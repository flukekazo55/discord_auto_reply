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
    t = Thread(target=run)
    t.start()
