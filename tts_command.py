import os
from gtts import gTTS
import discord
import asyncio


async def handle_tts(message):
    if not message.author.voice or not message.author.voice.channel:
        await message.channel.send("Please join a voice channel first.")
        return

    text_to_speak = message.content.replace("/ftts", "").strip()
    if not text_to_speak:
        await message.channel.send("Please provide text to speak.")
        return

    filename = "tts.mp3"
    tts = gTTS(text=text_to_speak, lang='th')
    tts.save(filename)

    user_channel = message.author.voice.channel
    current_voice_client = message.guild.voice_client

    try:
        voice_client = None

        # Case 1: Bot not connected → connect
        if current_voice_client is None:
            voice_client = await user_channel.connect()

        # Case 2: Bot is connected to a different channel → move
        elif current_voice_client.channel != user_channel:
            await current_voice_client.disconnect()
            voice_client = await user_channel.connect()

        # Case 3: Bot is already in the same channel → reuse
        else:
            voice_client = current_voice_client

        # Play audio
        audio_source = discord.FFmpegPCMAudio(executable="ffmpeg", source=filename)
        if not voice_client.is_playing():
            voice_client.play(audio_source)

            while voice_client.is_playing():
                await asyncio.sleep(1)

        os.remove(filename)

    except Exception as e:
        await message.channel.send(f"TTS error: {e}")
        print(f"TTS ERROR: {e}")
