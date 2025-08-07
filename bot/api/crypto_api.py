import aiohttp
import asyncio

async def get_crypto_price(crypto_id: str, currency: str = None):

    if not currency:
        currency = "usd"
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={currency.lower()}&ids={crypto_id}"

    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as response:
                raw_data = await response.json()

                data = raw_data[0]
                return {
                    "name": data["name"],
                    "symbol": data["symbol"],
                    "current_price": data["current_price"],
                    "market_cap_rank" : data["market_cap_rank"],
                    "total_volume": data["total_volume"],
                    "percent_change": round(data["price_change_percentage_24h"], 2)
                }
    except aiohttp.ClientError as e:
        return {"error": f"Network error: {str(e)}"}

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


#
# info = asyncio.run(get_crypto_price("binancecoin", "usd"))
# print(info)