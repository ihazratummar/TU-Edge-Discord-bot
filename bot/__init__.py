from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
MONGO_URI = os.getenv("MONGO_URI")
GITHUB_AI_TOKEN = os.getenv("GITHUB_AI_TOKEN")


MONGO_CLIENT = AsyncIOMotorClient(MONGO_URI)



__all__ = [
    "BOT_TOKEN",
    "MONGO_CLIENT",
    "FINNHUB_KEY",
    "GITHUB_AI_TOKEN"
]
