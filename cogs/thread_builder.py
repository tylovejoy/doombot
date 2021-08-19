import sys
from logging import getLogger

import discord
from discord.ext import commands

from utils.embeds import doom_embed

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


class ThreadBuilder(commands.Cog, name="Thread Builder"):
    """ThreadBuilder"""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_any_role(*constants_bot.THREAD_BUILD_WHITELIST)
    @commands.command(
        help="Build a thread with a title and image URL. URL is optional.",
        brief="Build a thread with a title and image url",
        aliases=[],
    )
    async def createthread(
        self, ctx: commands.Context, title: str, image_url: str = None
    ):
        await ctx.message.delete()
        embed = discord.Embed(title=title, color=discord.Color.dark_purple())
        try:
            if image_url is not None:
                embed.set_image(url=image_url)
        except Exception:
            pass
        else:
            message = await ctx.send(embed=embed)
            await message.start_thread(name=title, auto_archive_duration=10080)


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(ThreadBuilder(bot))
