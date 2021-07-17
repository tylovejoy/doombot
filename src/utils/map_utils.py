import asyncio
import re
import sys

import discord
import internal.constants as constants
import pymongo
from internal.database import MapData
from utils.embeds import doom_embed
from utils.views import Paginator

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


async def searchmap(
    ctx, query: dict, map_type="", map_name="", creator="", map_code=""
):
    """Search database for query and displays it.

    Args:
        ctx (:obj: `commands.Context`)
        query (dict): Query for database
        map_type (str, optional): Type of map to search
        map_name (str, optional): Name of map to seach
        creator (str, optional): Creator of map to search
        map_code (str, optional): Map code to search

    Returns:
        None

    """
    # Checks for map_type, if exists
    try:
        await ctx.message.delete()
    except Exception:  # TODO: correct exception?
        pass
    if map_type:
        if map_type not in constants.TYPES_OF_MAP:
            await ctx.send(
                f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
            )
            return

    # init vars
    row, embeds = 0, []

    embed = doom_embed(title=map_name or creator or map_code or map_type)
    count = await MapData.count_documents(query)

    async for entry in MapData.find(query).sort([("map_name", pymongo.ASCENDING)]):

        # Every 10th embed field, create a embed obj and add to a list
        if row != 0 and (row % 10 == 0 or count - 1 == row):

            embed.add_field(
                name=f"{entry.code} - {constants.PRETTY_NAMES[entry.map_name]}",
                value=f"> Creator: {entry.creator}\n> Map Types: {', '.join(entry.type)}\n> Description: {entry.desc}",
                inline=False,
            )
            embeds.append(embed)
            embed = doom_embed(title=map_name or creator or map_code or map_type)

        # Create embed fields for fields 1 thru 9
        elif row % 10 != 0 or row == 0:
            embed.add_field(
                name=f"{entry.code} - {constants.PRETTY_NAMES[entry.map_name]}",
                value=f"> Creator: {entry.creator}\n> Map Types: {', '.join(entry.type)}\n> Description: {entry.desc}",
                inline=False,
            )

        # If only one page
        if count == 1:
            embeds.append(embed)
        row += 1

    # Displays paginated embeds
    if row:
        view = Paginator(embeds)
        paginator = await ctx.send(embed=view.formatted_pages[0], view=view)
        await view.wait()
        await paginator.delete()
    else:
        m = await ctx.send(
            f"Nothing exists for {map_name or creator or map_code or map_type}!"
        )
        await asyncio.sleep(10)
        try:
            await m.delete()
        except Exception:  # TODO: Correct exception?
            pass


def normal_map_query(map_name, map_type=""):
    """Create a query string for map search commands.

    Args:
        map_name: The map name a user is searching for.
        map_type: The map type a user is searching for.

    Returns:
        dict: query for map search command, depending on if map_type is given.

    """
    apostrophe = "'"
    if map_type:
        return {
            "map_name": f"{''.join(map_name.split()).lower().replace(apostrophe, '').replace(':', '')}",
            "type": map_type.upper(),
        }
    return {
        "map_name": f"{''.join(map_name.split()).lower().replace(apostrophe, '').replace(':', '')}"
    }


async def map_submit_embed(document, title):
    embed = doom_embed(title=title)
    embed.add_field(
        name=f"{document.code}",
        value=(
            f"> Map: {constants.PRETTY_NAMES[document.map_name]}\n"
            f"> Creator: {document.creator}\n"
            f"> Map Types: {' '.join(document.type)}\n"
            f"> Description: {document.desc}"
        ),
        inline=False,
    )
    return embed


async def map_edit_confirmation(confirmed, msg, document):
    if confirmed is True:
        await msg.edit(content=f"{document.code} has been edited.")
        await document.commit()
    elif confirmed is False:
        await msg.edit(content=f"{document.code} has not been edited.")
    elif confirmed is None:
        await msg.edit(
            content=f"Submission timed out! {document.code} has not been edited."
        )
    await msg.clear_reactions()
    await asyncio.sleep(10)
    await msg.delete()


async def map_edit_checks(ctx, search) -> int:
    """User input validation. Display error to user.

    Returns:
        (int): if arguments do not pass checks return 0, else 1
    """
    if not search:
        return -1
    # Only allow original poster OR whitelisted roles to delete.
    if search.posted_by != ctx.author.id:
        if not bool(
            any(role.id in constants_bot.ROLE_WHITELIST for role in ctx.author.roles)
        ):
            return 0
    return 1


def convert_short_types(map_type):
    """Convert user inputted map_type to proper map_type if using abbreviation."""
    if map_type in ["MULTI", "MULTILVL", "MULTILEVEL"]:
        return "MULTILEVEL"
    elif map_type in ["PIO", "PIONEER"]:
        return "PIONEER"
    elif map_type in ["HC", "HARDCORE"]:
        return "HARDCORE"
    elif map_type in ["MC", "MILDCORE"]:
        return "MILDCORE"
    elif map_type in ["TA", "TIMEATTACK", "TIME-ATTACK"]:
        return "TIME-ATTACK"
    elif map_type in ["FRAMEWORK", "FW"]:
        return "FRAMEWORK"
    return map_type


def map_name_converter(map_name):
    """Convert variations of map_name to proper map_name for database."""
    map_name = map_name.lower()
    for i in range(len(constants.ALL_MAP_NAMES)):
        if map_name in constants.ALL_MAP_NAMES[i]:
            return constants.ALL_MAP_NAMES[i][0]
    return


def map_code_regex(m):
    if re.match(r"^[a-zA-Z0-9]+$", m):
        return True


def map_type_check(m):
    m = [convert_short_types(x.upper()) for x in m.split()]
    # Checks map_type(s) exists
    for x in m:
        if x not in constants.TYPES_OF_MAP:
            return
    return True
