import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
from bot.core.constant import DbConstant
from bot import MONGO_CLIENT

extensions = [
    "bot.cogs.watchlist",
    "bot.cogs.market"
]

class Bot(commands.Bot):
    def __init__(self, command_prefix: str, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=command_prefix, intents=intents, **kwargs)
        self.mongo_client = MONGO_CLIENT
        self.db = self.mongo_client[DbConstant.DATABASE_NAME.value]
        self.scheduler  = AsyncIOScheduler()

    async def on_ready(self):
        for extension  in extensions:
            await self.load_extension(extension)

        synced = await self.tree.sync()


        print(f"{self.application_id} is now ready..")
        print(f"{len(synced)} commands loaded...")
