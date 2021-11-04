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


async def _setup_db(name, start, end, embed):
    last_tournament_id = await TournamentData().find(sort=[("tournament_id", -1)], limit=1).to_list(1)
    if not last_tournament_id:
        last_tournament_id = 0
    tournament_id = last_tournament_id + 1

    data = {
        "tournament_id": tournament_id,
        "name": name,
        "schedule_start": start,
        "schedule_end": end,
        "embed_dict": embed
    }

    tournament = TournamentData(**data)


class Tournament2(commands.Cog, name="Tournament2"):
    """Tournament2"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):
        logger.info(await _setup_db())
        # x = await TournamentData().find_one()
        # # This is for init the
        # # x.tournament_id = 1
        # # x.name = "Test"
        # # x.records = TournamentRecords()
        # logger.info(x.records)
        # logger.info(x.records.ta)
        # x.records.ta += [TimeAttackData(**{"posted_by": 2, "name": "test2", "record": 2.0, "attachment_url": "test2"})]
        #
        # await x.commit()



def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament2(bot))
