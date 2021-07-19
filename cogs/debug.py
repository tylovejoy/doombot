from discord.ext import commands
from jishaku.cog import JishakuBase, jsk
from jishaku.metacog import GroupCogMeta


class Debugging(JishakuBase, metaclass=GroupCogMeta, command_parent=jsk):
    """Add default Jishaku debugging as a cog."""


def setup(bot: commands.Bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Debugging(bot))
