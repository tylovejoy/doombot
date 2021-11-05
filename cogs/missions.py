from logging import getLogger
import sys

from discord.ext import commands

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


class Missions(commands.Cog, name="Missions for tournaments."):
    """Missions."""

    def __init__(self, bot):
        self.bot = bot
