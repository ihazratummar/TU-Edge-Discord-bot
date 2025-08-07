from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
MONGO_URI = os.getenv("MONGO_URI")


MONGO_CLIENT = AsyncIOMotorClient(MONGO_URI)




__all__ = [
    "BOT_TOKEN",
    "MONGO_CLIENT",
    "FINNHUB_KEY"
]
