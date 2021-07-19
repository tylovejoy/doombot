import asyncio
import sys

import discord
from discord.ext import commands

import internal.constants as constants
from utils.map_utils import convert_short_types, normal_map_query, searchmap

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


class MapSearch(commands.Cog, name="Map Search"):
    """A collection of map search commands."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if command is used in MAP_CHANNEL."""
        if ctx.channel.id == constants_bot.MAP_CHANNEL_ID or (ctx.guild is None):
            return True

    @commands.command(
        aliases=constants.AYUTTHAYA[1:],
        help="Display all Ayutthaya maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Ayutthaya maps.",
        hidden=True,
    )
    async def ayutthaya(self, ctx, map_type=""):
        """Search for and display all Ayutthaya maps."""
        map_name = "Ayutthaya"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.BLACKFOREST[1:],
        help="Display all Black Forest maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Black Forest maps.",
        hidden=True,
    )
    async def blackforest(self, ctx, map_type=""):
        """Search for and display all Black Forest maps."""
        map_name = "Black Forest"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.BLIZZARDWORLD[1:],
        help="Display all Blizzard World maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Blizzard World maps.",
        hidden=True,
    )
    async def blizzardworld(self, ctx, map_type=""):
        """Search for and display all Blizzard World maps."""
        map_name = "Blizzard World"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.BUSAN[1:],
        help="Display all Busan maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Busan maps.",
        hidden=True,
    )
    async def busan(self, ctx, map_type=""):
        """Search for and display all Busan maps."""
        map_name = "Busan"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.CASTILLO[1:],
        help="Display all Castillo maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Castillo maps.",
        hidden=True,
    )
    async def castillo(self, ctx, map_type=""):
        """Search for and display all Castillo maps."""
        map_name = "Castillo"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.CHATEAUGUILLARD[1:],
        help="Display all Chateau Guillard maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Chateau Guillard maps.",
        hidden=True,
    )
    async def chateauguillard(self, ctx, map_type=""):
        """Search for and display all Chateau Guillard maps."""
        map_name = "Chateau Guillard"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.DORADO[1:],
        help="Display all Dorado maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Dorado maps.",
        hidden=True,
    )
    async def dorado(self, ctx, map_type=""):
        """Search for and display all Dorado maps."""
        map_name = "Dorado"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.EICHENWALDE[1:],
        help="Display all Eichenwalde maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Eichenwalde maps.",
        hidden=True,
    )
    async def eichenwalde(self, ctx, map_type=""):
        """Search for and display all Eichenwalde maps."""
        map_name = "Eichenwalde"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.HANAMURA[1:],
        help="Display all Hanamura maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Hanamura maps.",
        hidden=True,
    )
    async def hanamura(self, ctx, map_type=""):
        """Search for and display all Hanamura maps."""
        map_name = "Hanamura"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.HAVANA[1:],
        help="Display all Havana maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Havana maps.",
        hidden=True,
    )
    async def havana(self, ctx, map_type=""):
        """Search for and display all Havana maps."""
        map_name = "Havana"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.HOLLYWOOD[1:],
        help="Display all Hollywood maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Hollywood maps.",
        hidden=True,
    )
    async def hollywood(self, ctx, map_type=""):
        """Search for and display all Hollywood maps."""
        map_name = "Hollywood"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.HORIZONLUNARCOLONY[1:],
        help="Display all Horizon Lunar Colony maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Horizon Lunar Colony maps.",
        hidden=True,
    )
    async def horizonlunarcolony(self, ctx, map_type=""):
        """Search for and display all Horizon Lunar Colony maps."""
        map_name = "Horizon Lunar Colony"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.ILIOS[1:],
        help="Display all Ilios maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Ilios maps.",
        hidden=True,
    )
    async def ilios(self, ctx, map_type=""):
        """Search for and display all Ilios maps."""
        map_name = "Ilios"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.JUNKERTOWN[1:],
        help="Display all Junkertown maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Junkertown maps.",
        hidden=True,
    )
    async def junkertown(self, ctx, map_type=""):
        """Search for and display all Junkertown maps."""
        map_name = "Junkertown"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.LIJIANGTOWER[1:],
        help="Display all Lijiang Tower maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Lijiang Tower maps.",
        hidden=True,
    )
    async def lijiangtower(self, ctx, map_type=""):
        """Search for and display all Lijiang Tower maps."""
        map_name = "Lijiang Tower"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.NECROPOLIS[1:],
        help="Display all Necropolis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Necropolis maps.",
        hidden=True,
    )
    async def necropolis(self, ctx, map_type=""):
        """Search for and display all Necropolis maps."""
        map_name = "Necropolis"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.NEPAL[1:],
        help="Display all Nepal maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Nepal maps.",
        hidden=True,
    )
    async def nepal(self, ctx, map_type=""):
        """Search for and display all Nepal maps."""
        map_name = "Nepal"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.NUMBANI[1:],
        help="Display all Numbani maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Numbani maps.",
        hidden=True,
    )
    async def numbani(self, ctx, map_type=""):
        """Search for and display all Numbani maps."""
        map_name = "Numbani"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.OASIS[1:],
        help="Display all Oasis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Oasis maps.",
        hidden=True,
    )
    async def oasis(self, ctx, map_type=""):
        """Search for and display all Oasis maps."""
        map_name = "Oasis"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.PARIS[1:],
        help="Display all Paris maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Paris maps.",
        hidden=True,
    )
    async def paris(self, ctx, map_type=""):
        """Search for and display all Paris maps."""
        map_name = "Paris"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.RIALTO[1:],
        help="Display all Rialto maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Rialto maps.",
        hidden=True,
    )
    async def rialto(self, ctx, map_type=""):
        """Search for and display all Rialto maps."""
        map_name = "Rialto"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.ROUTE66[1:],
        help="Display all Route 66 maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Route 66 maps.",
        hidden=True,
    )
    async def route66(self, ctx, map_type=""):
        """Search for and display all Route 66 maps."""
        map_name = "Route 66"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.TEMPLEOFANUBIS[1:],
        help="Display all Temple of Anubis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Temple of Anubis maps.",
        hidden=True,
    )
    async def templeofanubis(self, ctx, map_type=""):
        """Search for and display all Temple of Anubis maps."""
        map_name = "Temple of Anubis"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.VOLSKAYAINDUSTRIES[1:],
        help="Display all Volskaya Industries maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Volskaya Industries maps.",
        hidden=True,
    )
    async def volskayaindustries(self, ctx, map_type=""):
        """Search for and display all Volskaya Industries maps."""
        map_name = "Volskaya Industries"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WATCHPOINTGIBRALTAR[1:],
        help="Display all Watchpoint Gibraltar maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Watchpoint Gibraltar maps.",
        hidden=True,
    )
    async def watchpointgibraltar(self, ctx, map_type=""):
        """Search for and display all Watchpoint Gibraltar maps."""
        map_name = "Watchpoint Gibraltar"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.KINGSROW[1:],
        help="Display all King's Row maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all King's Row maps.",
        hidden=True,
    )
    async def kingsrow(self, ctx, map_type=""):
        """Search for and display all King's Row maps."""
        map_name = "King's Row"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.PETRA[1:],
        help="Display all Petra maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Petra maps.",
        hidden=True,
    )
    async def petra(self, ctx, map_type=""):
        """Search for and display all Petra maps."""
        map_name = "Petra"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.ECOPOINTANTARCTICA[1:],
        help="Display all Ecopoint Antarctica maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Ecopoint Antarctica maps.",
        hidden=True,
    )
    async def ecopointantarctica(self, ctx, map_type=""):
        """Search for and display all Ecopoint Antarctica maps."""
        map_name = "Ecopoint Antarctica"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.KANEZAKA[1:],
        help="Display all Kanezaka maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Kanezaka maps.",
        hidden=True,
    )
    async def kanezaka(self, ctx, map_type=""):
        """Search for and display all Kanezaka maps."""
        map_name = "Kanezaka"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WORKSHOPCHAMBER[1:],
        help="Display all Workshop Chamber maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Chamber maps.",
        hidden=True,
    )
    async def workshopchamber(self, ctx, map_type=""):
        """Search for and display all Workshop Chamber maps."""
        map_name = "Workshop Chamber"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WORKSHOPEXPANSE[1:],
        help="Display all Workshop Expanse maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Expanse maps.",
        hidden=True,
    )
    async def workshopexpanse(self, ctx, map_type=""):
        """Search for and display all Workshop Expanse maps."""
        map_name = "Workshop Expanse"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WORKSHOPGREENSCREEN[1:],
        help="Display all Workshop Greenscreen maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Greenscreen maps.",
        hidden=True,
    )
    async def workshopgreenscreen(self, ctx, map_type=""):
        """Search for and display all Workshop Greenscreen maps."""
        map_name = "Workshop Greenscreen"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WORKSHOPISLAND[1:],
        help="Display all Workshop Island maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Island maps.",
        hidden=True,
    )
    async def workshopisland(self, ctx, map_type=""):
        """Search for and display all Workshop Island maps."""
        map_name = "Workshop Island"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.PRACTICERANGE[1:],
        help="Display all Practice Range maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Practice Range maps.",
        hidden=True,
    )
    async def practicerange(self, ctx, map_type=""):
        """Search for and display all Practice Range maps."""
        map_name = "Practice Range"
        map_type = convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await searchmap(ctx, query, map_type=map_type, map_name=map_name)


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(MapSearch(bot))
