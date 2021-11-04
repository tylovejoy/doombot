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


if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


def parse_maps(text):
    lines = text.split("\n")
    for line in lines:
        line.split(" - ")
    maps = {
        "ta": {"code": lines[0][0], "map": lines[0][1], "author": lines[0][2]},
        "mc": {"code": lines[1][0], "map": lines[1][1], "author": lines[1][2]},
        "hc": {"code": lines[2][0], "map": lines[2][1], "author": lines[2][2]},
        "bo": {"code": lines[3][0], "map": lines[3][1], "author": lines[3][2]},
    }
    return maps

def display_maps(maps):
    string = ""
    for key in maps["ta"].keys():
        string += maps["ta"][key]
    string += "\n"
    for key in maps["mc"].keys():
        string += maps["mc"][key]
    string += "\n"
    for key in maps["hc"].keys():
        string += maps["hc"][key]
    string += "\n"
    for key in maps["bo"].keys():
        string += maps["bo"][key]
    return string


class Tournament2(commands.Cog, name="Tournament2"):
    """Tournament2"""

    def __init__(self, bot):
        self.bot = bot
        self.cur_tournament = None

    async def _setup_db(self, name, start, end, maps, embed):
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
            "embed_dict": embed,
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
            ctx.send("You cannot start a tournament while another one is active.")
            return

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.author

        # Begin Questions Wizard
        wizard_embed = doom_embed("Tournament Start Wizard", desc="What's the title for this tournament?")
        wizard = await ctx.send(embed=wizard_embed)
        wizard_results = {}

        title_response = await self.bot.wait_for("message", check=check, timeout=30)
        wizard_results["title": title_response.content]
        wizard_embed.add_field(name="Title:", value=title_response.content)
        await title_response.delete()
        wizard_embed.desc = "What are the maps for this tournament?"
        await wizard.edit(embed=wizard_embed)

        maps_response = await self.bot.wait_for("message", check=check, timeout=30)
        maps = parse_maps(maps_response.content)
        await maps_response.delete()
        maps_str = display_maps(maps)
        wizard_results["maps": maps]
        wizard_embed.add_field(name="Maps:", value=maps_str)
        wizard_embed.desc = "When should this tournament begin?"
        await wizard.edit(embed=wizard_embed)

        start_response = await self.bot.wait_for("message", check=check, timeout=30)
        
        start_time = dateparser.parse(
            start_response.content, settings={"PREFER_DATES_FROM": "future"}
        )
        start_unix = time.mktime(start_time.timetuple())
        wizard_embed.add_field(
            name="Start Time:", value=f"<t:{start_unix}:R>\n<t:{start_unix}:F>"
        )
        wizard_embed.desc = "When should this tournament end?"
        await wizard.edit(embed=wizard_embed)
        end_response = await self.bot.wait_for("message", check=check, timeout=30)
        end = dateparser.parse(
            end_response.content, settings={"PREFER_DATES_FROM": "future"}
        )

        end_time = end.isoformat()

        if start_time:
            delta = end - datetime.datetime.now()
            end_time = start_time + delta
            end_time = end_time.isoformat()

        end_unix = time.mktime(end_time.timetuple())
        wizard_embed.add_field(name="End Time:", value=f"<t:{end_unix}:R>\n<t:{end_unix}:F>")



        await self._setup_db(wizard_results["title"], start_time, end_time, maps, {})


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament2(bot))
