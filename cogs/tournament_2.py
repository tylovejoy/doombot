import asyncio
import datetime
import time
import sys
from logging import getLogger
from utils.embeds import doom_embed
import dateparser
import discord
from discord.ext import commands
from internal.database import (
    BonusData,
    HardcoreData,
    MildcoreData,
    TimeAttackData,
    TopThree,
    TournamentData,
    TournamentRecords,
)
from utils.views import Confirm

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


def parse_map(text):
    for x in text:
        x.split(" - ")
    return {"code": x[0], "level": x[1], "author": x[2]}


def display_maps(maps):
    string = ""
    for key in maps.keys():
        string += maps[key]
    return string


class Tournament2(commands.Cog, name="Tournament2"):
    """Tournament2"""

    def __init__(self, bot):
        self.bot = bot
        self.cur_tournament = None

    async def _setup_db(self, name, start, end, maps):
        last_tournament = await TournamentData().find_one(
            sort=[("tournament_id", -1)], limit=1
        )
        if last_tournament:
            tournament_id = last_tournament.tournament_id + 1
        else:
            tournament_id = 1

        tournament = TournamentData(**{
            "tournament_id": tournament_id,
            "name": name,
            "schedule_start": start,
            "schedule_end": end,
        })
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


    @commands.command()
    async def start(self, ctx):
        if self.cur_tournament:
            ctx.send("You cannot start a tournament while another one is active.", delete_after=10)
            return

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.author

        # Begin Questions Wizard
        wizard_embed = doom_embed(
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
            )
        )
        wizard = await ctx.send(embed=wizard_embed)
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

        end_time = results["end_time"].isoformat()
        if results["start_time"]:
            delta = results["end_time"] - datetime.datetime.now()
            end_time = results["start_time"] + delta
            end_time = end_time.isoformat()
        start_unix = time.mktime(results["start_time"].timetuple())
        end_unix = time.mktime(end_time.timetuple())


        results["ta"] = parse_map(lines[3])
        results["mc"] = parse_map(lines[4])
        results["hc"] = parse_map(lines[5])
        results["bo"] = parse_map(lines[6])

        embed = doom_embed(desc=(
            f"**{results['title']}**\n"
            f"<t:{start_unix}:R> -- <t:{start_unix}:F>\n"
            f"<t:{end_unix}:R> -- <t:{end_unix}:F>\n"
            f"**{display_maps(results['ta'])}**\n"
            f"**{display_maps(results['mc'])}**\n"
            f"**{display_maps(results['hc'])}**\n"
            f"**{display_maps(results['bo'])}**\n"
        ))
        maps = {
            "ta": results["ta"],
            "mc": results["mc"],
            "hc": results["hc"],
            "bo": results["bo"],
        }

        view = Confirm("Start Tournament Wizard", ctx.author)
        confirmation_msg = await ctx.send("Is this correct?", embed=embed, view=view)
        await view.wait()

        if view.value:
            pass

        elif not view.value:
            await confirmation_msg.edit(
                content="Not accepted. Nothing will be changed."
            )
        elif view.value is None:
            await confirmation_msg.edit(content="Timed out. Nothing will be changed.")
        
        
        await self._setup_db(results["title"], results["start_time"], results["end_time"], maps)


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament2(bot))
