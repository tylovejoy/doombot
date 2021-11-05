import asyncio
import datetime
import time
import sys
from logging import getLogger
from utils.embeds import doom_embed
import dateparser
import discord
from discord.ext import commands, tasks
from internal.database import (
    BonusData,
    HardcoreData,
    MildcoreData,
    TimeAttackData,
    TopThree,
    TournamentData,
    TournamentRecords,
)
from utils.tournament_utils import lock_unlock
from utils.views import Confirm

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
        if not latest_tournament or latest_tournament.schedule_end > datetime.datetime.utcnow():
            return
        else:
            self.cur_tournament = latest_tournament

        if (
            datetime.datetime.utcnow()
            >= self.cur_tournament.schedule_start
            != datetime.datetime(year=1, month=1, day=1)
        ):
            logger.info("Starting scheduled tournament.")
            await self._start_round()
            self.cur_tournament.schedule_start = datetime.datetime(
                year=1, month=1, day=1
            )
            await self.cur_tournament.commit()

        if datetime.datetime.utcnow() >= self.cur_tournament.schedule_end:
            logger.info("Ending scheduled tournament.")
            await self._end_round()

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
            }
        )
        maps = {
            "ta": data["ta"],
            "mc": data["mc"],
            "hc": data["hc"],
            "bo": data["bo"],
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

    async def _unlock_all(self):
        await lock_unlock(
            [self.ta_channel, self.mc_channel, self.hc_channel, self.bonus_channel],
            [self.ta_role, self.trifecta_role, self.bracket_role],
            unlock=True,
        )

    async def _start_round(self):
        await self._unlock_all()
        mentions = (
            f"{self.ta_role.mention} "
            f"{self.mc_role.mention} "
            f"{self.hc_role.mention} "
            f"{self.bonus_role.mention} "
            f"{self.trifecta_role.mention} "
        )
        tournament: TournamentData = self.cur_tournament
        embed = doom_embed(
            title=tournament.name,
            desc=f"**Ends** <t:{tournament.unix_end}:R> -- <t:{tournament.unix_end}:F>\n",
        )

        embed.add_field(
            name="Time Attack", value=display_maps(tournament.maps["ta"]), inline=False
        )
        embed.add_field(
            name="Mildcore", value=display_maps(tournament.maps["mc"]), inline=False
        )
        embed.add_field(
            name="Hardcore", value=display_maps(tournament.maps["hc"]), inline=False
        )
        embed.add_field(
            name="Bonus", value=display_maps(tournament.maps["bo"]), inline=False
        )
        await self.info_channel.send(mentions, embed=embed)

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
                "**Start Time**\n"
                "**End Time**\n"
                "TA_CODE - LEVEL - CREATOR\n"
                "MC_CODE - LEVEL - CREATOR\n"
                "HC_CODE - LEVEL - CREATOR\n"
                "BO_CODE - LEVEL - CREATOR\n"
            ),
        )
        wizard = await ctx.send(embed=embed)
        results = {}

        response = await self.bot.wait_for("message", check=check, timeout=30)
        lines = response.content.split("\n")

        await wizard.delete()
        await response.delete()

        results["title"] = lines[0]

        results["start_time"] = dateparser.parse(
            lines[1], settings={"PREFER_DATES_FROM": "future"}
        )
        results["end_time"] = dateparser.parse(
            lines[2], settings={"PREFER_DATES_FROM": "future"}
        )

        # end_time = results["end_time"].isoformat()
        if results["start_time"]:
            delta = results["end_time"] - datetime.datetime.now()
            end_time = results["start_time"] + delta
            # end_time = end_time.isoformat()

        results["unix_start"] = str(time.mktime(results["start_time"].timetuple()))[:-2]
        results["unix_end"] = str(time.mktime(end_time.timetuple()))[:-2]

        results["ta"] = parse_map(lines[3])
        results["mc"] = parse_map(lines[4])
        results["hc"] = parse_map(lines[5])
        results["bo"] = parse_map(lines[6])

        embed = doom_embed(
            title="",
            desc=(
                f"**{results['title']}**\n"
                f"**Start:** <t:{results['unix_start']}:R> -- <t:{results['unix_start']}:F>\n"
                f"**End:** <t:{results['unix_end']}:R> -- <t:{results['unix_end']}:F>\n"
                f"**{results['ta']['code']}** - {results['ta']['level']} by {results['ta']['author']}\n"
                f"**{results['mc']['code']}** - {results['mc']['level']} by {results['mc']['author']}\n"
                f"**{results['hc']['code']}** - {results['hc']['level']} by {results['hc']['author']}\n"
                f"**{results['bo']['code']}** - {results['bo']['level']} by {results['bo']['author']}\n"
            ),
        )

        view = Confirm("Start Tournament Wizard", ctx.author)
        confirmation_msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await self._setup_db(results)
            await confirmation_msg.edit(
                content=f"Scheduled tournament confirmed for <t:{results['unix_start']}:R> -- <t:{results['unix_start']}:F>",
                embed=None,
                view=view,
            )

        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted. Nothing will be changed."
            )
        elif view.value is None:
            await confirmation_msg.edit(content="Timed out. Nothing will be changed.")


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament2(bot))
