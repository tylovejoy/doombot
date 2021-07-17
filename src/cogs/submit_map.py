import asyncio
import sys
from logging import getLogger
from discord.ext import commands
from internal.constants import TYPES_OF_MAP
from internal.database import MapData
from utils.embeds import doom_embed
from utils.form import Form
from utils.map_utils import (
    map_code_regex,
    map_name_converter,
    map_type_check,
    convert_short_types,
    map_submit_embed,
    _accept,
)
from utils.utilities import delete_messages
from views.confirm import Confirm

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


class SubmitMap(commands.Cog, name="Map submission/deletion/editing"):
    """SubmitMap"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if command is used in MAP_SUBMIT_CHANNEL."""
        if ctx.channel.id == constants_bot.MAP_SUBMIT_CHANNEL_ID:
            return True

    @commands.command(
        help=(
            "Submit map codes\n\n"
            "**Use command without arguments for a simpler submission.**"
            "You can add multiple creators and map types!\n\n"  # noqa: E501
            f"Here is a list of map codes that can be used:\n{' | '.join(constants.TYPES_OF_MAP)}"
            "Use 'cancel' at any time to cancel the submission."
        ),
        brief="Submit map code",
    )
    async def submitmap(
        self, ctx, map_code=None, map_name=None, map_type=None, creator=None, *, desc=""
    ):
        """Submit a map to database."""

        message_cache = [ctx.message]
        if map_code is None or map_name is None or map_type is None or creator is None:
            if any([map_code, map_name, map_type, creator]) and not all(
                [map_code, map_name, map_type, creator]
            ):
                warn = await ctx.send(
                    "There was some info missing. Please answer the following questions."
                )
                message_cache.append(warn)

            form = Form(ctx, title="Map Submission Wizard")

            form.add_question(
                question="What is the map code?",
                key="map_code",
                validation=map_code_regex,
            )
            form.add_question(
                question=(
                    "What map is it?\nMany variations of map names work such as "
                    "'King's Row', 'Kings Row', 'kr', 'kings', 'kingsrow', etc."
                ),
                key="map_name",
                validation=map_name_converter,
            )
            form.add_question(
                question=f"What is/are the map type(s)?\n{' | '.join(TYPES_OF_MAP)}",
                key="map_type",
                validation=map_type_check,
            )
            form.add_question("Who is/are the map creator(s)?", "creator")
            form.add_question("What is the map description?", "desc")

            result = await form.execute()

            if result is None:
                cancel = await ctx.send("Map submission cancelled.")
                message_cache.append(cancel)
                await asyncio.sleep(10)
                await delete_messages(message_cache)
                return

            map_code = result.map_code
            map_name = result.map_name
            map_type = [convert_short_types(x.upper()) for x in result.map_type.split()]
            creator = result.creator
            desc = result.desc
        else:
            if not map_code_regex(map_code):
                reject = await ctx.send(
                    "Only letters A-Z and numbers 0-9 allowed in <map_code>. "
                    "Map submission rejected."
                )
                message_cache.append(reject)
                await asyncio.sleep(10)
                await delete_messages(message_cache)
                return

            if not map_name_converter(map_name):
                reject = await ctx.send(
                    "<map_name> doesn't exist! Map submission rejected. "
                    "Use `/maps` for a list of acceptable maps."
                )
                message_cache.append(reject)
                await asyncio.sleep(10)
                await delete_messages(message_cache)
                return

            if not map_type_check(map_type):
                reject = await ctx.send(
                    "<map_type> doesn't exist! Map submission rejected. "
                    "Use `/maptypes` for a list of acceptable map types."
                )
                message_cache.append(reject)
                await asyncio.sleep(10)
                await delete_messages(message_cache)
                return

            map_type = [convert_short_types(x.upper()) for x in map_type.split()]

        map_code = map_code.upper()
        count = await MapData.count_documents({"code": map_code})

        if count != 0:
            exists = await ctx.send(
                f"{map_code} already exists! Map submission rejected."
            )
            message_cache.append(exists)
            await delete_messages(message_cache)
            return

        new_map_name = map_name_converter(map_name)

        submission = MapData(
            **dict(
                code=map_code,
                creator=creator,
                map_name=new_map_name,
                desc=desc,
                posted_by=ctx.author.id,
                type=map_type,
            )
        )

        embed = await map_submit_embed(submission, "New Map")

        view = Confirm(embed)
        confirm = await ctx.send("Is this correct?", embed=embed, view=view)
        # Wait for the View to stop listening for input...
        await view.wait()
        if view.value is None:  # Timed out
            pass

        elif view.value:  # Accept
            await submission.commit()
            new_map_channel = self.bot.get_channel(constants_bot.NEW_MAPS_CHANNEL_ID)
            await new_map_channel.send(embed=embed)
        else:  # Reject
            pass

        message_cache.append(confirm)
        await delete_messages(message_cache)


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(SubmitMap(bot))
