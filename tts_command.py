import os
from gtts import gTTS
import discord
import asyncio

# Store TTS queues per guild
tts_queues = {}
tts_locks = {}

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
                tts = gTTS(text=text_to_speak, lang='th')
                tts.save(filename)

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

                audio_source = discord.FFmpegPCMAudio(executable="ffmpeg", source=filename)

                while voice_client.is_playing():
                    await asyncio.sleep(1)

                voice_client.play(audio_source)
                while voice_client.is_playing():
                    await asyncio.sleep(1)

            except Exception as e:
                await message.channel.send(f"Error: {e}")
                print(f"[TTS ERROR] {e}")
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
