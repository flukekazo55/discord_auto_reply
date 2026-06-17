#!/usr/bin/env bash
# Run the Discord bot from a bash terminal (Git Bash on Windows, or Linux/Mac).
# Creates a virtualenv if needed, installs deps, then starts the bot.
#
#   bash run.sh
#
set -e
cd "$(dirname "$0")"

# 1. Create the virtualenv on first run.
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv (.venv)..."
  python -m venv .venv
fi

# 2. Pick the venv's python (Windows Git Bash uses Scripts/, Linux/Mac use bin/).
if [ -f ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"
else
  PY=".venv/bin/python"
fi

# 3. Make sure dependencies are installed (fast no-op once satisfied).
echo "Installing dependencies..."
"$PY" -m pip install -q -r requirements.txt

# 4. Warn if ffmpeg is missing (voice /ftts needs it; text commands still work).
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "WARNING: ffmpeg not found on PATH -> /ftts voice will not work (text commands are fine)."
fi

# 5. Start the bot. It reads tokens from .env automatically.
echo "Starting bot... (Ctrl+C to stop)"
exec "$PY" main.py
