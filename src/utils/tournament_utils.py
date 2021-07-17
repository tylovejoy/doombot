import logging
import sys
import discord
from disputils import BotEmbedPaginator

from database.BonusData import BonusData
from database.HardcoreData import HardcoreData
from database.MildcoreData import MildcoreData
from database.TimeAttackData import TimeAttackData
from internal.pb_utils import display_record
from internal import constants
from internal import confirmation

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


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
    count = 0
    embed = discord.Embed(title=f"{category}")
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
            embed = discord.Embed(title=category)

        count += 1
    if guild:
        channel = guild.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID)
    if embeds:
        if ctx:
            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()
        if guild:
            for e in embeds:
                await channel.send(embed=e)

    else:
        if guild:
            await channel.send(f"No times exist for the {category.lower()} tournament!")
        else:
            await ctx.send(f"No times exist for the {category.lower()} tournament!")


async def exporter(category, channel, ctx=None, guild=None):
    if category == "TIMEATTACK":
        _data_category = TimeAttackData
    elif category == "MILDCORE":
        _data_category = MildcoreData
    elif category == "HARDCORE":
        _data_category = HardcoreData
    else:  # "BONUS"
        _data_category = BonusData

    async for entry in _data_category.find().sort("record", 1):
        if ctx:
            username = discord.utils.find(
                lambda m: m.id == entry.posted_by, ctx.guild.members
            )
        if guild:
            username = discord.utils.find(
                lambda m: m.id == entry.posted_by, guild.members
            )

        embed = discord.Embed(
            title=username.name,
            url=entry.attachment_url,
        )
        embed.add_field(name=category, value=f"{display_record(entry.record)}")
        embed.set_image(url=entry.attachment_url)
        await channel.send(embed=embed)


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

        embed = discord.Embed(
            title=username.name,
            url=entry.attachment_url,
        )
        embed.add_field(name=category, value=f"{display_record(entry.record)}")
        embed.set_image(url=entry.attachment_url)
        await ctx.send(embed=embed)


async def confirm_collection_drop(ctx, category):
    if category == "time attack":
        _collection = TimeAttackData
    elif category == "mildcore":
        _collection = MildcoreData
    elif category == "hardcore":
        _collection = HardcoreData
    elif category == "bonus":
        _collection = BonusData

    confirmation_msg = await ctx.send(
        f"Are you sure you want to delete all {category + ' ' if category != 'all' else ''}times?"
    )
    confirmed = await confirmation.confirm(ctx, confirmation_msg)
    if confirmed is True:

        if category == "all":
            msg_ta = await ctx.send("Clearing all time attack times... Please wait.")
            await TimeAttackData.collection.drop()
            await msg_ta.edit(content="All times in time attack have been cleared.")

            msg_mc = await ctx.send("Clearing all mildcore times... Please wait.")
            await MildcoreData.collection.drop()
            await msg_mc.edit(content="All times in mildcore have been cleared.")

            msg_hc = await ctx.send("Clearing all hardcore times... Please wait.")
            await HardcoreData.collection.drop()
            await msg_hc.edit(content="All times in hardcore have been cleared.")

            msg_bonus = await ctx.send("Clearing all bonus times... Please wait.")
            await BonusData.collection.drop()
            await msg_bonus.edit(content="All times in bonus have been cleared.")

        else:
            msg = await ctx.send(f"Clearing {category} times... Please wait.")
            await _collection.collection.drop()
            await msg.edit(
                content=f"All times {'in' if category != 'all' else ''} {category if category != 'all' else ''} have been cleared."
            )

    elif confirmed is False:
        await confirmation_msg.edit(
            content="Times were not cleared.",
        )

    elif confirmed is None:
        await confirmation_msg.edit(
            content="Timed out! Times were not cleared.",
        )


async def lock_unlock(channel, role, unlock=True):
    overwrite = channel.overwrites_for(role)
    overwrite.send_messages = unlock
    overwrite.attach_files = unlock
    await channel.set_permissions(role, overwrite=overwrite)


def mentions_to_list(mentions):
    combined_mentions_strip = mentions.replace("<@&", "").replace(">", "")
    return [int(x) for x in combined_mentions_strip.split()]
