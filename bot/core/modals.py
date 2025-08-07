import discord.ui

from bot.core.ModalsSchema import ModalFieldsSchema


class GenericModal(discord.ui.Modal):
    def __init__(
            self,
            title: str,
            fields: list[ModalFieldsSchema],
            on_submit_callback = None,
            timeout: float | None = None,
            custom_id: str | None = None
    ):
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

        for field in fields:
            text_input = discord.ui.TextInput(
                label=field.label,
                style= discord.TextStyle.short if field.style == 1 else discord.TextStyle.paragraph,
                custom_id=field.custom_id,
                placeholder= field.placeholder,
                default= field.default,
                required=field.required,
                min_length=field.min_length,
                max_length= field.max_length
            )

            self.add_item(text_input)

        self._on_submit_call_back = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        if self._on_submit_call_back:
            await self._on_submit_call_back(interaction, self.children)
