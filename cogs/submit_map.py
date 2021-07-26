import asyncio
import sys
from logging import getLogger

from discord.ext import commands

from internal.constants import PRETTY_NAMES, TYPES_OF_MAP
from internal.database import MapData
from utils.form import Form
from utils.map_utils import (
    convert_short_types,
    map_code_regex,
    map_edit_checks,
    map_name_converter,
    map_submit_embed,
    map_type_check,
)
from utils.utilities import delete_messages
from utils.views import Confirm

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
            f"Here is a list of map codes that can be used:\n{' | '.join(TYPES_OF_MAP)}"
            "Use 'cancel' at any time to cancel the submission."
        ),
        brief="Submit map code",
    )
    async def submitmap(
        self, ctx, map_code=None, map_name=None, map_type=None, creator=None, *, desc=""
    ):
        """Submit a map to database."""
        author = ctx.message.author
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
            await asyncio.sleep(10)
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

        view = Confirm("Submission", author)
        confirm = await ctx.send("Is this correct?", embed=embed, view=view)
        # Wait for the View to stop listening for input...
        await view.wait()
        if view.value is None:  # Timed out
            pass

        elif view.value:  # Accept
            await submission.commit()
            new_map_channel = self.bot.get_channel(constants_bot.NEW_MAPS_CHANNEL_ID)
            new_map = await new_map_channel.send(embed=embed)
            await new_map.start_thread(
                name=f"{map_code} - {PRETTY_NAMES[new_map_name]} by {creator}"
            )
        else:  # Reject
            pass

        message_cache.append(confirm)
        await delete_messages(message_cache)

    @commands.command(
        help="Delete map code\nOnly original posters and mods can delete a map code.",
        brief="Delete map code",
    )
    async def deletemap(self, ctx, map_code):
        """Delete a specific map_code."""
        author = ctx.message.author
        message_cache = [ctx.message]
        map_code = map_code.upper()

        search = await MapData.find_one({"code": map_code})
        check = await map_edit_checks(ctx, search)
        if check < 1:
            if check == -1:
                msg = await ctx.channel.send(f"{map_code} does not exist.")
                message_cache.append(msg)
            elif check == 0:
                msg = await ctx.channel.send(
                    "You do not have sufficient permissions. Map was not affected."
                )
                message_cache.append(msg)
                await asyncio.sleep(10)
            await delete_messages(message_cache)
            return

        embed = await map_submit_embed(search, "Map Deletion")

        view = Confirm("Deletion", author)
        confirm = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()
        if view.value is None:  # Timed out
            pass
        elif view.value:  # Accept
            await search.delete()
        else:  # Reject
            pass

        message_cache.append(confirm)
        await delete_messages(message_cache)

    @commands.command(
        help="Edit description for a certain map code. <desc> will overwrite current description.\nOnly original posters and mods can edit a map code.",
        brief="Edit description for a certain map code",
    )
    async def editdesc(self, ctx, map_code, *, desc):
        """Edit a specific map_code's description."""
        author = ctx.message.author
        message_cache = [ctx.message]
        map_code = map_code.upper()

        search = await MapData.find_one({"code": map_code})

        check = await map_edit_checks(ctx, search)
        if check < 1:
            if check == -1:
                msg = await ctx.channel.send(f"{map_code} does not exist.")
                message_cache.append(msg)
            elif check == 0:
                msg = await ctx.channel.send(
                    "You do not have sufficient permissions. Map was not affected."
                )
                message_cache.append(msg)
                await asyncio.sleep(10)
            await delete_messages(message_cache)
            return

        search.desc = desc

        embed = await map_submit_embed(search, "Edit Map Description")

        view = Confirm("Edit", author)
        confirm = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()
        if view.value is None:  # Timed out
            pass
        elif view.value:  # Accept
            await search.commit()
        else:  # Reject
            pass

        message_cache.append(confirm)
        await delete_messages(message_cache)

    @commands.command(
        help=(
            "Edit map types for a certain map code.\n"
            "<map_type> will overwrite current map types.\n"
            "Only original posters and mods can edit a map code."
        ),
        brief="Edit map types for a certain map code",
    )
    async def edittypes(self, ctx, map_code, *, map_type):
        """Edit a specific map_code's map_types."""
        author = ctx.message.author
        message_cache = [ctx.message]
        map_code = map_code.upper()

        search = await MapData.find_one({"code": map_code})

        check = await map_edit_checks(ctx, search)
        if check < 1:
            if check == -1:
                msg = await ctx.channel.send(f"{map_code} does not exist.")
                message_cache.append(msg)
            elif check == 0:
                msg = await ctx.channel.send(
                    "You do not have sufficient permissions. Map was not affected."
                )
                message_cache.append(msg)
                await asyncio.sleep(10)
            await delete_messages(message_cache)
            return

        map_type = [convert_short_types(x.upper()) for x in map_type.split()]

        for x in map_type:
            if x not in TYPES_OF_MAP:
                m = await ctx.send(
                    "<map_type> doesn't exist! Map submission rejected. "
                    "Use `/maptypes` for a list of acceptable map types."
                )
                await asyncio.sleep(10)
                message_cache.append(m)
                await delete_messages(message_cache)
                return

        search.type = map_type

        embed = await map_submit_embed(search, "Edit Map Types")

        view = Confirm("Edit", author)
        confirm = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()
        if view.value is None:  # Timed out
            pass
        elif view.value:  # Accept
            await search.commit()
        else:  # Reject
            pass

        message_cache.append(confirm)
        await delete_messages(message_cache)

    @commands.command(
        help="Edit the map code for a certain map code.\n"
        "Only original posters and mods can edit a map code.",
        brief="Edit the map code for a certain map code",
    )
    async def editcode(self, ctx, map_code, new_map_code):
        """Edit a specific map_code's map_code."""
        author = ctx.message.author
        message_cache = [ctx.message]
        map_code = map_code.upper()
        new_map_code = new_map_code.upper()

        search = await MapData.find_one({"code": map_code})

        check = await map_edit_checks(ctx, search)
        if check < 1:
            if check == -1:
                msg = await ctx.channel.send(f"{map_code} does not exist.")
                message_cache.append(msg)
            elif check == 0:
                msg = await ctx.channel.send(
                    "You do not have sufficient permissions. Map was not affected."
                )
                message_cache.append(msg)
                await asyncio.sleep(10)
            await delete_messages(message_cache)
            return

        if not map_code_regex(new_map_code):
            m = await ctx.send(
                "Only letters A-Z and numbers 0-9 allowed in <map_code>. "
                "Map submission rejected."
            )
            await asyncio.sleep(10)
            message_cache.append(m)
            await delete_messages(message_cache)
            return

        search.code = new_map_code

        embed = await map_submit_embed(search, "Edit Map Code")

        view = Confirm("Edit", author)
        confirm = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()
        if view.value is None:  # Timed out
            pass
        elif view.value:  # Accept
            await search.commit()
        else:  # Reject
            pass

        message_cache.append(confirm)
        await delete_messages(message_cache)

    @commands.command(
        help="Edit the creator(s) for a certain map code.\n"
        "Only original posters and mods can edit the creator(s).",
        brief="Edit the creator(s) for a certain map code",
        aliases=["editcreators"],
    )
    async def editcreator(self, ctx, map_code, creator):
        """Edit a specific map_code's creators."""
        author = ctx.message.author
        message_cache = [ctx.message]
        map_code = map_code.upper()

        search = await MapData.find_one({"code": map_code})

        check = await map_edit_checks(ctx, search)
        if check < 1:
            if check == -1:
                msg = await ctx.channel.send(f"{map_code} does not exist.")
                message_cache.append(msg)
            elif check == 0:
                msg = await ctx.channel.send(
                    "You do not have sufficient permissions. Map was not affected."
                )
                message_cache.append(msg)
                await asyncio.sleep(10)
            await delete_messages(message_cache)
            return

        search.creator = creator

        embed = await map_submit_embed(search, "Edit Map Creator(s)")

        view = Confirm("Edit", author)
        confirm = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()
        if view.value is None:  # Timed out
            pass
        elif view.value:  # Accept
            await search.commit()
        else:  # Reject
            pass

        message_cache.append(confirm)
        await delete_messages(message_cache)


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(SubmitMap(bot))
