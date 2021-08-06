import discord
from discord import Embed


def doom_embed(
    title: str, desc: str = "", url: str = "", color: hex = 0x000001
) -> Embed:
    embed = discord.Embed(title=title, description=desc, color=color, url=url)
    embed.set_author(name="DoomBot says")
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/app-icons/801483463642841150/4316132ab7deebe9b1bc93fc2fea576b.png"
    )
    return embed


def hall_of_fame(title: str, desc: str = "") -> Embed:
    embed = discord.Embed(title=title, description=desc, color=0xF7BD00)
    embed.set_author(name="Hall of Fame")
    embed.set_thumbnail(url="https://clipartart.com/images/dog-trophy-clipart-2.png")
    return embed
