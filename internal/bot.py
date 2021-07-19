import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

from utils.pretty_help import PrettyHelp

# Logging setup
logger = logging.getLogger(__name__)


DOOMBOT_ASCII = r"""
______  _____  _____ ___  _________  _____  _____
|  _  \|  _  ||  _  ||  \/  || ___ \|  _  ||_   _|
| | | || | | || | | || .  . || |_/ /| | | |  | |
| | | || | | || | | || |\/| || ___ \| | | |  | |
| |/ / \ \_/ /\ \_/ /| |  | || |_/ /\ \_/ /  | |
|___/   \___/  \___/ \_|  |_/\____/  \___/   \_/
"""


class Bot(commands.Bot):
    """Discord Bot."""

    def __init__(self, **kwargs):
        """Initialize Bot."""
        super().__init__(
            command_prefix=commands.when_mentioned_or(*kwargs.pop("prefix")),
            description=kwargs.pop("description"),
            intents=discord.Intents.all(),
            case_insensitive=kwargs.pop("case_insensitive"),
            help_command=PrettyHelp(show_index=False, color=discord.Color.purple()),
        )
        self.app_info = None

        self.loop.create_task(self.load_all_extensions())

    async def load_all_extensions(self):
        """Load all *.py files in /cogs/ as Cogs."""
        await self.wait_until_ready()
        await asyncio.sleep(
            1
        )  # Ensure that on_ready has completed and finished printing
        cogs = [x.stem for x in Path("cogs").glob("*.py")]
        logger.info("Loading extensions...")
        for extension in cogs:
            try:
                self.load_extension(f"cogs.{extension}")
                logger.info(f"Loading {extension}...")
            except Exception as e:
                error = f"{extension}\n {type(e).__name__} : {e}"
                logger.info(f"failed to load extension {error}")
        logger.info("Extensions loaded.")

    async def on_ready(self):
        """Display app info when bot comes online."""
        self.app_info = await self.application_info()
        logger.info(
            f"{DOOMBOT_ASCII}"
            f"\nLogged in as: {self.user.name}\n"
            f"Using discord.py version: {discord.__version__}\n"
            f"Owner: {self.app_info.owner}\n"
        )

    async def on_message(self, message):
        """Allow bot to ignore all other bots."""
        if message.author.bot:
            return
        await self.process_commands(message)
