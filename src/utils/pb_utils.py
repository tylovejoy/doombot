import asyncio
import datetime
import re

import discord
import internal.constants as constants
import pymongo
from internal.database import MapData, WorldRecords
from utils.embeds import doom_embed
from utils.views import Paginator


async def boards(ctx, map_code, level, title, query):
    count = 1
    exists = False
    embed = doom_embed(title=f"{title}")
    async for entry in WorldRecords.find(query).sort("record", 1).limit(10):
        exists = True
        try:
            name = discord.utils.find(
                lambda m: m.id == entry.posted_by, ctx.guild.members
            ).name
        except AttributeError:
            name = entry.name
        embed.add_field(
            name=f"#{count} - {name}",
            value=(
                f"> Record: {display_record(entry.record)}\n"
                f"> Verified: {constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI}"
            ),
            inline=False,
        )
        count += 1
    if exists:
        m = await ctx.send(embed=embed)
    else:
        m = await ctx.send(f"No scoreboard for {map_code} level {level.upper()}!")
    await asyncio.sleep(60)
    await m.delete()
    await ctx.message.delete()


def is_time_format(s):
    """Check if string is in HH:MM:SS.SS format or a legal variation."""
    return bool(
        re.compile(
            r"(?<!.)(\d{1,2})?:?(\d{2})?:?(?<!\d)(\d{1,2})\.?\d{1,2}?(?!.)"
        ).match(s)
    )


def time_convert(time_input):
    """Convert time (str) into seconds (float)."""
    time_list = time_input.split(":")
    if len(time_list) == 1:
        return float(time_list[0])
    elif len(time_list) == 2:
        return float((int(time_list[0]) * 60) + float(time_list[1]))
    elif len(time_list) == 3:
        return float(
            (int(time_list[0]) * 3600) + (int(time_list[1]) * 60) + float(time_list[2])
        )
    return


def display_record(record):
    """Display record in HH:MM:SS.SS format."""
    if check_negative(record):
        return format_timedelta(record)
    elif str(datetime.timedelta(seconds=record)).count(".") == 1:
        return str(datetime.timedelta(seconds=record))[: -4 or None]
    return str(datetime.timedelta(seconds=record)) + ".00"


def check_negative(s):
    try:
        f = float(s)
        if f < 0:
            return True
        # Otherwise return false
        return False
    except ValueError:
        return False


def format_timedelta(td):
    if datetime.timedelta(seconds=td) < datetime.timedelta(0):
        return "-" + format_timedelta(-td)
    else:
        return str(td)


async def search_all_pbs(ctx, query, name=""):
    # init vars
    row, embeds = 0, []
    author = ctx.message.author
    embed = doom_embed(title=name)
    count = await MapData.count_documents(query)

    async for entry in MapData.find(query).sort([("code", pymongo.ASCENDING)]):

        # Every 10th embed field, create a embed obj and add to a list
        if row != 0 and (row % 10 == 0 or count - 1 == row):

            embed.add_field(
                name=f"{entry.code} - {entry.level}",
                value=f"> Record: {entry.record}",
                inline=False,
            )
            embeds.append(embed)
            embed = discord.Embed(title=name)

        # Create embed fields for fields 1 thru 9
        elif row % 10 != 0 or row == 0:
            embed.add_field(
                name=f"{entry.code} - {entry.level}",
                value=f"> Record: {entry.record}",
                inline=False,
            )

        # If only one page
        if count == 1:
            embeds.append(embed)
        row += 1

    # Displays paginated embeds
    if row > 1:
        view = Paginator(embeds, author)
        paginator = await ctx.send(embed=view.formatted_pages[0], view=view)
        await view.wait()
        await paginator.delete()
    elif row == 1:
        await ctx.send(embed=embeds[0], delete_after=120)

    else:
        m = await ctx.send(f"Nothing exists for {name}!")
        await asyncio.sleep(10)
        try:
            await m.delete()
        except Exception:  # TODO: Correct exception?
            pass
