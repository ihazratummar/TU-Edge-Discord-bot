import asyncio
import discord
import logging
from bot.config import Bot
from bot import BOT_TOKEN


logging.basicConfig(
    level=logging.INFO,
    force='%(asctime)s %(levelname)s:%(name)s: %(message)s'
)

if not BOT_TOKEN:
    raise ValueError("No Discord bot token found in environment variables.")

bot = Bot(command_prefix="t!", intents= discord.Intents.all())

async def main():
    async with  bot:
        await  bot.start(token=BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())