from bot.cogs.market.market_ai_response import MarketAi

async def setup(bot):
    await bot.add_cog(MarketAi(bot))