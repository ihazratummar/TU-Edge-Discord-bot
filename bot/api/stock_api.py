import asyncio

import finnhub
from bot import  FINNHUB_KEY


async def get_stock_price(symbol: str):
    try:
        finnhub_client = finnhub.Client(api_key= FINNHUB_KEY)
        quote = finnhub_client.quote(symbol=symbol)

        return {
            "symbol": symbol,
            "current_price": quote["c"],
            "change": quote['d'],
            "percent_change": round(quote['dp'], 2),
            "day_high": quote['h'],
            "day_low": quote['l'],
            "day_open": quote['o'],
            "last_close": quote['pc'],
            "timestamp": quote['t'],
        }
    except Exception as e:
        print(f"Unexpected error {e}")
        return {"error": "Invalid symbol"}


info = asyncio.run(get_stock_price("AAPL"))
print(info)