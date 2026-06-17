import os
import time
import shutil
import edge_tts
import discord
import asyncio

# Store TTS queues per guild
tts_queues = {}
tts_locks = {}

# Auto-disconnect bookkeeping
IDLE_TIMEOUT_SECONDS = 300  # leave after 5 minutes with nothing to say
voice_last_active = {}      # guild_id -> last time the bot spoke
voice_monitors = {}         # guild_id -> running monitor task


def _ffmpeg_executable():
    """Resolve the ffmpeg binary: PATH first, then an optional FFMPEG_PATH
    override, else fall back to the bare name (assumes it's on PATH)."""
    return shutil.which("ffmpeg") or os.environ.get("FFMPEG_PATH") or "ffmpeg"


def _mark_active(guild_id):
    voice_last_active[guild_id] = time.time()


async def _monitor_voice(guild):
    """Leave the voice channel when nobody (besides the bot) is left, or after
    IDLE_TIMEOUT_SECONDS with no playback."""
    try:
        while True:
            await asyncio.sleep(15)
            vc = guild.voice_client
            if vc is None or not vc.is_connected():
                return

            humans = [m for m in vc.channel.members if not m.bot]
            if not humans:
                print(f"[TTS] No one in voice for guild {guild.id}; disconnecting.")
                await vc.disconnect()
                return

            if vc.is_playing():
                _mark_active(guild.id)
            elif time.time() - voice_last_active.get(guild.id, 0) > IDLE_TIMEOUT_SECONDS:
                print(f"[TTS] Idle {IDLE_TIMEOUT_SECONDS}s for guild {guild.id}; disconnecting.")
                await vc.disconnect()
                return
    finally:
        voice_monitors.pop(guild.id, None)


def _ensure_monitor(guild):
    task = voice_monitors.get(guild.id)
    if task is None or task.done():
        voice_monitors[guild.id] = asyncio.create_task(_monitor_voice(guild))


def _tts_voice():
    """Voice for edge-tts. Thai options:
    th-TH-NiwatNeural (male), th-TH-PremwadeeNeural (female)."""
    return os.environ.get("TTS_VOICE", "th-TH-NiwatNeural")


def _tts_voice():
    """Voice for edge-tts. Thai options:
    th-TH-NiwatNeural (male), th-TH-PremwadeeNeural (female)."""
    return os.environ.get("TTS_VOICE", "th-TH-NiwatNeural")

async def handle_tts(message):
    if not message.author.voice or not message.author.voice.channel:
        await message.channel.send("Please join a voice channel first.")
        return

    text_to_speak = message.content.replace("/ftts", "").strip()
    if not text_to_speak:
        await message.channel.send("Please provide text to speak.")
        return

    guild_id = message.guild.id
    if guild_id not in tts_queues:
        tts_queues[guild_id] = asyncio.Queue()
        tts_locks[guild_id] = asyncio.Lock()

    await tts_queues[guild_id].put((message, text_to_speak))

    # If lock is not acquired, start queue processor
    if not tts_locks[guild_id].locked():
        asyncio.create_task(process_tts_queue(guild_id))

async def process_tts_queue(guild_id):
    async with tts_locks[guild_id]:
        queue = tts_queues[guild_id]
        while not queue.empty():
            message, text_to_speak = await queue.get()

            filename = f"tts_{guild_id}.mp3"
            try:
                communicate = edge_tts.Communicate(text_to_speak, voice=_tts_voice())
                await communicate.save(filename)

                user_channel = message.author.voice.channel
                current_voice_client = message.guild.voice_client

                voice_client = None
                if current_voice_client is None:
                    voice_client = await user_channel.connect()
                elif current_voice_client.channel != user_channel:
                    await current_voice_client.disconnect()
                    voice_client = await user_channel.connect()
                else:
                    voice_client = current_voice_client

                # Bot is connected: track activity and ensure the idle/empty
                # watcher is running for this guild.
                _mark_active(guild_id)
                _ensure_monitor(message.guild)

                audio_source = discord.FFmpegPCMAudio(executable=_ffmpeg_executable(), source=filename)

                while voice_client.is_playing():
                    await asyncio.sleep(1)

                voice_client.play(audio_source)
                while voice_client.is_playing():
                    await asyncio.sleep(1)

                _mark_active(guild_id)

            except Exception as e:
                await message.channel.send(f"Error: {e}")
                print(f"[TTS ERROR] {e}")
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
