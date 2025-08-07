import logging

from discord.ext import commands

from bot.api.crypto_api import get_crypto_price
from bot.api.future_crypto_api import future_crypto_api
from bot.api.index_futures_api import get_index_futures_data
from bot.api.stock_api import get_stock_price
from bot.core.ai import generate_market_ai_response
from bot.core.constant import type_list, TradeType
from bot.core.embed_builder import generic_embed


class MarketAi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(name="market", description="Get market insight by ai")
    async def market(self, ctx: commands.Context, symbol: str, trade_type: str):
        await ctx.defer()

        if trade_type.lower() not in type_list:
            await ctx.send(f"Type not supported, user this type please: {", ".join(type_list)} ")
            return
        try:
            if trade_type.lower() == TradeType.CRYPTO.value:
                print("checking crypto")
                crypto_id , currency = symbol.split("/")
                crypto_data = await get_crypto_price(crypto_id=crypto_id.lower(), currency= currency.lower())
                if "error" in crypto_data:
                    return
                ai_response = await generate_market_ai_response(live_data=crypto_data)
                if not ai_response:
                    ai_description = "⚠️ Could not generate AI insight at the moment. Please try again later."
                else:
                    ai_description = ai_response

                fields = [
                    ("🪙 Symbol", crypto_data.get("symbol", 'N/A'), True),
                    ("💵 Current Price", f"${crypto_data.get('current_price', 'N/A')}", True),
                    ("📈 Percent Change", f"{crypto_data.get('percent_change', 0.0)}%", True),
                    ("📊 Total Volume", f"{crypto_data.get('total_volume', 0.0):,}", True),
                ]

            elif trade_type.lower() == TradeType.STOCK.value:
                print("checking stock")
                stock_data = await get_stock_price(symbol=symbol.upper())
                if "error" in stock_data:
                    return
                ai_response = await generate_market_ai_response(live_data=stock_data)
                if not ai_response:
                    ai_description = "⚠️ Could not generate AI insight at the moment. Please try again later."
                else:
                    ai_description = ai_response

                fields = [
                    ("🪙 Symbol", stock_data.get("symbol", 'N/A'), True),
                    ("💵 Current Price", f"${stock_data.get('current_price', 'N/A')}", True),
                    ("📈 Percent Change", f"{stock_data.get('percent_change')} %", True),
                ]

            elif trade_type.lower() == TradeType.FOREX.value:
                print("checking forex")
                symbol = symbol.split("/")
                asset, currency = symbol
                forex_data = await get_index_futures_data(symbol=f"{asset}{currency}=X")
                if "error" in forex_data:
                    return
                ai_response = await generate_market_ai_response(live_data=forex_data)
                if not ai_response:
                    ai_description = "⚠️ Could not generate AI insight at the moment. Please try again later."
                else:
                    ai_description = ai_response

                fields = [
                    ("🪙 Symbol", forex_data.get("symbol", 'N/A'), True),
                    ("💵 Current Price", f"${forex_data.get('current_price', 'N/A')}", True),
                    ("📈 Percent Change", f"{forex_data.get('percent_change', 0.0)}%", True),
                    ("📊 Total Volume", f"{forex_data.get('total_volume', 0.0):,}", True),
                ]

            elif trade_type.lower() == TradeType.INDICES_FUTURES.value:
                print("checking future")
                index_data = await get_index_futures_data(symbol= f"{symbol}=F")
                if "error" in index_data:
                    return
                ai_response = await generate_market_ai_response(live_data=index_data)
                if not ai_response:
                    ai_description = "⚠️ Could not generate AI insight at the moment. Please try again later."
                else:
                    ai_description = ai_response

                fields = [
                    ("🪙 Symbol", index_data.get("symbol", 'N/A'), True),
                    ("💵 Current Price", f"${index_data.get('current_price', 'N/A')}", True),
                    ("📈 Percent Change", f"{index_data.get('percent_change', 0.0)}%", True),
                    ("📊 Total Volume", f"{index_data.get('total_volume', 0.0):,}", True),
                ]

            elif trade_type.lower() == TradeType.CRYPTO_FUTURES.value:
                print("checking future")
                crypto_future_data = await future_crypto_api(symbol)
                if "error" in crypto_future_data:
                    return
                ai_response = await generate_market_ai_response(live_data=crypto_future_data)
                if not ai_response:
                    ai_description = "⚠️ Could not generate AI insight at the moment. Please try again later."
                else:
                    ai_description = ai_response

                fields = [
                    ("🪙 Symbol", crypto_future_data.get("symbol", 'N/A'), True),
                    ("💵 Current Price", f"${crypto_future_data.get('current_price', 'N/A')}", True),
                    ("📈 Percent Change", f"{crypto_future_data.get('percent_change', 0.0)}%", True),
                    ("📊 Total Volume", f"{crypto_future_data.get('total_volume', 0.0):,}", True),
                ]

            else:
                ai_description = "No Response"
                fields = []

            embed = generic_embed(
                title="🤖 TU Helper",
                description= f">>> **{symbol}**\n{ai_description}",
                fields=fields
            )

            await ctx.send(embed= embed)
        except Exception as  e:
            logging.error(f"[MARKET ERROR] Error getting market ai response {e}")


