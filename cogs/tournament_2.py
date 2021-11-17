import asyncio
import datetime
import operator
from os import name
import time
import sys
from logging import getLogger
from internal.point_tracking import CategoryPointTracking, GeneralPointTracking
from utils.embeds import doom_embed, hall_of_fame
import dateparser
import discord
from discord.ext import commands, tasks
from internal.database import (
    AnnoucementSchedule,
    TournamentRecordData,
    TournamentData,
    TournamentRecords,
    ExperiencePoints,
    WorldRecords,
)
from utils.pb_utils import time_convert, display_record
from utils.tournament_utils import lock_unlock, category_sort, Category
from utils.views import (
    ClearView,
    Confirm,
    BracketToggle,
    MissionCategories,
    RemoveMissions,
    ScheduleView,
    StartEndToggle,
    TournamentChoicesNoAll,
    Paginator,
)

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)

DIAMOND_CUTOFF = 0
GM_CUTOFF = 0


def merge(combined_, rank):
    for (k1, k2) in zip(combined_.keys(), rank.keys()):
        if isinstance(combined_[k1], int):
            combined_[k1] += rank[k2]
        else:
            merge(combined_[k1], rank[k2])


def parse_map(text):
    text = text.split(" - ")
    return {"code": text[0], "level": text[1], "author": text[2]}


def display_maps(maps):
    return f"{maps['code']} - {maps['level']} by {maps['author']}"


def make_ordinal(n):
    """
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    n = int(n)
    suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    return str(n) + suffix


def viewable_channels():
    def predicate(ctx):
        return ctx.channel.id in [
            constants_bot.TOURNAMENT_CHAT_CHANNEL_ID,
            constants_bot.ORG_CHANNEL_ID,
            constants_bot.EXPORT_SS_CHANNEL_ID,
            constants_bot.MAP_SELECT_CHANNEL_ID,
        ]

    return commands.check(predicate)


async def _format_missions(category, missions):
    formatted = ""
    t_cat = {
        "ta": "Time Attack",
        "mc": "Mildcore",
        "hc": "Hardcore",
        "bo": "Bonus",
        "general": "General",
    }

    for key in missions[category]:
        if category == "general":
            if missions[category][key]["type"] == "xp":
                formatted += f"**{t_cat[key]}:** Get {missions[category][key]['target']} XP (excluding missions)\n"
            elif missions[category][key]["type"] == "mission":
                formatted += f"**{t_cat[key]}:** Complete {missions[category][key]['target'][0]} {missions[category][key]['target'][1]} missions\n"
            elif missions[category][key]["type"] == "top":
                formatted += f"**{t_cat[key]}:** Get Top 3 in {missions[category][key]['target']} categories.\n"
        else:

            if missions[category][key]["type"] == "sub":
                formatted += f"**{t_cat[key]}:** Get {missions[category][key]['type']} {missions[category][key]['target']} seconds.\n"
            elif missions[category][key]["type"] == "complete":
                formatted += f"**{t_cat[key]}:** Complete the level.\n"

    return formatted


class Tournament2(commands.Cog, name="Tournament2"):
    """Tournament2"""

    def __init__(self, bot):
        self.bot = bot
        self.cur_tournament = None

        logger.info("schedule_checker has started.")
        self.schedule_checker.start()
        logger.info("annoucement_checker has started.")
        self.annoucement_checker.start()

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
    async def annoucement_checker(self):
        announcements = await AnnoucementSchedule().find({}).to_list(length=None)
        for announcement in announcements:
            if datetime.datetime.now() >= announcement.schedule:
                embed = discord.Embed.from_dict(announcement.embed)
                await self.info_channel.send(announcement.mentions, embed=embed)
                await announcement.delete()

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
                "bracket_cat": data["bracket_cat"],
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
        tournament.records_gold = {
            "ta": [],
            "mc": [],
            "hc": [],
            "bo": [],
        }
        tournament.records_diamond = {
            "ta": [],
            "mc": [],
            "hc": [],
            "bo": [],
        }
        tournament.records_gm = {
            "ta": [],
            "mc": [],
            "hc": [],
            "bo": [],
        }
        tournament.records_unranked = {
            "ta": [],
            "mc": [],
            "hc": [],
            "bo": [],
        }
        tournament.missions = {
            "easy": {
                "ta": None,
                "mc": None,
                "hc": None,
                "bo": None,
            },
            "medium": {
                "ta": None,
                "mc": None,
                "hc": None,
                "bo": None,
            },
            "hard": {
                "ta": None,
                "mc": None,
                "hc": None,
                "bo": None,
            },
            "expert": {
                "ta": None,
                "mc": None,
                "hc": None,
                "bo": None,
            },
            "general": {},
        }
        await tournament.commit()
        self.cur_tournament = tournament

    async def _rank_splitter(self, lb=False):
        await self._update_tournament()
        cat_keys = ["ta", "mc", "hc", "bo"]

        gold = self.cur_tournament.records_gold
        diamond = self.cur_tournament.records_diamond
        gm = self.cur_tournament.records_gm
        unranked = self.cur_tournament.records_unranked

        for key in cat_keys:
            for record in self.cur_tournament.records[key]:
                search = await ExperiencePoints().find_one(
                    {"user_id": record.posted_by}
                )

                if not search:
                    search = ExperiencePoints(
                        **{
                            "user_id": record.posted_by,
                            "rank": {
                                "ta": "Unranked",
                                "mc": "Unranked",
                                "hc": "Unranked",
                                "bo": "Unranked",
                            },
                            "xp_avg": {
                                "ta": [None, None, None, None, None],
                                "mc": [None, None, None, None, None],
                                "hc": [None, None, None, None, None],
                                "bo": [None, None, None, None, None],
                            },
                            "xp": 0,
                            "coins": 0,
                        }
                    )
                    await search.commit()

                if search.rank[key] == "Gold":
                    gold[key] = gold[key] + [record]
                elif search.rank[key] == "Diamond":
                    diamond[key] = diamond[key] + [record]
                elif search.rank[key] == "Grandmaster":
                    gm[key] = gm[key] + [record]
                elif search.rank[key] == "Unranked":
                    unranked[key] = unranked[key] + [record]

        if lb:
            return [unranked, gold, diamond, gm]

        self.cur_tournament.records_gold = gold
        self.cur_tournament.records_diamond = diamond
        self.cur_tournament.records_gm = gm
        self.cur_tournament.records_unranked = unranked
        await self.cur_tournament.commit()

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
            "tr": self.trifecta_role.mention,
            "br": self.bracket_role.mention,
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
                "bo": await self._unlock_bo(),
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
                name="Time Attack",
                value=display_maps(tournament.maps["ta"]),
                inline=False,
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

    async def _xp_to_db(self, points: GeneralPointTracking):
        for user_id in points.points:
            search = await ExperiencePoints().find_one({"user_id": user_id})
            search.xp += sum(points.points[user_id]["points"].values())

            for t_cat in ["ta", "mc", "hc", "bo"]:
                total_cat_points = (
                    points.points[user_id]["points"][t_cat]
                    + points.points[user_id]["points"][t_cat + "_missions"]
                )

                # search.xp_avg[t_cat] = search.xp_avg[t_cat][1:] + [total_cat_points]
                await search.commit()

    async def _calculate_new_rank(self):
        search = await ExperiencePoints.find({}).to_list(length=None)
        for doc in search:
            for t_cat in ["ta", "mc", "hc", "bo"]:
                cleaned_list = [x for x in doc.xp_avg[t_cat] if x is not None]
                avg = sum(cleaned_list) / len(cleaned_list)
                if avg < DIAMOND_CUTOFF:
                    new_rank = "Gold"
                elif DIAMOND_CUTOFF <= avg < GM_CUTOFF:
                    new_rank = "Diamond"
                elif GM_CUTOFF <= avg:
                    new_rank = "Grandmaster"
                doc.rank[t_cat] = new_rank
                await doc.commit()

    async def _end_round(self):
        await self._update_tournament()
        await self._lock_all()
        records = self.cur_tournament.records
        await self._rank_splitter()

        # Points
        unranked = CategoryPointTracking(
            self.cur_tournament.missions, self.cur_tournament.records_unranked
        ).points
        gold = CategoryPointTracking(
            self.cur_tournament.missions, self.cur_tournament.records_gold
        ).points
        diamond = CategoryPointTracking(
            self.cur_tournament.missions, self.cur_tournament.records_diamond
        ).points
        gm = CategoryPointTracking(
            self.cur_tournament.missions, self.cur_tournament.records_gm
        ).points

        combined = {**unranked}

        for key in gold:
            if key in combined.keys():
                merge(combined[key], gold[key])
            else:
                combined[key] = gold[key]

        for key in diamond:
            if key in combined.keys():
                merge(combined[key], diamond[key])
            else:
                combined[key] = diamond[key]

        for key in gm:
            if key in combined.keys():
                merge(combined[key], gm[key])
            else:
                combined[key] = gm[key]

        general = GeneralPointTracking(
            missions=self.cur_tournament.missions,
            unranked=self.cur_tournament.records_unranked,
            gold=self.cur_tournament.records_gold,
            diamond=self.cur_tournament.records_diamond,
            gm=self.cur_tournament.records_gm,
            points=combined,
        )

        await self._xp_to_db(general)
        # await self._calculate_new_rank()

        if not self.cur_tournament.bracket:
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
        await self._submit_records_to_bot()
        await self.info_channel.send(f"{mentions}", embed=end_announcement)

    async def _submit_records_to_bot(self):
        for t_cat in ["ta", "mc", "hc", "bo"]:
            for record in self.cur_tournament.records[t_cat]:
                new_record = WorldRecords(**{
                    "code": self.cur_tournament.maps[t_cat]["code"],
                    "level": self.cur_tournament.maps[t_cat]["level"],
                    "record": record.record,
                    "name": record.name,
                    "posted_by": record.posted_by,
                    "url": record.attachment_url,
                    "verified": True,
                })
                await new_record.commit()

    async def _export_records(self, records, category, category_name):
        await self.export_channel.send(f"***{10 * '-'} {category_name} {10 * '-'}***")
        if not records:
            await self.export_channel.send(
                f"No times exist for the {category_name} category!"
            )
            return

        records = sorted(records, key=operator.itemgetter("record"))
        embeds = await self._tournament_boards(category)

        while embeds:
            await self.export_channel.send(embeds=embeds[:10])
            embeds = embeds[10:]

        embeds = []
        for record in records:
            embed = doom_embed(title=record.name + " Screenshot Link")
            embed.add_field(name=record.name, value=display_record(record.record))
            embed.set_image(url=record.attachment_url)
            embeds.append(embed)

        while embeds:
            await self.export_channel.send(embeds=embeds[:10])
            embeds = embeds[10:]

    async def _find_records(self, ctx, category):
        await self._update_tournament()
        records = self.cur_tournament.records[category.value]
        author_record = None
        pos = None
        for i, r in enumerate(records):
            if r.posted_by == ctx.author.id:
                author_record = r
                pos = i
                break
        return records, author_record, pos

    async def _tournament_boards(self, category, rank_cat=None):
        if not rank_cat:
            records = sorted(
                self.cur_tournament.records[category], key=operator.itemgetter("record")
            )
        else:
            records = sorted(rank_cat[category], key=operator.itemgetter("record"))
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

    @commands.has_role(constants_bot.ORG_ROLE_ID)
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
        results["bracket_cat"] = view.dropdown.bracket_cat
        results["title"] = lines[0]

        if lines[1].lower() != "now":
            results["start_time"], results["unix_start"] = await self._start_time(
                lines[1], now=False
            )
            start = f"<t:{results['unix_start']}:R> -- <t:{results['unix_start']}:F>"
        else:
            results["start_time"], results["unix_start"] = await self._start_time()
            start = f"Now"

        results["end_time"], results["unix_end"] = await self._end_time(
            lines[2], results["start_time"]
        )

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
        name="rankboard",
        enabled=False,
    )
    async def _rank_view_board(self, ctx, category, rank):
        await ctx.message.delete()
        await self._update_tournament()
        ranks = await self._rank_splitter(lb=True)
        if rank.lower() == "unranked":
            await self._view_board(ctx, category.lower(), ranks[0])
        elif rank.lower() == "gold":
            await self._view_board(ctx, category.lower(), ranks[1])
        elif rank.lower() == "diamond":
            await self._view_board(ctx, category.lower(), ranks[2])
        elif rank.lower() == "grandmaster":
            await self._view_board(ctx, category.lower(), ranks[3])

    @commands.command(
        aliases=["times"],
        help="Choose a specific category to view currently submitted times for that category. \nExample: /board ta",
        brief="Leaderboard for Tournament Times",
    )
    @viewable_channels()
    async def board(self, ctx, category=None):
        await ctx.message.delete()
        await self._update_tournament()

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

    async def _view_board(self, ctx, category, rank=None):
        embeds = await self._tournament_boards(category, rank)
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

    async def _update_tournament(self):
        self.cur_tournament = await TournamentData().find_one(
            {"tournament_id": self.cur_tournament.tournament_id}
        )

    @commands.has_role(constants_bot.ORG_ROLE_ID)
    @commands.command(
        name="changetime",
        help="Change tournament start or end time. Changing the start time will also change the end time to stay the same length.",
        brief="Change tournament start or end time.",
        enabled=False,
    )
    async def _change_tournament_time(self, ctx):
        await self._update_tournament()
        t = self.cur_tournament
        await ctx.message.delete()

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.author

        embed = doom_embed(
            title="Change tournament start/end time.",
            desc=(
                "Use the button to toggle start/end time modification.\n"
                "Then respond with what the time should be. (e.g. 10 minutes, 1 week, etc.)\n"
                "If you edit the start time, the end time will automatically be changed to stay the same length as initally set."
            ),
        )
        view = StartEndToggle(ctx.author)
        wizard = await ctx.send(embed=embed, view=view, delete_after=30)
        response = await self.bot.wait_for("message", check=check, timeout=30)

        if not view.end:
            t.start_time, t.unix_start = await self._start_time(
                response.content, now=False
            )
            start = f"<t:{t.unix_start}:R> -- <t:{t.unix_start}:F>"
            t.end_time, t.unix_end = await self._end_time(t.start_time)
        # else:
        #     t.end_time, t.unix_end = await self._end_time(), t.start_time)

    async def _start_time(self, start=None, now=True):
        if not now:
            start_time = dateparser.parse(
                start, settings={"PREFER_DATES_FROM": "future"}
            )
            unix_start = str(time.mktime(start_time.timetuple()))[:-2]
        else:
            start_time = datetime.datetime(year=1, month=1, day=1)
            unix_start = str(time.mktime(datetime.datetime.utcnow().timetuple()))[:-2]
        return start_time, unix_start

    async def _end_time(self, end, start):
        end_time = dateparser.parse(end, settings={"PREFER_DATES_FROM": "future"})
        if start != datetime.datetime(year=1, month=1, day=1):
            delta = end_time - datetime.datetime.now()
            end_time = start + delta
        unix_end = str(time.mktime(end_time.timetuple()))[:-2]
        return end_time, unix_end

    @commands.has_role(constants_bot.ORG_ROLE_ID)
    @commands.command(
        name="canceltournament",
        help="Cancel the current active/scheduled tournament. Complete deletetion.",
        brief="Cancel the current active/scheduled tournament.",
    )
    async def _cancel_tournament(self, ctx):
        await self._update_tournament()
        if self.cur_tournament.schedule_end == datetime.datetime(
            year=1, month=1, day=1
        ):
            await ctx.send(
                "There is no active or scheduled tournament.", delete_after=15
            )
            return

        view = Confirm("Cancel Tournament Wizard", ctx.author)
        confirmation_msg = await ctx.send(
            "Do you want to delete this tournament?", view=view
        )
        await view.wait()

        if view.value:
            await confirmation_msg.edit(
                content=f"Deleting the active/scheduled tournament.",
                embed=None,
                view=view,
            )
            await self.cur_tournament.delete()
            self.cur_tournament = None

        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted. Nothing will be changed."
            )
        elif view.value is None:
            await confirmation_msg.edit(content="Timed out. Nothing will be changed.")

    async def _clear_category(self, category):
        await self._update_tournament()
        self.cur_tournament.records[category] = []
        await self.cur_tournament.commit()

    @commands.has_role(constants_bot.ORG_ROLE_ID)
    @commands.command(name="clear", help="Clear one or more record categories.")
    async def _clear(self, ctx):
        await ctx.message.delete()
        embed = doom_embed(
            title="Clear Records Wizard", desc="Select which categories to clear."
        )
        view = ClearView(ctx.author)
        wizard = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.value:
            embed.description = "Clearing the selected categories."
            await wizard.edit(
                embed=embed,
                view=view,
            )
            for cat in view.dropdown.bracket_cat:
                await self._clear_category(cat)

        elif not view.value:
            embed.description = "Not accepted. Nothing will be changed."
            await wizard.edit(embed=embed)

        elif view.value is None:
            embed.description = "Timed out. Nothing will be changed."
            await wizard.edit(embed=embed)

    @commands.has_role(constants_bot.ORG_ROLE_ID)
    @commands.command(name="announce")
    async def _announce(self, ctx):
        await ctx.message.delete()

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.author

        embed = doom_embed(
            title="Annoucement Wizard",
            desc=(
                "Toggle schedule on or off with the button. Select roles to be mentioned.\n"
                "Put the scheduled time on the first line if needed.\n\n"
                "_Use this format as shown:_\n"
                "**SCHEDULED_TIME** [if applicable]\n"
                "**ANNOUCEMENT TITLE**\n"
                "**ANNOUCEMENT CONTENTS**"
            ),
        )
        view = ScheduleView(ctx.author)
        wizard = await ctx.send(embed=embed, view=view, delete_after=120)
        response = await self.bot.wait_for("message", check=check, timeout=120)
        annoucement = response.content.split("\n")
        mentions = ""
        for m in view.mentions:
            mentions += self._mentions(m)
        if view.schedule:
            schedule = dateparser.parse(
                annoucement[0], settings={"PREFER_DATES_FROM": "future"}
            )
            unix_schedule = str(time.mktime(schedule.timetuple()))[:-2]
            title = annoucement[1]
            content = "\n".join(annoucement[2:])
            embed = doom_embed(title="Announcement")
            embed.add_field(name=title, value=content, inline=False)
            embed.add_field(
                name="Scheduled:",
                value=f"<t:{unix_schedule}:R> - <t:{unix_schedule}:F>",
                inline=False,
            )
        else:
            title = annoucement[0]
            content = "\n".join(annoucement[1:])
            embed = doom_embed(title="Announcement")
            embed.add_field(name=title, value=content)

        view_c = Confirm("Announcement", ctx.author)
        confirmation_msg = await ctx.send("Is this correct?", embed=embed, view=view_c)
        await view_c.wait()

        if view_c.value:
            if view.schedule:
                embed.remove_field(-1)
                document = AnnoucementSchedule(
                    **{
                        "embed": embed.to_dict(),
                        "schedule": schedule,
                        "mentions": mentions,
                    }
                )
                await document.commit()
                return
            await self.info_channel.send(f"{mentions}", embed=embed)
            await confirmation_msg.edit(delete_after=15, view=view_c)
        elif not view_c.value:
            await confirmation_msg.edit(
                content="Not accepted. `/announce` will not run.",
                delete_after=15,
                view=view_c,
            )
        elif view_c.value is None:
            await confirmation_msg.edit(
                content="Confirmation timed out! `/announce` will not run.",
                view=view_c,
                delete_after=15,
            )

    @commands.command(name="halloffame", help="", brief="", aliases=["hof", "fame"])
    async def _hall_of_fame(self, ctx):
        all_tournaments = await TournamentData.find(
            {}, sort=[("tournament_id", -1)]
        ).to_list(length=None)

        embeds = []

        bracket_desc = (
            f"{self.ta_role.mention}\n"
            "`1st` <@593838073012289536>\n"
            "`2nd` <@593838073012289536>\n"
            "\n\n"
            f"{self.mc_role.mention}\n"
            "`1st` <@593838073012289536>\n"
            "\n\n"
            f"{self.hc_role.mention}\n"
            "`1st` <@294502010445758464>\n"
            "`2nd` @Jazzy\n"
        )

        bracket = hall_of_fame(
            "Bracket Winners",
            desc=bracket_desc,
        )

        for t in all_tournaments:
            if t.bracket:
                continue
            ta_podium = await self._podium(t.records["ta"])
            mc_podium = await self._podium(t.records["mc"])
            hc_podium = await self._podium(t.records["hc"])
            bo_podium = await self._podium(t.records["bo"])

            codes = [
                f"{t.maps['ta']['level']} by {t.maps['ta']['author']} (**{t.maps['ta']['code']}**)\n",
                f"{t.maps['mc']['level']} by {t.maps['mc']['author']} (**{t.maps['mc']['code']}**)\n",
                f"{t.maps['hc']['level']} by {t.maps['hc']['author']} (**{t.maps['hc']['code']}**)\n",
                f"{t.maps['bo']['level']} by {t.maps['bo']['author']} (**{t.maps['bo']['code']}**)\n",
            ]

            top_three = hall_of_fame(
                f"Weekly Tournament - Top 3",
                desc=f"<t:{t.unix_start}:D>",
            )
            top_three.add_field(
                name="Time Attack",
                value=codes[0] + "\n".join(ta_podium),
                inline=False,
            )
            top_three.add_field(
                name="Mildcore",
                value=codes[1] + "\n".join(mc_podium),
                inline=False,
            )
            top_three.add_field(
                name="Hardcore",
                value=codes[2] + "\n".join(hc_podium),
                inline=False,
            )
            top_three.add_field(
                name="Bonus",
                value=codes[3] + "\n".join(bo_podium),
                inline=False,
            )
            embeds.append(top_three)
        view = Paginator([bracket] + embeds, ctx.author)
        paginator = await ctx.send(embed=view.formatted_pages[0], view=view)
        await view.wait()
        await paginator.delete()

    async def _podium(self, records):
        records_sorted = sorted(records, key=operator.itemgetter("record"))
        podium = []
        for i, _id in enumerate(records_sorted):
            if i == 3:
                break
            member = self.guild.get_member(int(_id.posted_by))
            if member is None:
                podium.append(f"`{make_ordinal(i + 1)}` Unknown")
            else:
                podium.append(f"`{make_ordinal(i + 1)}` {member.mention}")
        return podium

    @commands.has_role(constants_bot.ORG_ROLE_ID)
    @commands.command(
        name="addmission", aliases=["addmissions"], help="Add missions to a category."
    )
    async def _add_missions(self, ctx):
        if self.cur_tournament is None:
            await ctx.send("There is no active/scheduled tournament!", delete_after=15)
            return
        await self._update_tournament()
        embed = doom_embed(
            title="Add Missions Wizard",
            desc=(
                "Add missions for each tournament category (TA, MC, etc.) for the chosen mission cateogry.\n"
            ),
        )
        embed.add_field(
            name="General Missions",
            value=(
                "Only one general mission is allowed."
                "Accepted general mission types: __xp, missions, top__\n"
                "These are short for __XP Threshold (excluding mission XP), Complete X missions in Y category, and Get top 3 in X categories.__\n"
                "Example: `xp - 4000` | `missions - 3 hard` | `top - 3`\n\n"
                "_Use this format as shown:_\n"
                "**GENERAL MISSION TYPE** - **GENERAL MISSION TARGET**\n"
            ),
        )
        embed.add_field(
            name="Category Missions",
            value=(
                "Accepted mission types: __sub, complete__\n"
                "Example: `sub - 15` | `complete`\n"
                "_Sub X_ targets _must_ be in seconds\n\n"
                "_Use this format as shown:_\n"
                "**TA MISSION TYPE** - **TA MISSION TARGET**\n"
                "**MC MISSION TYPE** - **MC MISSION TARGET**\n"
                "**HC MISSION TYPE** - **HC MISSION TARGET**\n"
                "**BO MISSION TYPE** - **BO MISSION TARGET**\n"
            ),
        )
        view = MissionCategories(ctx.author)
        await ctx.send(embed=embed, view=view, delete_after=120)

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.author

        response = await self.bot.wait_for("message", check=check, timeout=120)

        if view.category == "general":
            line = response.content.split(" - ")
            missions = self.cur_tournament.missions["general"]

            missions["general"] = {"type": line[0], "target": line[1]}
            self.cur_tournament.missions["general"] = missions
        else:
            missions = self.cur_tournament.missions
            lines = [line.split(" - ") for line in response.content.split("\n")]
            for line in lines:
                if len(line) == 1:
                    line[1] = line[0]
            missions[view.category]["ta"] = {
                "type": lines[0][0],
                "target": lines[0][1],
            }
            missions[view.category]["mc"] = {
                "type": lines[1][0],
                "target": lines[1][1],
            }
            missions[view.category]["hc"] = {
                "type": lines[2][0],
                "target": lines[2][1],
            }
            missions[view.category]["bo"] = {
                "type": lines[3][0],
                "target": lines[3][1],
            }
            self.cur_tournament.missions = missions

        formatted = await _format_missions(view.category, missions)

        embed = doom_embed(title="Missions Preview", desc=formatted)

        view = Confirm("Missions Confirmation", ctx.author)
        confirmation_msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await confirmation_msg.edit(
                content="Confirmed. Missions added.", delete_after=15, view=view
            )
            await self.cur_tournament.commit()
        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted.",
                delete_after=15,
                view=view,
            )
        elif view.value is None:
            await confirmation_msg.edit(
                content="Confirmation timed out!",
                view=view,
                delete_after=15,
            )

    @commands.has_role(constants_bot.ORG_ROLE_ID)
    @commands.command(
        name="removemissions",
        aliases=["removemission", "deletemissions", "deletemission"],
        help="Removes all missions from the selected mission category.",
    )
    async def _remove_missions(self, ctx):
        await self._update_tournament()
        embed = doom_embed(
            title="Remove Missions Wizard",
            desc="This will remove all missions in the selected mission category.",
        )
        view = RemoveMissions(ctx.author)
        confirmation_msg = await ctx.send(embed=embed, view=view, delete_after=30)
        await view.wait()

        if view.value:
            await confirmation_msg.edit(
                content="Confirmed. Missions removed.", delete_after=15, view=view
            )
            for cat in view.category:
                self.cur_tournament.missions[cat] = {
                    "ta": None,
                    "mc": None,
                    "hc": None,
                    "bo": None,
                }
            await self.cur_tournament.commit()
        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted.",
                delete_after=15,
                view=view,
            )
        elif view.value is None:
            await confirmation_msg.edit(
                content="Confirmation timed out!",
                view=view,
                delete_after=15,
            )

    @commands.has_role(constants_bot.ORG_ROLE_ID)
    @commands.command(
        name="missions",
        aliases=["announcemissions"],
    )
    async def _announce_missions(self, ctx):
        await self._update_tournament()
        missions = self.cur_tournament.missions

        embed = doom_embed(title="Tournament Missions!")
        for m_cat in ["general", "easy", "medium", "hard", "expert"]:
            formatted = _format_missions(m_cat, missions)
            embed.add_field(name=m_cat.capitalize(), value=formatted)

        # Make confirmation
        # MAke mention dropdown
        view = ScheduleView(ctx.author)
        confirmation_msg = await ctx.channel.send("Respond with a scheduled time if option is selected.", embed=embed, view=view)
        await view.wait()

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.author
        
        if view.value:
            mentions = ""
            for m in view.mentions:
                mentions += self._mentions(m)
            
            if not view.schedule:
                await confirmation_msg.edit(
                    content="Confirmed.",
                    delete_after=15,
                    view=view,
                )
                await self.info_channel.send(mentions, embed=embed)
                return
            
            response = await self.bot.wait_for("message", check=check, timeout=120)
            schedule = dateparser.parse(
                response, settings={"PREFER_DATES_FROM": "future"}
            )
            unix_schedule = str(time.mktime(schedule.timetuple()))[:-2]
            announcement = AnnoucementSchedule(**{
                "embed": embed.to_dict(),
                "mentions": mentions,
                "schedule": schedule,
            })
            await announcement.commit()
            await confirmation_msg.edit(
                content=f"Scheduled for <t:{unix_schedule}:R> - <t:{unix_schedule}:F>",
                delete_after=15,
                view=view,
            )


        elif not view.value:
            await confirmation_msg.edit(
                content="Not confirmed.",
                delete_after=15,
                view=view,
            )
        elif view.value is None:
            await confirmation_msg.edit(
                content="Confirmation timed out!",
                view=view,
                delete_after=15,
            )


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament2(bot))
