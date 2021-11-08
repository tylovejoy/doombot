import asyncio
import datetime
import operator
import time
import sys
from logging import getLogger
from utils.embeds import doom_embed
import dateparser
import discord
from discord.ext import commands, tasks
from internal.database import (
    TournamentRecordData,
    TopThree,
    TournamentData,
    TournamentRecords,
)
from utils.pb_utils import time_convert, display_record
from utils.tournament_utils import lock_unlock, category_sort, Category
from utils.views import Confirm, BracketToggle, TournamentChoicesNoAll, Paginator

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


def parse_map(text):
    text = text.split(" - ")
    return {"code": text[0], "level": text[1], "author": text[2]}


def display_maps(maps):
    return f"{maps['code']} - {maps['level']} by {maps['author']}"


def viewable_channels():
    def predicate(ctx):
        return ctx.channel.id in [
            constants_bot.TOURNAMENT_CHAT_CHANNEL_ID,
            constants_bot.ORG_CHANNEL_ID,
            constants_bot.EXPORT_SS_CHANNEL_ID,
            constants_bot.MAP_SELECT_CHANNEL_ID,
        ]

    return commands.check(predicate)


class Tournament2(commands.Cog, name="Tournament2"):
    """Tournament2"""

    def __init__(self, bot):
        self.bot = bot
        self.cur_tournament = None

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
        self.org_channel = self.guild.get_channel(constants_bot.ORG_CHANNEL_ID)
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
        latest_tournament: TournamentData = await TournamentData().find_one(
            sort=[("tournament_id", -1)], limit=1
        )
        # Resume tournament after restart
        if not latest_tournament:
            return

        if latest_tournament.schedule_start == datetime.datetime(
            year=1, month=1, day=1
        ) and latest_tournament.schedule_end == datetime.datetime(
            year=1, month=1, day=1
        ):
            self.cur_tournament = None
            return

        self.cur_tournament = latest_tournament

        if (
            datetime.datetime.now()
            >= self.cur_tournament.schedule_start
            != datetime.datetime(year=1, month=1, day=1)
        ):
            logger.info("Starting scheduled tournament.")
            await self._start_round()
            self.cur_tournament.schedule_start = datetime.datetime(
                year=1, month=1, day=1
            )
            await self.cur_tournament.commit()
            return

        if (
            datetime.datetime.now()
            >= self.cur_tournament.schedule_end
            != datetime.datetime(year=1, month=1, day=1)
        ):
            logger.info("Ending scheduled tournament.")
            await self._end_round()
            return

    async def _setup_db(self, data):
        last_tournament = await TournamentData().find_one(
            sort=[("tournament_id", -1)], limit=1
        )
        if last_tournament:
            tournament_id = last_tournament.tournament_id + 1
        else:
            tournament_id = 1

        tournament = TournamentData(
            **{
                "tournament_id": tournament_id,
                "name": data["title"],
                "schedule_start": data["start_time"],
                "schedule_end": data["end_time"],
                "unix_start": data["unix_start"],
                "unix_end": data["unix_end"],
                "bracket": data["bracket"],
                "bracket_cat": data["bracket_cat"]
            }
        )
        maps = {
            "ta": data.get("ta", {}),
            "mc": data.get("mc", {}),
            "hc": data.get("hc", {}),
            "bo": data.get("bo", {}),
        }
        tournament.maps = {**maps}
        tournament.records = {
            "ta": [],
            "mc": [],
            "hc": [],
            "bo": [],
        }
        tournament.missions = {
            "ta": [],
            "mc": [],
            "hc": [],
            "bo": [],
        }
        await tournament.commit()
        self.cur_tournament = tournament

    async def _lock_all(self):
        await lock_unlock(
            [self.ta_channel, self.mc_channel, self.hc_channel, self.bonus_channel],
            [self.ta_role, self.trifecta_role, self.bracket_role],
            unlock=False,
        )

    async def _lock_ta(self):
        await lock_unlock(
            [self.ta_channel],
            [self.ta_role, self.trifecta_role, self.bracket_role],
            unlock=False,
        )

    async def _lock_mc(self):
        await lock_unlock(
            [self.mc_channel],
            [self.mc_role, self.trifecta_role, self.bracket_role],
            unlock=False,
        )

    async def _lock_hc(self):
        await lock_unlock(
            [self.hc_channel],
            [self.hc_role, self.trifecta_role, self.bracket_role],
            unlock=False,
        )

    async def _lock_bo(self):
        await lock_unlock(
            [self.bonus_channel],
            [self.bonus_role, self.trifecta_role, self.bracket_role],
            unlock=False,
        )

    async def _unlock_all(self):
        await lock_unlock(
            [self.ta_channel, self.mc_channel, self.hc_channel, self.bonus_channel],
            [self.ta_role, self.trifecta_role, self.bracket_role],
            unlock=True,
        )

    async def _unlock_ta(self):
        await lock_unlock(
            [self.ta_channel],
            [self.ta_role, self.trifecta_role, self.bracket_role],
            unlock=True,
        )

    async def _unlock_mc(self):
        await lock_unlock(
            [self.mc_channel],
            [self.mc_role, self.trifecta_role, self.bracket_role],
            unlock=True,
        )

    async def _unlock_hc(self):
        await lock_unlock(
            [self.hc_channel],
            [self.hc_role, self.trifecta_role, self.bracket_role],
            unlock=True,
        )

    async def _unlock_bo(self):
        await lock_unlock(
            [self.bonus_channel],
            [self.bonus_role, self.trifecta_role, self.bracket_role],
            unlock=True,
        )

    def _mentions(self, category):
        mentions = {
            "ta": self.ta_role.mention,
            "mc": self.mc_role.mention,
            "hc": self.hc_role.mention,
            "bo": self.bonus_role.mention,
        }
        return mentions[category]

    async def _start_round(self, bracket_cat=None):
        if not bracket_cat:
            await self._unlock_all()
            mentions = (
                f"{self.ta_role.mention}"
                f"{self.mc_role.mention}"
                f"{self.hc_role.mention}"
                f"{self.bonus_role.mention}"
                f"{self.trifecta_role.mention}"
            )
        else:
            unlocks = {
                "ta": await self._unlock_ta(),
                "mc": await self._unlock_mc(),
                "hc": await self._unlock_hc(),
                "bo": await self._unlock_bo()
            }
            unlocks[bracket_cat]
            mentions = (
                f"{self._mentions(bracket_cat)}"
                f"{self.trifecta_role.mention}"
                f"{self.bracket_role.mention}"
            )
        tournament: TournamentData = self.cur_tournament
        embed = doom_embed(
            title=tournament.name,
            desc=f"**Ends** <t:{tournament.unix_end}:R> -- <t:{tournament.unix_end}:F>\n",
        )
        if bracket_cat == "ta" or not bracket_cat:
            embed.add_field(
                name="Time Attack", value=display_maps(tournament.maps["ta"]), inline=False
            )
        if bracket_cat == "mc" or not bracket_cat:
            embed.add_field(
                name="Mildcore", value=display_maps(tournament.maps["mc"]), inline=False
            )
        if bracket_cat == "hc" or not bracket_cat:
            embed.add_field(
                name="Hardcore", value=display_maps(tournament.maps["hc"]), inline=False
            )
        if bracket_cat == "bo" or not bracket_cat:
            embed.add_field(
                name="Bonus", value=display_maps(tournament.maps["bo"]), inline=False
            )
        await self.info_channel.send(mentions, embed=embed)

    async def _end_round(self):
        self.cur_tournament = await TournamentData().find_one(
            sort=[("tournament_id", -1)], limit=1
        )
        records = self.cur_tournament.records
        if not self.cur_tournament.bracket:
            await self._lock_all()
            mentions = (
                f"{self.ta_role.mention}"
                f"{self.mc_role.mention}"
                f"{self.hc_role.mention}"
                f"{self.bonus_role.mention}"
                f"{self.trifecta_role.mention}"
            )
            ta = records["ta"]
            mc = records["mc"]
            hc = records["hc"]
            bo = records["bo"]
            await self._export_records(ta, Category.TIMEATTACK.value, "Time Attack")
            await self._export_records(mc, Category.MILDCORE.value, "Mildcore")
            await self._export_records(hc, Category.HARDCORE.value, "Hardcore")
            await self._export_records(bo, Category.BONUS.value, "Bonus")
        else:
            locks = {
                "ta": await self._lock_ta(),
                "mc": await self._lock_mc(),
                "hc": await self._lock_hc(),
                "bo": await self._lock_bo()
            }
            locks[self.cur_tournament.bracket_cat]
            mentions = (
                f"{self._mentions(self.cur_tournament.bracket_cat)}"
                f"{self.trifecta_role.mention}"
                f"{self.bracket_role.mention}"
            )
            self._mentions(self.cur_tournament.bracket_cat)
            br = records[self.cur_tournament.bracket_cat]
            await self._export_records(br, self.cur_tournament.bracket_cat, "Bracket")

        self.cur_tournament.schedule_end = datetime.datetime(year=1, month=1, day=1)
        await self.cur_tournament.commit()
        self.cur_tournament = None

        end_announcement = doom_embed(title=f"Tournament Announcement")
        end_announcement.add_field(
            name=f"The round has ended!",
            value=f"Stay tuned for the next announcement!",
        )
        await self.info_channel.send(f"{mentions}", embed=end_announcement)

    async def _export_records(self, records, category, category_name):
        await self.export_channel.send(f"***{10 * '-'} {category_name} {10 * '-'}***")
        if not records:
            await self.export_channel.send(
                f"No times exist for the {category_name} category!"
            )
            return
        records = sorted(records, key=operator.itemgetter("record"))
        embeds = await self._tournament_boards(category)
        for e in embeds:
            await self.export_channel.send(embed=e)

        for record in records:
            embed = doom_embed(title=record.name, url=record.attachment_url)
            embed.add_field(name=category, value=display_record(record.record))
            embed.set_image(url=record.attachment_url)
            await self.export_channel.send(embed=embed)

    async def _find_records(self, ctx, category):
        self.cur_tournament = await TournamentData().find_one(
            {"tournament_id": self.cur_tournament.tournament_id}
        )
        records = self.cur_tournament.records[category.value]
        author_record = None
        pos = None
        for i, r in enumerate(records):
            if r.posted_by == ctx.author.id:
                author_record = r
                pos = i
                break
        return records, author_record, pos

    async def _tournament_boards(self, category):
        records = sorted(
            self.cur_tournament.records[category], key=operator.itemgetter("record")
        )
        data_amount = len(records)

        embed = doom_embed(title="Records")
        embeds = []
        count = 0

        for record in records:
            user = discord.utils.find(
                lambda m: m.id == record.posted_by, self.guild.members
            )
            embed.add_field(
                name=f"#{count + 1} - {user.name if user else 'Unknown'}",
                value=f"> Record: {display_record(record.record)}\n",
                inline=False,
            )
            if (count + 1) % 10 == 0 or (count + 1) == data_amount:
                embeds.append(embed)
                embed = doom_embed(title="Records")

            count += 1

        return embeds

    @commands.command()
    async def start(self, ctx):
        if self.cur_tournament:
            await ctx.send(
                "You cannot start a tournament while another one is active.",
                delete_after=10,
            )
            return

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.author

        # Begin Questions Wizard
        embed = doom_embed(
            "Tournament Start Wizard",
            desc=(
                "Enter tournament details in this format:\n"
                "**Title**\n"
                "**Start Time** [Type '_now_' if immediate start.]\n"
                "**End Time**\n"
                "TA_CODE - LEVEL - CREATOR\n"
                "MC_CODE - LEVEL - CREATOR\n"
                "HC_CODE - LEVEL - CREATOR\n"
                "BO_CODE - LEVEL - CREATOR\n"
            ),
        )
        view = BracketToggle(ctx.author)
        wizard = await ctx.send(embed=embed, view=view)
        results = {}

        response = await self.bot.wait_for("message", check=check, timeout=30)
        if response.content.lower() in ["cancel", "stop", "end"]:
            await response.delete()
            await wizard.delete()
            return
        lines = response.content.split("\n")
        while True:
            if 4 != len(lines) != 7:
                await wizard.edit(
                    content="Message not formatted correctly. Try again.", view=view
                )
                response = await self.bot.wait_for("message", check=check, timeout=30)
                if response.content.lower() in ["cancel", "stop", "end"]:
                    await response.delete()
                    await wizard.delete()
                    return
            else:
                break

        await wizard.delete()
        await response.delete()

        results["bracket"] = view.bracket
        results["bracket_cat"] = view.bracket_cat
        results["title"] = lines[0]

        if lines[1].lower() != "now":
            results["start_time"] = dateparser.parse(
                lines[1], settings={"PREFER_DATES_FROM": "future"}
            )
        else:
            results["start_time"] = datetime.datetime(year=1, month=1, day=1)

        results["end_time"] = dateparser.parse(
            lines[2], settings={"PREFER_DATES_FROM": "future"}
        )

        if results["start_time"] != datetime.datetime(year=1, month=1, day=1):
            delta = results["end_time"] - datetime.datetime.now()
            results["end_time"] = results["start_time"] + delta
            results["unix_start"] = str(time.mktime(results["start_time"].timetuple()))[
                :-2
            ]
            start = f"<t:{results['unix_start']}:R> -- <t:{results['unix_start']}:F>"
        else:
            results["unix_start"] = str(
                time.mktime(datetime.datetime.utcnow().timetuple())
            )[:-2]
            start = f"Now"

        results["unix_end"] = str(time.mktime(results["end_time"].timetuple()))[:-2]

        if not results["bracket"]:
            results["ta"] = parse_map(lines[3])
            results["mc"] = parse_map(lines[4])
            results["hc"] = parse_map(lines[5])
            results["bo"] = parse_map(lines[6])
            codes = (
                f"**{results['ta']['code']}** - {results['ta']['level']} by {results['ta']['author']}\n"
                f"**{results['mc']['code']}** - {results['mc']['level']} by {results['mc']['author']}\n"
                f"**{results['hc']['code']}** - {results['hc']['level']} by {results['hc']['author']}\n"
                f"**{results['bo']['code']}** - {results['bo']['level']} by {results['bo']['author']}\n"
            )
        else:
            results[results["bracket_cat"]] = parse_map(lines[3])
            codes = (
                f"**{results[results['bracket_cat']]['code']}** - "
                f"{results[results['bracket_cat']]['level']} by {results[results['bracket_cat']]['author']}\n"
            )

        embed = doom_embed(
            title="",
            desc=(
                f"**{results['title']}**\n"
                f"**Start:** {start}\n"
                f"**End:** <t:{results['unix_end']}:R> -- <t:{results['unix_end']}:F>\n"
                f"{codes}"
            ),
        )

        view = Confirm("Start Tournament Wizard", ctx.author)
        confirmation_msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await confirmation_msg.edit(
                content=f"Scheduled tournament confirmed for <t:{results['unix_start']}:R> -- <t:{results['unix_start']}:F>",
                embed=None,
                view=view,
            )
            await self._setup_db(results)
            if lines[1].lower() == "now":
                if results["bracket"]:
                    await self._start_round(results["bracket_cat"])
                else:
                    await self._start_round()

        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted. Nothing will be changed."
            )
        elif view.value is None:
            await confirmation_msg.edit(content="Timed out. Nothing will be changed.")

    @commands.command(
        name="submit",
        help="Record must be in HH:MM:SS.ss format. Screenshot must be attached to the submission message.",
        brief="Submit times to tournament.",
    )
    async def _submit_record(self, ctx, record):
        category = category_sort(ctx.message)
        if category is Category.OTHER:
            return

        if not ctx.message.attachments:
            await ctx.send(
                "No attachment found. Please submit time with attachment in the same message."
            )
            return

        record_in_seconds = time_convert(record)

        if not record_in_seconds:
            await ctx.send("Invalid time. Map submission rejected.")
            return

        records, author_record, pos = await self._find_records(ctx, category)

        if author_record:
            author_record.record = record
            author_record.attachment_url = ctx.message.attachments[0].url
            records[pos] = author_record
        else:
            author_record = TournamentRecordData(
                **{
                    "posted_by": ctx.author.id,
                    "name": ctx.author.name,
                    "record": record_in_seconds,
                    "attachment_url": ctx.message.attachments[0].url,
                }
            )
            records = records + [author_record]

        embed = doom_embed(title="New Submission")
        # Verification embed for user.
        embed.add_field(
            name=f"Name: {discord.utils.find(lambda m: m.id == author_record.posted_by, ctx.guild.members).name}",
            value=f"> Record: {display_record(record_in_seconds)}\n",
            inline=False,
        )
        embed.set_image(url=ctx.message.attachments[0].url)

        view = Confirm("Submission", ctx.message.author)
        msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await msg.edit(content="Submission accepted", delete_after=15, view=view)
            # Update record
            self.cur_tournament.records[category.value] = records
            await self.cur_tournament.commit()

        elif not view.value:
            await ctx.message.delete()
            await msg.edit(
                content="Submission has not been accepted.",
                delete_after=15,
                view=view,
            )

        elif view.value is None:
            await ctx.message.delete()
            await msg.edit(
                content="Submission timed out! Submission has not been accepted.",
                delete_after=15,
                view=view,
            )

    @commands.command(
        help="Delete a submission to tournament. Optional argument <user> for mod usage.",
        brief="Delete a submission to tournament",
        name="delete",
    )
    async def _delete(self, ctx, user: discord.Member = None):
        category = category_sort(ctx.message)
        await ctx.message.delete()
        if category is Category.OTHER:
            return

        if user is None:
            record_id = ctx.author.id
        else:
            record_id = user.id

        records, author_record, pos = await self._find_records(ctx, category)

        if not author_record:
            await ctx.channel.send(
                "Provided arguments might not exist. Nothing was deleted."
            )
            return

        if records[pos].posted_by != ctx.author.id:
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
            name=f"Name: {discord.utils.find(lambda m: m.id == records[pos].posted_by, ctx.guild.members).name}",
            value=(f"> Record: {display_record(records[pos].record)}\n"),
            inline=False,
        )

        view = Confirm("Deletion", ctx.author)

        msg = await ctx.send("Do you want to delete this?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await msg.edit(
                content="Personal best deleted successfully.",
                delete_after=15,
                view=view,
            )
            del records[pos]
            await self.cur_tournament.commit()

        elif not view.value:
            await msg.edit(
                content="Personal best was not deleted.", delete_after=15, view=view
            )

        elif view.value is None:
            await msg.edit(
                content="Deletion timed out! Personal best has not been deleted.",
                delete_after=15,
                view=view,
            )

    @commands.command(
        aliases=["times"],
        help="Choose a specific category to view currently submitted times for that category. \nExample: /board ta",
        brief="Leaderboard for Tournament Times",
    )
    @viewable_channels()
    async def board(self, ctx, category=None):
        await ctx.message.delete()
        self.cur_tournament = await TournamentData().find_one(
            {"tournament_id": self.cur_tournament.tournament_id}
        )

        if category is None:
            view = TournamentChoicesNoAll(ctx.author)
            msg = await ctx.send(
                "Which category leaderboard would you like to view?",
                delete_after=15,
                view=view,
            )
            await view.wait()
            await msg.edit(content="Please wait...", view=view, delete_after=1)
            await self._view_board(ctx, view.value)
            return

        await self._view_board(ctx, category.lower())

    async def _view_board(self, ctx, category):
        embeds = await self._tournament_boards(category)
        if not embeds:
            await ctx.send(
                f"No times exist for this category!",
                delete_after=15,
            )
            return
        if len(embeds) > 1:
            view = Paginator(embeds, ctx.author)
            paginator = await ctx.send(embed=view.formatted_pages[0], view=view)
            await view.wait()
            await paginator.delete()
        else:
            await ctx.send(embed=embeds[0], delete_after=120)


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament2(bot))
