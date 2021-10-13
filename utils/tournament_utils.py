import sys
from logging import getLogger

import discord

from internal.database import (
    BonusData,
    HardcoreData,
    MildcoreData,
    TimeAttackData,
    TopThree,
)
from utils.embeds import doom_embed
from utils.pb_utils import display_record
from utils.views import Confirm, Paginator

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


def category_sort(message):
    if message.channel.id == constants_bot.TA_CHANNEL_ID:
        which_category = "TIMEATTACK"
    elif message.channel.id == constants_bot.MC_CHANNEL_ID:
        which_category = "MILDCORE"
    elif message.channel.id == constants_bot.HC_CHANNEL_ID:
        which_category = "HARDCORE"
    elif message.channel.id == constants_bot.BONUS_CHANNEL_ID:
        which_category = "BONUS"
    else:
        return None
    return which_category


async def tournament_boards(category, ctx=None, guild=None):
    """Display boards for scoreboard and leaderboard commands."""
    if ctx:
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
    count = 0
    embed = doom_embed(title=f"{category}")
    embeds = []

    if category == "TIMEATTACK":
        _data_category = TimeAttackData
    elif category == "MILDCORE":
        _data_category = MildcoreData
    elif category == "HARDCORE":
        _data_category = HardcoreData
    else:  # "BONUS"
        _data_category = BonusData

    data_amount = await _data_category.count_documents()

    async for entry in _data_category.find().sort("record", 1):
        if ctx:
            name = discord.utils.find(
                lambda m: m.id == entry.posted_by, ctx.guild.members
            )

        if guild:
            name = discord.utils.find(lambda m: m.id == entry.posted_by, guild.members)

        embed.add_field(
            name=f"#{count + 1} - {name}",
            value=f"> Record: {display_record(entry.record)}\n",
            inline=False,
        )
        if (count + 1) % 10 == 0 or (count + 1) == data_amount:
            embeds.append(embed)
            embed = doom_embed(title=category)

        count += 1
    if guild:
        channel = guild.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID)
    if embeds:
        if ctx:
            if len(embeds) > 1:
                view = Paginator(embeds, ctx.author)
                paginator = await ctx.send(embed=view.formatted_pages[0], view=view)
                await view.wait()
                await paginator.delete()
            else:
                await ctx.send(embed=embeds[0], delete_after=120)
        if guild:
            for e in embeds:
                await channel.send(embed=e)

    else:
        if guild:
            await channel.send(f"No times exist for the {category.lower()} tournament!")
        else:
            await ctx.send(
                f"No times exist for the {category.lower()} tournament!",
                delete_after=15,
            )


async def exporter(category, channel, ctx=None, guild=None):
    top_three: TopThree = await TopThree.find_one({})

    if category == "TIMEATTACK":
        _data_category = TimeAttackData
    elif category == "MILDCORE":
        _data_category = MildcoreData
    elif category == "HARDCORE":
        _data_category = HardcoreData
    else:  # "BONUS"
        _data_category = BonusData

    count = 0
    async for entry in _data_category.find().sort("record", 1):

        if count < 3:
            if category == "TIMEATTACK":
                top_three.ta_podium = top_three.ta_podium + [entry.posted_by]
            elif category == "MILDCORE":
                top_three.mc_podium = top_three.mc_podium + [entry.posted_by]
            elif category == "HARDCORE":
                top_three.hc_podium = top_three.hc_podium + [entry.posted_by]
            else:  # "BONUS"
                top_three.bonus_podium = top_three.bonus_podium + [entry.posted_by]

            await top_three.commit()

        if ctx:
            username = discord.utils.find(
                lambda m: m.id == entry.posted_by, ctx.guild.members
            )
        if guild:
            username = discord.utils.find(
                lambda m: m.id == entry.posted_by, guild.members
            )

        embed = doom_embed(
            title=username.name if username.name else "Unknown",
            url=entry.attachment_url,
        )
        embed.add_field(name=category, value=f"{display_record(entry.record)}")
        embed.set_image(url=entry.attachment_url)
        await channel.send(embed=embed)
        count += 1


async def single_exporter(ctx, category, user: discord.Member = None):
    if category == "TIMEATTACK":
        _data_category = TimeAttackData
    elif category == "MILDCORE":
        _data_category = MildcoreData
    elif category == "HARDCORE":
        _data_category = HardcoreData
    else:  # "BONUS"
        _data_category = BonusData

    async for entry in _data_category.find({"posted_by": user.id}).sort("record", 1):
        username = discord.utils.find(
            lambda m: m.id == entry.posted_by, ctx.guild.members
        )

        embed = doom_embed(
            title=username.name if username.name else "Unknown",
            url=entry.attachment_url,
        )
        embed.add_field(name=category, value=f"{display_record(entry.record)}")
        embed.set_image(url=entry.attachment_url)
        await ctx.send(embed=embed)


async def confirm_collection_drop(ctx, category):
    author = ctx.message.author
    await ctx.message.delete()
    if category == "time attack":
        _collection = TimeAttackData
    elif category == "mildcore":
        _collection = MildcoreData
    elif category == "hardcore":
        _collection = HardcoreData
    elif category == "bonus":
        _collection = BonusData

    view = Confirm("Deletion", author)
    confirmation_msg = await ctx.send(
        f"Are you sure you want to delete all {category + ' ' if category != 'all' else ''}times?",
        view=view,
    )
    await view.wait()
    if view.value:
        if category == "all":
            msg_ta = await ctx.send("Clearing all time attack times... Please wait.")
            await TimeAttackData.collection.drop()
            await msg_ta.edit(
                content="All times in time attack have been cleared.", delete_after=10
            )

            msg_mc = await ctx.send("Clearing all mildcore times... Please wait.")
            await MildcoreData.collection.drop()
            await msg_mc.edit(
                content="All times in mildcore have been cleared.", delete_after=10
            )

            msg_hc = await ctx.send("Clearing all hardcore times... Please wait.")
            await HardcoreData.collection.drop()
            await msg_hc.edit(
                content="All times in hardcore have been cleared.", delete_after=10
            )

            msg_bonus = await ctx.send("Clearing all bonus times... Please wait.")
            await BonusData.collection.drop()
            await msg_bonus.edit(
                content="All times in bonus have been cleared.", delete_after=10
            )

        else:
            msg = await ctx.send(f"Clearing {category} times... Please wait.")
            await _collection.collection.drop()
            await msg.edit(
                content=f"All times {'in' if category != 'all' else ''} {category if category != 'all' else ''} have been cleared.",
                delete_after=10,
            )

    elif not view.value:
        await confirmation_msg.edit(content="Times were not cleared.", delete_after=10)

    elif view.value is None:
        await confirmation_msg.edit(
            content="Timed out! Times were not cleared.", delete_after=10
        )


async def lock_unlock(channel, role, unlock=True):
    overwrite = channel.overwrites_for(role)
    overwrite.send_messages = unlock
    overwrite.attach_files = unlock
    await channel.set_permissions(role, overwrite=overwrite)


def mentions_to_list(mentions):
    combined_mentions_strip = mentions.replace("<@&", "").replace(">", "")
    return [int(x) for x in combined_mentions_strip.split()]
