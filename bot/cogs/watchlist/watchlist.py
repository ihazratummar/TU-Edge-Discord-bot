import asyncio
import json
import time
from collections import defaultdict

import websockets
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot import FINNHUB_KEY
from bot.core.constant import DbConstant


class Watchlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_collection: AsyncIOMotorCollection = self.bot.db[DbConstant.USER_COLLECTION.value]
        self.api_key = FINNHUB_KEY
        self.ws_url = f"wss://ws.finnhub.io?token={self.api_key}"
        # self.bot.loop.create_task(self.start_websockets())


        self.symbol_to_users = {}  # Mapping from symbol to list of user_ids
        self.symbols_subscribed = set()
        self.user_delays = {}
        self.last_sent = defaultdict(lambda: defaultdict(lambda: 0))  # user_id -> symbol -> last_sent_timestamp
        # self.bot.loop.create_task(self.periodic_user_data_refresh())

    async def periodic_user_data_refresh(self, interval=60):
        await self.bot.wait_until_ready()
        while True:
            await self.update_symbol_to_users()
            await asyncio.sleep(interval)


    async def start_websockets(self):
        await  self.bot.wait_until_ready()

        async for websocket in websockets.connect(self.ws_url):
            try:
                print("[WEBSOCKET] CONNECTED")
                await self.update_symbol_to_users()
                await self.subscribe_symbols(websocket)

                async for message in websocket:
                    print("[DEBUG] Raw message:", message)
                    data = json.loads(message)
                    asyncio.create_task(self.handle_data(data))  # Don't block main loop
            except Exception as e:
                print(f"[WEBSOCKET ERROR] {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)


    async def update_symbol_to_users(self):
        """Fetch all users and their watchlist from DB"""

        self.symbol_to_users.clear()

        cursor = self.user_collection.find({})

        async for doc in cursor:
            user_id = str(doc["user_id"])
            delay = doc.get("delay", 30)
            self.user_delays[user_id] = delay
            for item in doc.get("watchlist", []):
                symbol = item["symbol"]
                if symbol not in self.symbol_to_users:
                    self.symbol_to_users[symbol] = []
                self.symbol_to_users[symbol].append(user_id)

    async def subscribe_symbols(self, websocket):
        """Subscribe to all symbols in all watchlist"""

        for symbol in self.symbol_to_users:
            if symbol not in self.symbols_subscribed:
                await websocket.send(json.dumps({"type": "subscribe", "symbol": symbol}, indent=4))
                self.symbols_subscribed.add(symbol)




    async def handle_data(self, data: dict):
        """handle incoming price updates and DM relevant users"""

        if data.get("type") != "trade":
            return

        for trade  in data.get("data",[]):
            symbol = trade["s"]
            price = trade['p']
            timestamp = trade['t']
            volume = trade['v']

            user_ids = self.symbol_to_users.get(symbol,[])

            now = time.time()

            for user_id in user_ids:
                delay = self.user_delays.get(user_id, 30)
                last_sent_time = self.last_sent[user_id][symbol]

                if now - last_sent_time >= delay:
                    self.last_sent[user_id][symbol] = now
                    user = self.bot.get_user(int(user_id))
                    if user:
                        try:
                            await user.send(f"📈 {symbol} price updated: **${price}**")
                        except Exception as e:
                            print(f"[DM Error] {user_id}: {e}")



# import aiohttp
#
# async def test_symbol(symbol):
#     url = f"wss://ws.finnhub.io?token={FINNHUB_KEY}"
#     async with aiohttp.ClientSession() as session:
#         async with session.ws_connect(url) as ws:
#             await ws.send_json({"type": "subscribe", "symbol": symbol})
#             print(f"Subscribed to: {symbol}")
#             for _ in range(10):
#                 msg = await ws.receive()
#                 if msg.type == aiohttp.WSMsgType.TEXT:
#                     print("Received:", msg.data)
#
# asyncio.run(test_symbol("BINANCE:BTCUSDT.P"))