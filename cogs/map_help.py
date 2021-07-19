import sys
from logging import getLogger

from discord.ext import commands

import internal.constants as constants
from internal.database import Guides
from utils.map_utils import guide_duplicate_check
from utils.multiple_choice import MultipleChoice
from utils.views import Confirm, GuidePaginator

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


class MapHelp(commands.Cog, name="Helpful Map Commands"):
    """Helpful map commands/utility.

    Shows user acceptable map names and map types to use with other commands.
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if commands are used in MAP_CHANNEL and MAP_SUBMIT_CHANNEL."""
        if (
            ctx.channel.id
            in (
                constants_bot.MAP_CHANNEL_ID,
                constants_bot.MAP_SUBMIT_CHANNEL_ID,
            )
            or (ctx.guild is None)
        ):
            return True

    @commands.command(
        help="Shows all acceptable map names for commands",
        brief="Shows map names for commands",
    )
    async def maps(self, ctx):
        """Display acceptable map names for use in other commands."""
        await ctx.message.delete()
        post = ""
        for maps in constants.ALL_MAP_NAMES:
            post += " | ".join(maps) + "\n"
        await ctx.send(f"```Acceptable map names:\n{post}```", delete_after=30)

    @commands.command(
        aliases=["types"],
        help="Shows all acceptable map types for commands",
        brief="Shows map types for commands",
    )
    async def maptypes(self, ctx):
        """Display acceptable map types for use in other commands."""
        await ctx.message.delete()
        await ctx.send(
            "Map types:\n```\n" + "\n".join(constants.TYPES_OF_MAP) + "```",
            delete_after=30,
        )


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(MapHelp(bot))
