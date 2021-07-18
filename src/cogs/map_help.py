import sys
from logging import getLogger

import internal.constants as constants
from discord.ext import commands
from disputils import MultipleChoice
from internal.database import Guides
from utils.map_utils import guide_duplicate_check
from utils.views import Confirm, GuidePaginator

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


class MapHelp(commands.Cog, name="Helpful Map Commands"):
    """Helpful map commands/utility.

    Shows user acceptable map names and map types to use with other commands.
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if commands are used in MAP_CHANNEL and MAP_SUBMIT_CHANNEL."""
        if (
            ctx.channel.id
            in (
                constants_bot.MAP_CHANNEL_ID,
                constants_bot.MAP_SUBMIT_CHANNEL_ID,
            )
            or (ctx.guild is None)
        ):
            return True

    @commands.command(
        help="Shows all acceptable map names for commands",
        brief="Shows map names for commands",
    )
    async def maps(self, ctx):
        """Display acceptable map names for use in other commands."""
        await ctx.message.delete()
        post = ""
        for maps in constants.ALL_MAP_NAMES:
            post += " | ".join(maps) + "\n"
        await ctx.send(f"```Acceptable map names:\n{post}```", delete_after=30)

    @commands.command(
        aliases=["types"],
        help="Shows all acceptable map types for commands",
        brief="Shows map types for commands",
    )
    async def maptypes(self, ctx):
        """Display acceptable map types for use in other commands."""
        await ctx.message.delete()
        await ctx.send(
            "Map types:\n```\n" + "\n".join(constants.TYPES_OF_MAP) + "```",
            delete_after=30,
        )

    @commands.command(help="", brief="", aliases=[])
    async def submitguide(self, ctx: commands.Context, map_code: str, url: str):
        await ctx.message.delete()
        map_code = map_code.upper()

        search = await Guides.find_one({"code": map_code})
        if search is None:
            search = Guides(**dict(code=map_code))
        if search.guide is not None and await guide_duplicate_check(search.guide, url):
            await ctx.send("Duplicate entry. Submission failed.", delete_after=10)
            return

        if search.guide:
            search.guide = search.guide + [url]
            search.guide_owner = search.guide_owner + [ctx.author.id]

        else:
            search.guide = [url]
            search.guide_owner = [ctx.author.id]

        view = Confirm("Submission", ctx.author)

        confirm = await ctx.send(
            f"Is this the correct link for **{map_code}**?\n{url}", view=view
        )
        await view.wait()

        if view.value:
            await search.commit()
            await confirm.edit(view=view, delete_after=1)
        if not view.value:
            await confirm.edit(view=view, delete_after=1)
        if view.value is None:
            await confirm.edit(view=view, delete_after=1)

    @commands.command(
        help="Search for a guide for a specific map code.",
        brief="",
    )
    async def guide(self, ctx, map_code):
        await ctx.message.delete()
        map_code = map_code.upper()
        search = await Guides.find_one({"code": map_code})
        if not search or not search.guide:
            await ctx.send(f"There are no guides for {map_code} yet.", delete_after=10)
            return
        links = []
        for url in search.guide:
            links.append(url)

        if len(links) == 1:
            await ctx.send(content=links[0], delete_after=120)
        else:
            view = GuidePaginator(links, ctx.author)
            paginator = await ctx.send(content=view.pages[0], view=view)
            await view.wait()
            await paginator.delete()

    @commands.command(help="", brief="", aliases=[])
    async def deleteguide(self, ctx, map_code):
        await ctx.message.delete()
        map_code = map_code.upper()
        search: Guides = await Guides.find_one({"code": map_code})

        if search is None:
            await ctx.send(f"There are no guides for {map_code} yet.", delete_after=10)
            return

        index = 0
        owned_indexes = []
        for owner in search.guide_owner:
            if owner == ctx.author.id or any(
                role.id in constants_bot.ROLE_WHITELIST for role in ctx.author.roles
            ):
                owned_indexes.append(index)
            index += 1

        owned_urls = []
        for i in owned_indexes:
            owned_urls.append(search.guide[i])

        choices = MultipleChoice(
            self.bot,
            [f"{i + 1} | {url} \n" for i, url in enumerate(owned_urls)],
            "Which guide should be deleted?",
        )
        await choices.run(users=[ctx.author], channel=ctx.channel)
        answer = choices.choice
        await choices.quit()
        if answer is None:
            return
        choice_number = int(answer[0]) - 1
        url_to_delete = None
        new_guide = []
        new_guide_owner = []
        for i, guide in enumerate(search.guide):
            if i == choice_number:
                url_to_delete = guide
                continue
            new_guide.append(guide)
        for i, owner in enumerate(search.guide_owner):
            if i == choice_number:
                continue
            new_guide_owner.append(owner)
        search.guide = new_guide
        search.guide_owner = new_guide_owner

        view = Confirm("Deletion", ctx.author)
        msg = await ctx.send(
            f"Do you want to delete this guide?\n{url_to_delete}", view=view
        )
        await view.wait()
        await msg.edit(view=view)
        if view.value:
            await search.commit()
        elif not view.value:
            pass
        elif view.value is None:
            pass


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(MapHelp(bot))
