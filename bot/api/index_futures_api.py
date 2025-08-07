import logging
from typing import Optional

import yfinance as yf


async def get_index_futures_data(symbol: str) -> Optional[dict]:

    try:
        ticker = yf.Ticker(symbol)
        raw_data = ticker.info
        if not raw_data or "regularMarketPrice" not in raw_data:
            return {
                "symbol": symbol,
                "error": "Data not found or invalid symbol."
            }

        regularMarketPrice = raw_data.get("regularMarketPrice", None)
        percent_change = raw_data.get("regularMarketChangePercent", 0.0)
        volume = raw_data.get("regularMarketVolume", 0)

        return {
            "symbol" : symbol,
            "current_price": regularMarketPrice,
            "percent_change": round(percent_change, 2),
            "volume": volume
        }

    except Exception as e:
        logging.error(f"HTTPError for symbol {symbol}: {e}")
        return {"error": "Invalid symbol"}

# info = asyncio.run(get_index_futures_data("NIY=F"))
# print(info)

# data = yf.Ticker("USDINR=X")
# print(data.info)