import discord.ui

from bot.core.models.button_schema import ButtonSchema


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

    def add_buttons(self, buttons: list[ButtonSchema]):
        for button_data in buttons:
            button = discord.ui.Button(
                label=button_data.label,
                style=button_data.style,
                emoji=button_data.emoji,
                custom_id=button_data.custom_id or f"button_{id(self)}",
                disabled=button_data.disabled
            )
            if button_data.callback:
                button.callback = button_data.callback

            self.add_item(button)
