import datetime
import logging
from asyncio import create_task
from enum import Enum

import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot.api.crypto_api import get_crypto_price
from bot.api.future_crypto_api import future_crypto_api
from bot.api.index_futures_api import get_index_futures_data
from bot.api.stock_api import get_stock_price
from bot.core.ModalsSchema import ModalFieldsSchema
from bot.core.constant import DbConstant, TradeType, type_list
from bot.core.embed_builder import generic_embed
from bot.core.modals import GenericModal
from bot.core.views import GenericView

class WatchlistCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_collection: AsyncIOMotorCollection = self.bot.db[DbConstant.USER_COLLECTION.value]

    async def check_user_watchlist(self, user_id):
        user_doc = await self.user_collection.find_one({"user_id": user_id})
        if not user_doc:
            return False

        is_check = user_doc.get("watchlist_check", False)
        if not is_check:
            return False

        return True

    @commands.hybrid_command(name="watchlist_delay",
                             description="Set a delay after how amy sec you want to update the watchlist")
    async def watchlist_delay(self, ctx: commands.Context, delay: int):

        if delay < 0 or type(delay) != int:
            await ctx.send(f"Please provide a valid delay value. Ex - `5, 10, or more`")

        update = await self.user_collection.update_one(
            {"user_id": ctx.author.id},
            {"$set": {"delay": delay}}
        )

        if update.modified_count > 0 or update.upserted_id is not None:
            await ctx.send(f"{delay} seconds sets for watchlist update for dms.")

    @commands.hybrid_command(name="watchlist_add", description="The item you want to add your watchlist")
    async def add_watchlist(self, ctx: commands.Context):

        if not await self.check_user_watchlist(user_id=ctx.author.id):
            await ctx.defer()
            embed = await self.view_watchlist_guide(user_id=ctx.author.id)
            await self.user_collection.update_one({"user_id": ctx.author.id}, {"$set": {"watchlist_check": True}},
                                                  upsert=True)
            # Always check if interaction has already been responded to
            await ctx.send(embed=embed)
        else:

            text_fields = [
                ModalFieldsSchema(
                    label="Symbol",
                    placeholder="AAPL, BITCOIN/USDT ,BTCUSDT, EUR/USD , ES=F",
                    required=True,
                    custom_id="symbol_custom_id"
                ),
                ModalFieldsSchema(
                    label="Type",
                    placeholder=", ".join(type_list),
                    required=True,
                    custom_id="type_custom_id",
                    default="Stock"
                )
            ]

            modal = GenericModal(
                title="Add Watchlist",
                fields=text_fields,
                custom_id="watchlist_custom_id",
                on_submit_callback=self.on_modal_submit
            )

            await  ctx.interaction.response.send_modal(modal)

    async def on_modal_submit(self, interaction: discord.Interaction, children: list[discord.ui.TextInput]):
        await interaction.response.defer()
        try:
            modal_custom_id = interaction.data.get("custom_id", "")
            if not modal_custom_id.startswith("watchlist_"):
                await  interaction.followup.send("Invalid modal", ephemeral=True)

            watchlist_entry = {}

            for field in children:
                if field.custom_id == "symbol_custom_id":
                    watchlist_entry["symbol"] = field.value
                elif field.custom_id == "type_custom_id":
                    watchlist_entry["type"] = field.value.lower()

            print(f"Watchlist entry {watchlist_entry}")

            trade_type = watchlist_entry.get("type")
            if trade_type not in type_list:
                await interaction.followup.send(
                    f"`{trade_type}` is invalid watchlist type. \nAvailable types are - `{", ".join(type_list)}`")
                return

            symbol = watchlist_entry.get("symbol")

            if symbol:
                exist = await self.user_collection.find_one(
                    {
                        "user_id": interaction.user.id,
                        "watchlist": {
                            "$elemMatch" :{
                                "symbol":symbol
                            }
                        }
                    }
                )
                if exist:
                    await interaction.followup.send(f"{symbol} already in the watchlist")
                    return


            ##TODO Validation symbols

            update = await self.user_collection.update_one(
                {"user_id": interaction.user.id},
                {"$push": {"watchlist": watchlist_entry}},
                upsert=True
            )

            fields = [
                ("📈 Symbol", f"{watchlist_entry.get("symbol")}", True),
                ("📈 Type", f"{watchlist_entry.get("type")}", True),
            ]
            embed = generic_embed(
                title="Watchlist Added",
                description=f"{interaction.user.mention}, your item has been successfully added to your watchlist.",
                timestamp=datetime.datetime.now(),
                fields=fields,
            )

            if update.modified_count > 0 or update.upserted_id is not None:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error adding watchlist: {e}")
            await interaction.followup.send(
                "❌ Failed to add your watchlist. Please try again"
            )

    async def view_watchlist_guide(self, user_id: int):

        symbols_value = (
            "**Stock** → Symbol: `AAPL`, Type: `Stock`\n"
            "**Crypto** → Symbol: `BITCOIN/USD` ,`SOLANA/USD` , Type: `Crypto`\n"
            "**Forex** → Symbol: `EUR/USD, INR/USD`, Type: `Forex`\n"
            "**Crypto Futures** → Symbol: `BTCUSDT, ETHUSD`, Type: `Crypto Futures`\n"
            "**Indices Futures** → Symbol: `ES=F`, Type: `Indices Futures`"
        )

        fields = [
            ("Example", symbols_value, False)
        ]

        embed = generic_embed(
            title="Watchlist Symbols Guide",
            description="Here's how you can add items to your personal watchlist using `/watchlist_add` command.",
            fields=fields
        )

        await self.user_collection.update_one({"user_id": user_id}, {"$set": {"watchlist_check": True}})
        return embed

    @commands.hybrid_command(name="watchlist_guide", description="Check watchlist guide how to add symbols")
    async def watchlist_guide(self, ctx: commands.Context):
        embed = await self.view_watchlist_guide(user_id=ctx.author.id)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="view_watchlist", description="View your watchlist")
    async def view_watchlist(self, ctx: commands.Context):
        await ctx.defer()
        user_id = ctx.author.id
        user_doc = await self.user_collection.find_one({"user_id": user_id})

        if not user_doc or not user_doc.get("watchlist"):
            await ctx.send(f"❌ You don't have any items in your watchlist")
            return

        watchlist = user_doc["watchlist"]

        types = list({item["type"].title() for item in watchlist})
        options = [
            discord.SelectOption(label=type_name, value=type_name.lower())
            for type_name in types
        ]

        # Initial embed
        embed = generic_embed(
            title="📋 Your Watchlist",
            description="Select a type from the dropdown below to view corresponding symbols.",
        )

        # View setup
        view = GenericView()

        async def select_callback(interaction: discord.Interaction):

            await interaction.response.defer()

            selected_type = interaction.data["values"][0].lower()
            filtered = [entry for entry in watchlist if entry["type"].lower() == selected_type]
            if not filtered:
                await interaction.edit_original_response(embed=generic_embed(
                    title=f"No {selected_type.title()} entries",
                    description="No symbols found for the selected type."
                ))
                return

            fields = []

            for entry in filtered:
                symbol = entry["symbol"]
                type_ = entry["type"].lower()

                try:
                    if type_ == TradeType.STOCK.value:
                        stock_api_data = await get_stock_price(symbol)

                        if "error" in stock_api_data:
                            continue

                        name = stock_api_data.get("symbol")
                        value = f">>> 💵 Price {stock_api_data.get("current_price", "N/A")}\n📊 Change: `{stock_api_data.get("percent_change")}%`"
                    elif type_ == TradeType.CRYPTO.value:
                        symbol = symbol.split("/")
                        crypto_id, currency = symbol
                        crypto_data = await get_crypto_price(crypto_id=crypto_id, currency=currency)
                        if "error" in crypto_data:
                            continue
                        name = crypto_data.get("name")
                        value = f">>> 💵 Price {crypto_data.get("current_price", "N/A")}\n📊 Change: `{crypto_data.get("percent_change")}%` \n📈 Volume: {crypto_data.get("total_volume", "N/A")}"

                    elif type_ == TradeType.CRYPTO_FUTURES.value:
                        crypto_future_data = await future_crypto_api(symbol)
                        if "error" in crypto_future_data:
                            continue
                        name = crypto_future_data.get("symbol", 'N/A')
                        value = f">>> 💵 Price {crypto_future_data.get("current_price", "N/A")}\n📊 Change: `{crypto_future_data.get("percent_change")}%` \n📈 Volume: {crypto_future_data.get("volume", "N/A")}"

                    elif type_ == TradeType.INDICES_FUTURES.value:
                        index_data = await get_index_futures_data(symbol= symbol)
                        if "error" in index_data:
                            continue
                        name = index_data.get("symbol")
                        value = f">>> 💵 Price {index_data.get("current_price", "N/A")}\n📊 Change: `{index_data.get("percent_change")}%` \n📈 Volume: {index_data.get("volume", "N/A")}"

                    elif type_ == TradeType.FOREX.value:
                        symbol = symbol.split("/")
                        asset, currency = symbol
                        forex_data = await get_index_futures_data(symbol=f"{asset}{currency}=X")
                        if "error" in forex_data:
                            continue
                        name = forex_data.get("symbol")
                        value = f">>> 💵 Price {forex_data.get("current_price", "N/A")}\n📊 Change: `{forex_data.get("percent_change")}%` \n📈 Volume: {forex_data.get("volume", "N/A")}"
                    else:
                        continue

                    fields.append((f"📈 {name.upper()}", value, True))
                except Exception as e:
                    logging.error(f"Error while processing {symbol} : {e}")
                    continue

            updated_embed = generic_embed(
                title=f"Watchlist: {selected_type.title()}",
                description=f"Symbols under `{selected_type.title()}` type:",
                fields=fields,
                timestamp=datetime.datetime.now()
            )

            await interaction.edit_original_response(embed=updated_embed)

        view.add_select(
            placeholder="Select watchlist type...",
            options=options,
            custom_id="watchlist_type_select",
            callback=select_callback
        )

        await ctx.send(embed=embed, view=view, ephemeral=True)
