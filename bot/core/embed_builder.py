import datetime

import discord


def generic_embed(
        title: str,
        description: str,
        color: discord.Color = discord.Color.from_str("#ddad3e"),
        fields: list[tuple[str, str, bool]] = None,
        thumbnail: str = None,
        image: str = None,
        footer: tuple[str, str] = None,
        timestamp: datetime.datetime= None

) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp = timestamp
    )

    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

    if thumbnail:
        embed.set_thumbnail(url= thumbnail)

    if image:
        embed.set_image(url=image)

    if footer:
        text, url =  footer
        embed.set_footer(text=text, icon_url= url if url else  None)



    return embed



