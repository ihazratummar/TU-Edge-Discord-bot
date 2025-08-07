from bot.cogs.watchlist.watchlist_commands import WatchlistCommands
from bot.cogs.watchlist.watchlist import Watchlist


async def setup(bot):
    await bot.add_cog(WatchlistCommands(bot= bot))