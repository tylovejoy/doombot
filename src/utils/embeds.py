import discord
from discord import Embed


def doom_embed(title: str, desc: str = "", url: str = "") -> Embed:
    embed = discord.Embed(title=title, description=desc, color=0x000001, url=url)
    embed.set_author(name="DoomBot says")
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/app-icons/801483463642841150/4316132ab7deebe9b1bc93fc2fea576b.png"
    )
    return embed
