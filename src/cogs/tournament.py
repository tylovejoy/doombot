import asyncio
import datetime
import sys
from logging import getLogger

import dateparser
import discord
from discord.ext import commands, tasks
from disputils import MultipleChoice
from internal.database import (
    BonusData,
    HardcoreData,
    MildcoreData,
    Schedule,
    TimeAttackData,
)
from utils.embeds import doom_embed
from utils.pb_utils import display_record, time_convert
from utils.tournament_utils import (
    category_sort,
    confirm_collection_drop,
    exporter,
    lock_unlock,
    mentions_to_list,
    single_exporter,
    tournament_boards,
)
from utils.tourrnament_wizard import TournamentWizard
from utils.views import Confirm, TournamentChoices

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


def viewable_channels():
    def predicate(ctx):
        return ctx.channel.id in [
            constants_bot.TOURNAMENT_CHAT_CHANNEL_ID,
            constants_bot.ORG_CHANNEL_ID,
            constants_bot.EXPORT_SS_CHANNEL_ID,
            constants_bot.MAP_SELECT_CHANNEL_ID,
        ]

    return commands.check(predicate)


class Tournament(commands.Cog, name="Tournament"):
    """Tournament"""

    def __init__(self, bot):
        self.bot = bot
        self.schedule_cache = None

        logger.info("schedule_checker has started.")
        self.schedule_checker.start()
        self.guild = self.bot.get_guild(constants_bot.GUILD_ID)

        self.ta_channel = self.guild.get_channel(constants_bot.TA_CHANNEL_ID)
        self.mc_channel = self.guild.get_channel(constants_bot.MC_CHANNEL_ID)
        self.hc_channel = self.guild.get_channel(constants_bot.HC_CHANNEL_ID)
        self.bonus_channel = self.guild.get_channel(constants_bot.BONUS_CHANNEL_ID)

        self.info_channel = self.guild.get_channel(
            constants_bot.TOURNAMENT_INFO_CHANNEL_ID
        )
        self.export_channel = self.guild.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID)

        self.ta_role = self.guild.get_role(constants_bot.TA_ROLE_ID)
        self.mc_role = self.guild.get_role(constants_bot.MC_ROLE_ID)
        self.hc_role = self.guild.get_role(constants_bot.HC_ROLE_ID)
        self.bonus_role = self.guild.get_role(constants_bot.BONUS_ROLE_ID)

        self.trifecta_role = self.guild.get_role(constants_bot.TRIFECTA_ROLE_ID)
        self.bracket_role = self.guild.get_role(
            constants_bot.BRACKET_TOURNAMENT_ROLE_ID
        )

    def cog_check(self, ctx):
        if ctx.channel.id in [
            constants_bot.TOURNAMENT_CHAT_CHANNEL_ID,
            constants_bot.HC_CHANNEL_ID,
            constants_bot.TA_CHANNEL_ID,
            constants_bot.MC_CHANNEL_ID,
            constants_bot.BONUS_CHANNEL_ID,
            constants_bot.ORG_CHANNEL_ID,
            constants_bot.EXPORT_SS_CHANNEL_ID,
            constants_bot.MAP_SELECT_CHANNEL_ID,
        ]:
            return True

    @tasks.loop(seconds=30)
    async def schedule_checker(self):
        self.schedule_cache = Schedule.find({})
        count = await Schedule.count_documents({})

        if count:
            current_time = datetime.datetime.now()

            async for s in self.schedule_cache:
                if s.start_time is not None and (
                    current_time
                    >= s.start_time
                    != datetime.datetime(year=1, month=1, day=1)
                ):
                    logger.info("Starting scheduled tournment.")
                    await self._start_round(s.mentions, s.embed_dict)
                    s.start_time = datetime.datetime(year=1, month=1, day=1)
                    await s.commit()

                if current_time >= s.schedule:
                    logger.info("Ending scheduled tournment.")
                    await self._end_round(s.mentions)
                    await s.delete()

    async def _start_round(self, mentions, embed_dict):
        list_mentions = mentions_to_list(mentions)

        if constants_bot.BRACKET_TOURNAMENT_ROLE_ID in list_mentions:
            await lock_unlock(self.ta_channel, self.bracket_role, unlock=True)
            await lock_unlock(self.mc_channel, self.bracket_role, unlock=True)
            await lock_unlock(self.hc_channel, self.bracket_role, unlock=True)
            await lock_unlock(self.bonus_channel, self.bracket_role, unlock=True)

        if constants_bot.TRIFECTA_ROLE_ID in list_mentions:
            await lock_unlock(self.ta_channel, self.trifecta_role, unlock=True)
            await lock_unlock(self.mc_channel, self.trifecta_role, unlock=True)
            await lock_unlock(self.hc_channel, self.trifecta_role, unlock=True)
            await lock_unlock(self.bonus_channel, self.trifecta_role, unlock=True)

        if constants_bot.TA_ROLE_ID in list_mentions:
            await lock_unlock(self.ta_channel, self.ta_role, unlock=True)

        if constants_bot.MC_ROLE_ID in list_mentions:
            await lock_unlock(self.mc_channel, self.mc_role, unlock=True)

        if constants_bot.HC_ROLE_ID in list_mentions:
            await lock_unlock(self.hc_channel, self.hc_role, unlock=True)

        if constants_bot.BONUS_ROLE_ID in list_mentions:
            await lock_unlock(self.bonus_channel, self.bonus_role, unlock=True)

        start_annoucenment = discord.Embed.from_dict(embed_dict)
        await self.info_channel.send(f"{mentions}", embed=start_annoucenment)

    async def _end_round(self, mentions):
        list_mentions = mentions_to_list(mentions)

        bracket = False
        if constants_bot.BRACKET_TOURNAMENT_ROLE_ID in list_mentions:
            bracket = True
            await lock_unlock(self.ta_channel, self.bracket_role, unlock=False)
            await lock_unlock(self.mc_channel, self.bracket_role, unlock=False)
            await lock_unlock(self.hc_channel, self.bracket_role, unlock=False)
            await lock_unlock(self.bonus_channel, self.bracket_role, unlock=False)

        trifecta = False
        if constants_bot.TRIFECTA_ROLE_ID in list_mentions:
            trifecta = True
            await lock_unlock(self.ta_channel, self.trifecta_role, unlock=False)
            await lock_unlock(self.mc_channel, self.trifecta_role, unlock=False)
            await lock_unlock(self.hc_channel, self.trifecta_role, unlock=False)
            await lock_unlock(self.bonus_channel, self.trifecta_role, unlock=False)

        if constants_bot.TA_ROLE_ID in list_mentions or any([bracket, trifecta]):
            await lock_unlock(self.ta_channel, self.ta_role, unlock=False)

            await self.export_channel.send(f"***{10 * '-'}TIME ATTACK{10 * '-'}***")
            await tournament_boards("TIMEATTACK", guild=self.guild)
            await exporter(
                "TIMEATTACK",
                self.export_channel,
                guild=self.guild,
            )
            await TimeAttackData.collection.drop()

        if constants_bot.MC_ROLE_ID in list_mentions or any([bracket, trifecta]):
            await lock_unlock(self.mc_channel, self.mc_role, unlock=False)

            await self.export_channel.send(f"***{10 * '-'}MILDCORE{10 * '-'}***")
            await tournament_boards("MILDCORE", guild=self.guild)
            await exporter(
                "MILDCORE",
                self.export_channel,
                guild=self.guild,
            )
            await MildcoreData.collection.drop()

        if constants_bot.HC_ROLE_ID in list_mentions or any([bracket, trifecta]):
            await lock_unlock(self.hc_channel, self.hc_role, unlock=False)

            await self.export_channel.send(f"***{10 * '-'}HARDCORE{10 * '-'}***")
            await tournament_boards("HARDCORE", guild=self.guild)
            await exporter(
                "HARDCORE",
                self.export_channel,
                guild=self.guild,
            )
            await HardcoreData.collection.drop()

        if constants_bot.BONUS_ROLE_ID in list_mentions or any([bracket, trifecta]):
            await lock_unlock(self.bonus_channel, self.bonus_role, unlock=False)

            await self.export_channel.send(f"***{10 * '-'}BONUS{10 * '-'}***")
            await tournament_boards("BONUS", guild=self.guild)
            await exporter(
                "BONUS",
                self.export_channel,
                guild=self.guild,
            )
            await BonusData.collection.drop()

        end_announcement = doom_embed(title=f"Tournament Announcement")
        end_announcement.add_field(
            name=f"The round has ended!",
            value=f"Stay tuned for the next announcement!",
        )
        await self.info_channel.send(f"{mentions}", embed=end_announcement)

    @commands.command(
        name="submit",
        help="Record must be in HH:MM:SS.ss format. Screenshot must be attached to the submission message.",
        brief="Submit times to tournament.",
    )
    async def submit(self, ctx, record):

        category = category_sort(ctx.message)
        if category is None:
            return

        if not ctx.message.attachments:
            await ctx.send(
                "No attachment found. Please submit time with attachment in the same message."
            )
            return

        record_in_seconds = time_convert(record)

        # Validates time
        if not record_in_seconds:
            await ctx.send("Invalid time. Map submission rejected.")
            return

        # Finds document
        if category == "TIMEATTACK":
            _category_data = TimeAttackData
        elif category == "MILDCORE":
            _category_data = MildcoreData
        elif category == "HARDCORE":
            _category_data = HardcoreData
        else:  # "BONUS"
            _category_data = BonusData

        search = await _category_data.find_one({"posted_by": ctx.author.id})

        # If document is found, verifies if submitted time is faster (if verified).
        if (search and (record_in_seconds >= search.record)) is True:
            await ctx.channel.send(
                "Times submitted for the tournament needs to be faster than prior submissions."
            )
            return

        # Create new TournamentData document, if none exists.
        if not search:
            if category == "TIMEATTACK":
                _new_submission = TimeAttackData
            elif category == "MILDCORE":
                _new_submission = MildcoreData
            elif category == "HARDCORE":
                _new_submission = HardcoreData
            else:  # "BONUS"
                _new_submission = BonusData

            search = _new_submission(
                **{
                    "posted_by": ctx.author.id,
                    "name": ctx.author.name,
                    "record": record_in_seconds,
                    "attachment_url": ctx.message.attachments[0].url,
                }
            )

        embed = doom_embed(title="New Submission")
        # Verification embed for user.
        embed.add_field(
            name=f"Name: {discord.utils.find(lambda m: m.id == search.posted_by, ctx.guild.members).name}",
            value=(
                f"> Category: {category}\n"
                f"> Record: {display_record(record_in_seconds)}\n"
            ),
            inline=False,
        )

        view = Confirm("Submission", ctx.message.author)
        msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await msg.edit(content="Submission accepted", delete_after=15)
            # Update record
            search.record = record_in_seconds
            search.name = ctx.author.name
            search.attachment_url = ctx.message.attachments[0].url
            # Save document
            await search.commit()

        elif not view.value:
            await ctx.message.delete()
            await msg.edit(
                content="Submission has not been accepted.",
                delete_after=15,
            )

        elif view.value is None:
            await ctx.message.delete()
            await msg.edit(
                content="Submission timed out! Submission has not been accepted.",
                delete_after=15,
            )

    @commands.command(
        help="Delete a submission to tournament. Optional argument <user> for mod usage.",
        brief="Delete a submission to tournament",
        name="delete",
    )
    async def _delete(self, ctx, user: discord.Member = None):
        author = ctx.message.author
        await ctx.message.delete()
        category = category_sort(ctx.message)
        if category is None:
            return

        # Finds document
        if category == "TIMEATTACK":
            _category_data = TimeAttackData
        elif category == "MILDCORE":
            _category_data = MildcoreData
        elif category == "HARDCORE":
            _category_data = HardcoreData
        else:  # "BONUS"
            _category_data = BonusData

        if user is None:
            search_id = ctx.author.id
        else:
            search_id = user.id

        search = await _category_data.find_one({"posted_by": search_id})

        if not search:
            await ctx.channel.send(
                "Provided arguments might not exist. Nothing was deleted."
            )
            return

        if search.posted_by != ctx.author.id:
            for role in ctx.author.roles:
                if role.id == constants_bot.ORG_ROLE_ID:
                    break
            else:
                await ctx.channel.send(
                    "You do not have sufficient permissions. Submission was not deleted."
                )
                return

        embed = doom_embed(title="Submission deletion")
        embed.add_field(
            name=f"Name: {discord.utils.find(lambda m: m.id == search.posted_by, ctx.guild.members).name}",
            value=(
                f"> Category: {category}\n"
                f"> Record: {display_record(search.record)}\n"
            ),
            inline=False,
        )

        view = Confirm("Deletion", author)
        msg = await ctx.send("Do you want to delete this?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await msg.edit(
                content="Personal best deleted succesfully.", delete_after=15
            )
            await search.delete()
        elif not view.value:
            await msg.edit(content="Personal best was not deleted.", delete_after=15)
        elif view.value is None:
            await msg.edit(
                content="Deletion timed out! Personal best has not been deleted.",
                delete_after=15,
            )

    @commands.group(
        pass_context=True,
        case_insensitive=True,
        aliases=["times"],
        help="Choose a specific category to view currently submitted times for that category. \nExample: /board ta",
        brief="Leadboard for Tournament Times",
    )
    @viewable_channels()
    async def board(self, ctx):
        await ctx.message.delete()
        if ctx.invoked_subcommand is None:
            embed = doom_embed(
                title="Leadboard for Tournament Times",
                desc="Choose a specific category to view currently submitted times for that category. \nExample: /board ta",
            )
            for cmd in self.bot.get_command("board").walk_commands():
                embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)
            await ctx.send(embed=embed, delete_after=30)

    @board.command(
        name="ta", aliases=["timeattack", "time-attack"], help="View time attack times"
    )
    @viewable_channels()
    async def _timeattack(self, ctx):
        await tournament_boards("TIMEATTACK", ctx=ctx)

    @board.command(name="mc", aliases=["mildcore"], help="View mildcore times")
    @viewable_channels()
    async def _mildcore(self, ctx):
        await tournament_boards("MILDCORE", ctx=ctx)

    @board.command(name="hc", aliases=["hardcore"], help="View hardcore times")
    @viewable_channels()
    async def _hardcore(self, ctx):
        await tournament_boards("HARDCORE", ctx=ctx)

    @board.command(name="bonus", help="View bonus times")
    @viewable_channels()
    async def _bonus(self, ctx):
        await tournament_boards("BONUS", ctx=ctx)

    @commands.group(
        pass_context=True,
        case_insensitive=True,
        help="[ORG ONLY] Clear all times from a specific tournament category.",
        brief="[ORG ONLY] Clear Tournament Times",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def clear(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = doom_embed(
                title="Clear Tournament Times",
                desc="Clear all times from a specific tournament category.",
            )
            for cmd in self.bot.get_command("clear").walk_commands():
                embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)
            await ctx.send(embed=embed, delete_after=15)

    @clear.command(
        name="ta", aliases=["timeattack", "time-attack"], help="Clear time attack times"
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _timeattack_clear(self, ctx):
        await confirm_collection_drop(ctx, "time attack")

    @clear.command(name="mc", aliases=["mildcore"], help="Clear mildcore times")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _mildcore_clear(self, ctx):
        await confirm_collection_drop(ctx, "mildcore")

    @clear.command(name="hc", aliases=["hardcore"], help="Clear hardcore times")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _hardcore_clear(self, ctx):
        await confirm_collection_drop(ctx, "hardcore")

    @clear.command(name="bonus", help="Clear bonus times")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _bonus_clear(self, ctx):
        await confirm_collection_drop(ctx, "bonus")

    @clear.command(name="all", help="Clear all times")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _all_clear(self, ctx):
        await confirm_collection_drop(ctx, "all")

    @commands.group(
        pass_context=True,
        case_insensitive=True,
        help="[ORG ONLY] Grab all screenshots from a specific tournament category and export to #ss-export",
        brief="[ORG ONLY] Export Tournament Screenshots",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def export(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = doom_embed(
                title="Export Tournament Screenshots",
                desc="Grab all screenshots from a specific tournament category.",
            )
            for cmd in self.bot.get_command("export").walk_commands():
                embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)
            await ctx.send(embed=embed, delete_after=15)

    @export.command(
        name="ta",
        aliases=["timeattack", "time-attack"],
        help="Export time attack screenshots",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _export_timeattack(self, ctx):
        await exporter(
            "TIMEATTACK",
            self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID),
            ctx=ctx,
        )

    @export.command(name="mc", aliases=["mildcore"], help="Export mildcore screenshots")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _export_mildcore(self, ctx):
        await exporter(
            "MILDCORE",
            self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID),
            ctx=ctx,
        )

    @export.command(name="hc", aliases=["hardcore"], help="Export hardcore screenshots")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _export_hardcore(self, ctx):
        await exporter(
            "HARDCORE",
            self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID),
            ctx=ctx,
        )

    @export.command(name="bonus", help="Export bonus screenshots")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _export_bonus(self, ctx):
        await exporter(
            "BONUS", self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID), ctx=ctx
        )

    @commands.command(
        name="deletess",
        help="[ORG ONLY] Deletes all screenshots in export channel",
        brief="[ORG ONLY] Deletes all screenshots in export channel",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _delete_screenshots(self, ctx):
        view = Confirm("Deletion", ctx.message.author)
        await ctx.message.delete()
        confirmation_msg = await ctx.send(
            f"Are you sure you want to delete all screenshots in the export channel?",
            view=view,
        )
        await view.wait()

        if view.value:
            channel = self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID)
            await confirmation_msg.edit(content="Clearing screenshots...")
            deleted = await channel.purge(limit=100)
            await confirmation_msg.edit(
                content=f"{len(deleted)} screenshots have been deleted.",
                delete_after=15,
            )

        elif not view.value:
            await confirmation_msg.edit(
                content="Screenshots were not deleted.", delete_after=15
            )

        elif view.value is None:
            await confirmation_msg.edit(
                content="Timed out! Screenshots were not deleted.", delete_after=15
            )

    @commands.group(
        pass_context=True,
        case_insensitive=True,
        aliases=["ss", "screenshot"],
        help="View a specific players latest screenshot from a specific tournament category.",
        brief="View Players Tournament Screenshots",
    )
    @viewable_channels()
    async def view(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = doom_embed(
                title="View Players Tournament Screenshots",
                desc="View a specific players latest screenshot from a specific tournament category.",
            )
            for cmd in self.bot.get_command("view").walk_commands():
                embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)
            await ctx.send(embed=embed, delete_after=15)

    @view.command(
        name="ta",
        aliases=["timeattack", "time-attack"],
        help="View a player's latest time attack screenshot",
    )
    async def _screenshot_ta(self, ctx, user: discord.Member = None):
        await single_exporter(ctx, "TIMEATTACK", user)

    @view.command(
        name="mc",
        aliases=["mildcore"],
        help="View a player's latest mildcore screenshot",
    )
    async def _screenshot_mc(self, ctx, user: discord.Member = None):
        await single_exporter(ctx, "MILDCORE", user)

    @view.command(
        name="hc",
        aliases=["hardcore"],
        help="View a player's latest hardcore screenshot",
    )
    async def _screenshot_hc(self, ctx, user: discord.Member = None):
        await single_exporter(ctx, "HARDCORE", user)

    @view.command(
        name="bonus",
        help="View a player's latest bonus screenshot",
    )
    async def _screenshot_bonus(self, ctx, user: discord.Member = None):
        await single_exporter(ctx, "BONUS", user)

    @commands.group(
        pass_context=True,
        case_insensitive=True,
        help="[ORG ONLY] Lock a specific submission channel",
        brief="[ORG ONLY] Lock a specific submission channel",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def lock(self, ctx):
        await ctx.message.delete()
        if ctx.invoked_subcommand is None:
            # embed = doom_embed(
            #     title="Lock a specific submission channel",
            #     desc="Example: /unlock ta",
            # )
            # for cmd in self.bot.get_command("unlock").walk_commands():
            #     embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)

            view = TournamentChoices(ctx.author)
            msg = await ctx.send(
                "Which category would you like to lock?", delete_after=15, view=view
            )
            await view.wait()
            if view.value == "Time Attack":
                await msg.edit(content="Please wait...", view=view, delete_after=1)
                await self._lock_ta(ctx)
            elif view.value == "Mildcore":
                await msg.edit(content="Please wait...", view=view, delete_after=1)
                await self._lock_mc(ctx)
            elif view.value == "Hardcore":
                await msg.edit(content="Please wait...", view=view, delete_after=1)
                await self._lock_hc(ctx)
            elif view.value == "Bonus":
                await msg.edit(content="Please wait...", view=view, delete_after=1)
                await self._lock_bonus(ctx)
            elif view.value == "All":
                await msg.edit(
                    content="Please wait...",
                    view=view,
                    delete_after=1,
                )
                await self._lock_ta(ctx)
                await self._lock_mc(ctx)
                await self._lock_hc(ctx)
                await self._lock_bonus(ctx)

    @lock.command(
        name="ta",
        aliases=["timeattack", "time-attack"],
        help="Lock time attack submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _lock_ta(self, ctx):
        await lock_unlock(self.ta_channel, self.ta_role, unlock=False)
        await lock_unlock(self.ta_channel, self.trifecta_role, unlock=False)
        await lock_unlock(self.ta_channel, self.bracket_role, unlock=False)
        await ctx.send("Time attack locked.", delete_after=15)

    @lock.command(
        name="mc",
        aliases=["mildcore"],
        help="Lock mildcore submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _lock_mc(self, ctx):
        await lock_unlock(self.mc_channel, self.mc_role, unlock=False)
        await lock_unlock(self.mc_channel, self.trifecta_role, unlock=False)
        await lock_unlock(self.mc_channel, self.bracket_role, unlock=False)
        await ctx.send("Mildcore locked.", delete_after=15)

    @lock.command(
        name="hc",
        aliases=["hardcore"],
        help="Lock hardcore submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _lock_hc(self, ctx):
        await lock_unlock(self.hc_channel, self.hc_role, unlock=False)
        await lock_unlock(self.hc_channel, self.trifecta_role, unlock=False)
        await lock_unlock(self.hc_channel, self.bracket_role, unlock=False)
        await ctx.send("Hardcore locked.", delete_after=15)

    @lock.command(
        name="bonus",
        help="Lock bonus submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _lock_bonus(self, ctx):
        await lock_unlock(self.bonus_channel, self.bonus_role, unlock=False)
        await lock_unlock(self.bonus_channel, self.trifecta_role, unlock=False)
        await lock_unlock(self.bonus_channel, self.bracket_role, unlock=False)
        await ctx.send("Bonus locked.", delete_after=15)

    @lock.command(
        name="all",
        help="Lock all submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _lock_all(self, ctx):
        await lock_unlock(self.ta_channel, self.ta_role, unlock=False)
        await lock_unlock(self.ta_channel, self.trifecta_role, unlock=False)
        await lock_unlock(self.ta_channel, self.bracket_role, unlock=False)
        await ctx.send("Time attack locked.", delete_after=15)

        await lock_unlock(self.mc_channel, self.mc_role, unlock=False)
        await lock_unlock(self.mc_channel, self.trifecta_role, unlock=False)
        await lock_unlock(self.mc_channel, self.bracket_role, unlock=False)
        await ctx.send("Mildcore locked.", delete_after=15)

        await lock_unlock(self.hc_channel, self.hc_role, unlock=False)
        await lock_unlock(self.hc_channel, self.trifecta_role, unlock=False)
        await lock_unlock(self.hc_channel, self.bracket_role, unlock=False)
        await ctx.send("Hardcore locked.", delete_after=15)

        await lock_unlock(self.bonus_channel, self.bonus_role, unlock=False)
        await lock_unlock(self.bonus_channel, self.trifecta_role, unlock=False)
        await lock_unlock(self.bonus_channel, self.bracket_role, unlock=False)
        await ctx.send("Bonus locked.", delete_after=15)

    @commands.group(
        pass_context=True,
        case_insensitive=True,
        help="[ORG ONLY] Unlock a specific submission channel",
        brief="[ORG ONLY] Unlock a specific submission channel",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def unlock(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = doom_embed(
                title="Unock a specific submission channel",
                desc="Example: /unlock ta",
            )
            for cmd in self.bot.get_command("unlock").walk_commands():
                embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)
            await ctx.send(embed=embed, delete_after=15)

    @unlock.command(
        name="ta",
        aliases=["timeattack", "time-attack"],
        help="Unock time attack submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _unlock_ta(self, ctx):
        await lock_unlock(self.ta_channel, self.ta_role, unlock=True)
        await lock_unlock(self.ta_channel, self.trifecta_role, unlock=True)
        await lock_unlock(self.ta_channel, self.bracket_role, unlock=True)
        await ctx.send("Time attack unlocked.", delete_after=15)

    @unlock.command(
        name="mc",
        aliases=["mildcore"],
        help="Unlock mildcore submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _unlock_mc(self, ctx):
        await lock_unlock(self.mc_channel, self.mc_role, unlock=True)
        await lock_unlock(self.mc_channel, self.trifecta_role, unlock=True)
        await lock_unlock(self.mc_channel, self.bracket_role, unlock=True)
        await ctx.send("Mildcore unlocked.", delete_after=15)

    @unlock.command(
        name="hc",
        aliases=["hardcore"],
        help="Unlock hardcore submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _unlock_hc(self, ctx):
        await lock_unlock(self.hc_channel, self.hc_role, unlock=True)
        await lock_unlock(self.hc_channel, self.trifecta_role, unlock=True)
        await lock_unlock(self.hc_channel, self.bracket_role, unlock=True)
        await ctx.send("Hardcore unlocked.", delete_after=15)

    @unlock.command(
        name="bonus",
        help="Unlock bonus submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _unlock_bonus(self, ctx):
        await lock_unlock(self.bonus_channel, self.bonus_role, unlock=True)
        await lock_unlock(self.bonus_channel, self.trifecta_role, unlock=True)
        await lock_unlock(self.bonus_channel, self.bracket_role, unlock=True)
        await ctx.send("Bonus unlocked.", delete_after=15)

    @unlock.command(
        name="all",
        help="Unlock all submissions",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _unlock_all(self, ctx):
        await lock_unlock(self.ta_channel, self.ta_role, unlock=True)
        await lock_unlock(self.ta_channel, self.trifecta_role, unlock=True)
        await lock_unlock(self.ta_channel, self.bracket_role, unlock=True)
        await ctx.send("Time attack locked.", delete_after=15)

        await lock_unlock(self.mc_channel, self.mc_role, unlock=True)
        await lock_unlock(self.mc_channel, self.trifecta_role, unlock=True)
        await lock_unlock(self.mc_channel, self.bracket_role, unlock=True)
        await ctx.send("Mildcore locked.", delete_after=15)

        await lock_unlock(self.hc_channel, self.hc_role, unlock=True)
        await lock_unlock(self.hc_channel, self.trifecta_role, unlock=True)
        await lock_unlock(self.hc_channel, self.bracket_role, unlock=True)
        await ctx.send("Hardcore locked.", delete_after=15)

        await lock_unlock(self.bonus_channel, self.bonus_role, unlock=True)
        await lock_unlock(self.bonus_channel, self.trifecta_role, unlock=True)
        await lock_unlock(self.bonus_channel, self.bracket_role, unlock=True)
        await ctx.send("Bonus locked.", delete_after=15)

    @commands.command(
        aliases=["startround"],
        help="",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def start(self, ctx):
        if await Schedule.count_documents({}) > 9:
            ctx.send("Too many tournaments active. Consider deleting some. :dbrug:")
            return
        wizard = TournamentWizard()
        await wizard.start(ctx)
        result = wizard.result

        try:
            embed = doom_embed(
                title=result["title"],
                desc=result["description"],
            )
            embed.add_field(name="Time Limit", value=result["time_limit"])
            for name, value in result["fields"]:
                embed.add_field(name=name, value=value, inline=False)
        except KeyError:
            return
        view = Confirm("Tournament", ctx.message.author)
        confirmation_msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            wizard.schedule.embed_dict = embed.to_dict()
            await wizard.schedule.commit()
            if result["start_time"] is not None:
                await confirmation_msg.edit(
                    content=f"Scheduled tournament confirmed for {result['start_time_datetime'].strftime('%m/%d/%Y at approx. %H:%M %Z')}",
                    view=view,
                )
                return
            else:
                await confirmation_msg.edit(view=view, delete_after=15)
            await self._start_round(result["mentions"], wizard.schedule.embed_dict)

        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted. `/start` will not run.",
                delete_after=15,
                view=view,
            )

        elif view.value is None:
            await confirmation_msg.edit(
                content="Confirmation timed out! `/start` will not run.",
                view=view,
                delete_after=15,
            )

    @commands.command(
        name="announce",
        help="[ORG ONLY] Nicely formatted annoucements posted on #tournament-announcements.\n\nBe sure to use quotation marks around the title and messages when they contain spaces!\n\nAdd an image by attaching to the command message.",
        brief="[ORG ONLY] Post annoucements in #tournament-announcements",
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _announcement(self, ctx, title: str, message: str, *, mentions=None):
        author = ctx.message.author
        await ctx.message.delete()
        if mentions:
            combined_mentions = "".join([x for x in mentions])
        else:
            combined_mentions = ""
        channel = self.bot.get_channel(constants_bot.TOURNAMENT_INFO_CHANNEL_ID)
        embed = doom_embed(title="Announcement")
        embed.add_field(name=title, value=message)
        if len(ctx.message.attachments) > 0:
            embed.set_image(url=ctx.message.attachments[0].url)

        view = Confirm("Announcement", author)
        confirmation_msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await channel.send(f"{combined_mentions}", embed=embed)
            await confirmation_msg.edit(delete_after=15, view=view)
        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted. `/announce` will not run.",
                delete_after=15,
                view=view,
            )
            return
        elif view.value is None:
            await confirmation_msg.edit(
                content="Confirmation timed out! `/announce` will not run.",
                view=view,
                delete_after=15,
            )
            return

    @commands.command(name="cancel", help="", brief="", aliases=[])
    async def _cancel_tournament(self, ctx):
        schedules = []
        async for schedule in Schedule.find({}):
            schedules.append(schedule)

        choices = MultipleChoice(
            self.bot,
            [f"{i + 1} | {s.title} {s.mentions}" for i, s in enumerate(schedules)],
            "Which tournament should be cancelled?",
        )
        await choices.run(users=[ctx.author], channel=ctx.channel)
        answer = choices.choice
        await choices.quit()
        if answer is None:
            return
        choice_number = int(answer[0]) - 1
        await schedules[choice_number].delete()
        await ctx.message.delete()

    @commands.command(name="changetime", help="", brief="", aliases=["change"])
    async def _change_tournament_time(self, ctx):
        author = ctx.message.author
        await ctx.message.delete()
        schedules = []
        async for schedule in Schedule.find({}):
            schedules.append(schedule)

        choices = MultipleChoice(
            self.bot,
            [f"{i + 1} | {s.title} {s.mentions}" for i, s in enumerate(schedules)],
            "Which tournament's time should be changed?",
        )
        await choices.run(users=[ctx.author], channel=ctx.channel)
        answer = choices.choice
        await ctx.message.delete()
        await choices.quit()

        if answer is None:
            return

        choice_number = int(answer[0]) - 1

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.author

        question = await ctx.send("What do you want to change the end time to?")
        response = await self.bot.wait_for("message", check=check, timeout=30)

        time = dateparser.parse(
            response.content, settings={"PREFER_DATES_FROM": "future"}
        )

        embed = doom_embed(
            title=f"{schedules[choice_number].title}",
            desc=f"{schedules[choice_number].mentions}",
        )
        embed.add_field(name="New ending time:", value=f"{response.content}")

        view = Confirm("Tournament time change", author)
        confirmation_msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            schedules[choice_number].schedule = time
            await schedules[choice_number].commit()

        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted. Nothing will be changed."
            )
        elif view.value is None:
            await confirmation_msg.edit(content="Timed out. Nothing will be changed.")
        await asyncio.sleep(5)
        await response.delete()
        await question.delete()
        await confirmation_msg.delete()


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament(bot))
