import asyncio
import datetime
import sys
from logging import getLogger

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


class Tournament2(commands.Cog, name="Tournament2"):
    """Tournament2"""

    def __init__(self, bot):
        self.bot = bot
        self.cur_tournament = None

    async def _setup_db(self, name, start, end, maps, embed):
        if self.cur_tournament:
            # TODO: Dont allow multiple tournaments.
            pass

        last_tournament = await TournamentData().find_one(
            sort=[("tournament_id", -1)], limit=1
        )
        if last_tournament:
            tournament_id = last_tournament.tournament_id + 1
        else:
            tournament_id = 1
        self.cur_tournament = tournament_id

        tournament = TournamentData(
            **{
                "tournament_id": tournament_id,
                "name": name,
                "schedule_start": start,
                "schedule_end": end,
                "embed_dict": embed,
            }
        )
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

    @commands.command()
    async def test(self, ctx):
        maps = {
            "ta": {"code": "CODE", "map": "MAP", "author": "AUTHOR"},
            "mc": {"code": "CODE", "map": "MAP", "author": "AUTHOR"},
            "hc": {"code": "CODE", "map": "MAP", "author": "AUTHOR"},
            "bo": {"code": "CODE", "map": "MAP", "author": "AUTHOR"},
        }
        logger.info(await self._setup_db("test", "1", "1", maps, {}))


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament2(bot))
