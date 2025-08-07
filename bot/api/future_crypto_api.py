import aiohttp


async def future_crypto_api(symbol: str):

    url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"

    try:

        async with aiohttp.ClientSession() as client:
            async with client.get(url) as response:
                raw_data = await response.json()
                print(raw_data)
                data = {
                    "symbol": raw_data.get("symbol", "N/A"),
                    "current_price": float(raw_data.get("lastPrice", 0)),
                    "percent_change": float(raw_data.get("priceChangePercent", 0)),
                    "volume": float(raw_data.get("volume", 0))
                }
                return  data

    except Exception as e:
        print(f"[F CRYPTO ERROR]: Unknown error {e}")
        return  {"error": "Invalid symbol"}

#
# info = asyncio.run(future_crypto_api("MEWUSDT"))
# print(info)