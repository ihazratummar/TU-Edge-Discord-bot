import datetime
import logging

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
from bot.core.models.button_schema import ButtonSchema
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
            await ctx.send(embed=embed)
        else:
            view = GenericView()
            options = [
                discord.SelectOption(label=trade_type.title(), value=trade_type)
                for trade_type in type_list
            ]

            async def on_type_select(interaction: discord.Interaction):
                selected_type = interaction.data["values"][0]

                async def on_symbol_modal_submit(modal_interaction: discord.Interaction, children: list[discord.ui.TextInput]):
                    symbol = children[0].value
                    await modal_interaction.response.defer()
                    await self._add_item_to_watchlist(modal_interaction, symbol, selected_type)

                symbol_field = [
                    ModalFieldsSchema(
                        label="Symbol",
                        placeholder="AAPL, BITCOIN/USDT, BTCUSDT...",
                        required=True,
                        custom_id="symbol_custom_id"
                    )
                ]

                modal = GenericModal(
                    title=f"Add Symbol for {selected_type.title()}",
                    fields=symbol_field,
                    custom_id=f"watchlist_symbol_modal",
                    on_submit_callback=on_symbol_modal_submit
                )

                await interaction.response.send_modal(modal)

            view.add_select(
                placeholder="Select a type to add to your watchlist",
                options=options,
                custom_id="watchlist_type_select",
                callback=on_type_select
            )

            await ctx.send("Please select a type for the new watchlist item:", view=view, ephemeral=True)

    async def _add_item_to_watchlist(self, interaction: discord.Interaction, symbol: str, trade_type: str):
        try:
            if trade_type not in type_list:
                await interaction.followup.send(
                    f"`{trade_type}` is invalid watchlist type. \nAvailable types are - `{', '.join(type_list)}`")
                return

            exist = await self.user_collection.find_one(
                {
                    "user_id": interaction.user.id,
                    "watchlist": {
                        "$elemMatch": {
                            "symbol": symbol.lower(),
                            "type": trade_type.lower()
                        }
                    }
                }
            )
            if exist:
                await interaction.followup.send(f"`{symbol}` with type `{trade_type}` already in the watchlist.")
                return

            watchlist_entry = {"symbol": symbol, "type": trade_type.lower()}

            update = await self.user_collection.update_one(
                {"user_id": interaction.user.id},
                {"$push": {"watchlist": watchlist_entry}},
                upsert=True
            )

            fields = [
                ("📈 Symbol", f"{watchlist_entry.get('symbol')}", True),
                ("📈 Type", f"{watchlist_entry.get('type')}", True),
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
            logging.error(f"Error adding watchlist: {e}")
            await interaction.followup.send(
                "❌ Failed to add your watchlist. Please try again"
            )

    async def view_watchlist_guide(self, user_id: int):

        symbols_value = (
            "**Stock** → Symbol: `AAPL`, Type: `Stock`\n"
            "**Crypto** → Symbol: `BITCOIN/USD` ,`SOLANA/USD` , Type: `Crypto`\n"
            "**Forex** → Symbol: `EUR/USD, INR/USD`, Type: `Forex`\n"
            "**Crypto Futures** → Symbol: `BTCUSDT, ETHUSD`, Type: `Crypto Futures`\n"
            "**Indices Futures** → Symbol: `ES=F`, Type: `Futures`"
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
            # Check if the user is authorized to use this interaction
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ You can only interact with your own watchlist!", ephemeral=True)
                return

            await interaction.response.defer()

            selected_type = interaction.data["values"][0].lower()
            filtered = [entry for entry in watchlist if entry["type"].lower() == selected_type]
            if not filtered:
                await interaction.edit_original_response(embed=generic_embed(
                    title=f"No {selected_type.title()} entries",
                    description="No symbols found for the selected type."
                ))
                return

            all_fields = []

            for entry in filtered:
                symbol = entry["symbol"]
                type_ = entry["type"].lower()

                try:
                    if type_ == TradeType.STOCK.value:
                        stock_api_data = await get_stock_price(symbol.upper())

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
                        index_data = await get_index_futures_data(symbol= f"{symbol}=F")
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

                    all_fields.append((f"📈 {name.upper()}", value, True))
                except Exception as e:
                    logging.error(f"Error while processing {symbol} : {e}")
                    continue

            # Pagination logic
            items_per_page = 9
            total_pages = max(1, (len(all_fields) + items_per_page - 1) // items_per_page)
            current_page = 1
            
            async def display_page(page_num: int, edit_interaction: discord.Interaction = None):
                start_idx = (page_num - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_fields = all_fields[start_idx:end_idx]
                
                description = f"Symbols under `{selected_type.title()}` type:"
                if total_pages > 1:
                    description += f"\n📄 Page {page_num}/{total_pages} ({len(all_fields)} total items)"
                
                updated_embed = generic_embed(
                    title=f"Watchlist: {selected_type.title()}",
                    description=description,
                    fields=page_fields,
                    timestamp=datetime.datetime.now()
                )

                # Create view with dropdown and pagination if needed
                combined_view = GenericView()
                
                # Re-add the dropdown menu
                combined_view.add_select(
                    placeholder="Select watchlist type...",
                    options=options,
                    custom_id="watchlist_type_select",
                    callback=select_callback
                )
                
                # Add pagination buttons if more than items_per_page items
                if len(all_fields) > items_per_page:
                    async def first_button_callback(btn_interaction: discord.Interaction):
                        # Check if the user is authorized to use this interaction
                        if btn_interaction.user.id != user_id:
                            await btn_interaction.response.send_message("❌ You can only interact with your own watchlist!", ephemeral=True)
                            return
                        await btn_interaction.response.defer()
                        await display_page(1, btn_interaction)
                    
                    async def prev_button_callback(btn_interaction: discord.Interaction):
                        # Check if the user is authorized to use this interaction
                        if btn_interaction.user.id != user_id:
                            await btn_interaction.response.send_message("❌ You can only interact with your own watchlist!", ephemeral=True)
                            return
                        await btn_interaction.response.defer()
                        prev_page = max(1, page_num - 1)
                        await display_page(prev_page, btn_interaction)
                    
                    async def next_button_callback(btn_interaction: discord.Interaction):
                        # Check if the user is authorized to use this interaction
                        if btn_interaction.user.id != user_id:
                            await btn_interaction.response.send_message("❌ You can only interact with your own watchlist!", ephemeral=True)
                            return
                        await btn_interaction.response.defer()
                        next_page = min(total_pages, page_num + 1)
                        await display_page(next_page, btn_interaction)
                    
                    async def last_button_callback(btn_interaction: discord.Interaction):
                        # Check if the user is authorized to use this interaction
                        if btn_interaction.user.id != user_id:
                            await btn_interaction.response.send_message("❌ You can only interact with your own watchlist!", ephemeral=True)
                            return
                        await btn_interaction.response.defer()
                        await display_page(total_pages, btn_interaction)

                    buttons = [
                        ButtonSchema(
                            label="First",
                            style=discord.ButtonStyle.secondary,
                            disabled=page_num == 1,
                            callback=first_button_callback,
                            emoji="⏮️",
                            custom_id="first_button_navigation"
                        ),
                        ButtonSchema(
                            label="Previous",
                            style=discord.ButtonStyle.secondary,
                            disabled=page_num == 1,
                            callback=prev_button_callback,
                            emoji="◀️",
                            custom_id="previous_button_navigation"
                        ),
                        ButtonSchema(
                            label="Next",
                            style=discord.ButtonStyle.secondary,
                            disabled=page_num == total_pages,
                            callback=next_button_callback,
                            emoji="▶️",
                            custom_id="next_button_navigation"
                        ),
                        ButtonSchema(
                            label="Last",
                            style=discord.ButtonStyle.secondary,
                            disabled=page_num == total_pages,
                            callback=last_button_callback,
                            emoji="⏭️",
                            custom_id="last_button_navigation"
                        )
                    ]
                    combined_view.add_buttons(buttons=buttons)
                if edit_interaction:
                    await edit_interaction.edit_original_response(embed=updated_embed, view=combined_view)
                else:
                    await interaction.edit_original_response(embed=updated_embed, view=combined_view)
            await display_page(current_page)
        view.add_select(
            placeholder="Select watchlist type...",
            options=options,
            custom_id="watchlist_type_select",
            callback=select_callback
        )
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @commands.hybrid_command(name="watchlist", description="Check all your watchlist in one place")
    async def my_watchlist(self, ctx: commands.Context):
        await ctx.defer()
        user_id = ctx.author.id
        user_doc = await self.user_collection.find_one({"user_id": user_id})

        if not user_doc or not user_doc.get("watchlist"):
            await ctx.send(f"❌ You don't have any items in your watchlist")
            return

        watchlist = user_doc["watchlist"]

        # Group symbols by type
        grouped_watchlist = {}
        for item in watchlist:
            item_type = item["type"].title()  # Capitalize for display
            symbol = item["symbol"]
            if item_type not in grouped_watchlist:
                grouped_watchlist[item_type] = []
            grouped_watchlist[item_type].append(symbol)

        fields = []
        for item_type, symbols in grouped_watchlist.items():
            symbols_str = ", ".join(symbols)
            fields.append((f"📈 {item_type}", symbols_str, False))

        embed = generic_embed(
            title=f"📋 {ctx.author.name}'s Watchlist",
            description="Here are all the items in your watchlist, grouped by type.",
            fields=fields,
            timestamp=datetime.datetime.now(),
            thumbnail= ctx.author.avatar.url if ctx.author.avatar else None
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="watchlist_remove", description="Remove an item from your watchlist")
    async def watchlist_remove(self, ctx: commands.Context, symbol: str, type: str):
        await ctx.defer()
        user_id = ctx.author.id

        if type.lower() not in type_list:
            await ctx.send(f"`{type}` is an invalid watchlist type. Available types are - `{", ".join(type_list)}`",
                           ephemeral=True)
            return

        update_result = await self.user_collection.update_one(
            {"user_id": user_id},
            {"$pull": {"watchlist": {"symbol": symbol, "type": type.lower()}}}
        )

        if update_result.modified_count > 0:
            embed = generic_embed(
                title="Watchlist Item Removed",
                description=f"Successfully removed `{symbol}` of type `{type}` from your watchlist.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Could not find `{symbol}` of type `{type}` in your watchlist.", ephemeral=True)


