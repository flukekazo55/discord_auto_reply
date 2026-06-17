from bot_config import client, DISCORD_BOT_TOKEN
from commands import register_commands
from keep_alive import keep_alive

# Start keep-alive server
keep_alive()

# Register command handlers
register_commands()

# Run the bot
try:
    client.run(DISCORD_BOT_TOKEN)
except KeyboardInterrupt:
    print("stopped by user on terminal")
