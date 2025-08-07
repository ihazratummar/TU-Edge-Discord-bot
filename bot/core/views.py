import discord.ui


class GenericView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout= None)

    def add_select(
            self,
            placeholder: str,
            options: list[discord.SelectOption],
            min_values: int = 1,
            max_values: int = 1,
            custom_id: str | None = None,
            disabled: bool = False,
            callback=None
    ):
        select = discord.ui.Select(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
            custom_id= custom_id
        )

        if callback:
            select.callback = callback
        self.add_item(select)