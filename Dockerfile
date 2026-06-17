FROM python:3.11-slim

# System dependencies for Discord voice:
#   ffmpeg  -> decodes the gTTS mp3 for playback (discord.FFmpegPCMAudio)
#   libopus -> Discord voice encoding (PyNaCl + discord.py[voice])
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libopus0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The keep-alive web server binds to $PORT so the host's health check passes.
ENV PORT=10000
EXPOSE 10000

CMD ["python", "main.py"]
