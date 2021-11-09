import sys
from copy import deepcopy
from logging import getLogger
from typing import List

import discord

from internal.database import WorldRecords

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


class Confirm(discord.ui.View):
    def __init__(self, name, author):
        super().__init__()
        self.value = None
        self.name = name
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            f"{self.name} accepted.", ephemeral=True
        )
        self.value = True
        self.clear_items()
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"{self.name} rejected.", ephemeral=True
        )
        self.value = False
        self.clear_items()
        self.stop()


class Paginator(discord.ui.View):
    def __init__(self, embeds: [discord.Embed], author: discord.Member):
        super().__init__(timeout=120)
        self.pages = embeds
        self.author = author
        self._curr_page = 0
        if len(self.pages) == 1:
            self.first.disabled = True
            self.back.disabled = True
            self.next.disabled = True
            self.last.disabled = True

    @property
    def formatted_pages(self) -> List[discord.Embed]:
        """The embeds with formatted footers to act as pages."""

        pages = deepcopy(self.pages)  # copy by value not reference
        for page in pages:
            if page.footer.text == discord.Embed.Empty:
                page.set_footer(text=f"({pages.index(page) + 1}/{len(pages)})")
            else:
                page_index = pages.index(page)
                if page.footer.icon_url == discord.Embed.Empty:
                    page.set_footer(
                        text=f"{page.footer.text} - ({page_index + 1}/{len(pages)})"
                    )
                else:
                    page.set_footer(
                        icon_url=page.footer.icon_url,
                        text=f"{page.footer.text} - ({page_index + 1}/{len(pages)})",
                    )
        return pages

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.button(label="First", emoji="⏮")
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.pages) == 1:
            button.disabled = True
        self._curr_page = 0
        await interaction.response.edit_message(
            embed=self.formatted_pages[0], view=self
        )

    @discord.ui.button(label="Back", emoji="◀")
    async def back(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.pages) == 1:
            button.disabled = True
        if self._curr_page == 0:
            self._curr_page = len(self.pages) - 1
        else:
            self._curr_page -= 1
        await interaction.response.edit_message(
            embed=self.formatted_pages[self._curr_page], view=self
        )

    @discord.ui.button(label="Next", emoji="▶")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.pages) == 1:
            button.disabled = True
        if self._curr_page == len(self.pages) - 1:
            self._curr_page = 0
        else:
            self._curr_page += 1
        await interaction.response.edit_message(
            embed=self.formatted_pages[self._curr_page], view=self
        )

    @discord.ui.button(label="Last", emoji="⏭")
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.pages) == 1:
            button.disabled = True
        self._curr_page = len(self.pages) - 1
        await interaction.response.edit_message(
            embed=self.formatted_pages[-1], view=self
        )

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.stop()


class Verification(discord.ui.View):
    def __init__(self, message: discord.Message, bot):
        super().__init__(timeout=None)
        self.verify = None
        self.message = message
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not bool(
            any(
                role.id in constants_bot.ROLE_WHITELIST
                for role in interaction.user.roles
            )
        ):
            return False
        return True

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
    async def verify(self, button: discord.ui.Button, interaction: discord.Interaction):
        search = await WorldRecords.find_one({"message_id": self.message.id})
        guild = self.bot.get_guild(constants_bot.GUILD_ID)
        hidden_channel = guild.get_channel(constants_bot.HIDDEN_VERIFICATION_CHANNEL)
        try:
            hidden_msg = await hidden_channel.fetch_message(search.hidden_id)
            await hidden_msg.delete()
        except discord.HTTPException:
            pass

        search.verified = True
        self.verify = True
        self.clear_items()
        await search.commit()
        self.stop()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, button: discord.ui.Button, interaction: discord.Interaction):
        search = await WorldRecords.find_one({"message_id": self.message.id})
        guild = self.bot.get_guild(constants_bot.GUILD_ID)
        hidden_channel = guild.get_channel(constants_bot.HIDDEN_VERIFICATION_CHANNEL)
        try:
            hidden_msg = await hidden_channel.fetch_message(search.hidden_id)
            await hidden_msg.delete()
        except discord.HTTPException:
            pass

        search.verified = False
        self.verify = False
        self.clear_items()
        await search.commit()
        self.stop()


class TournamentChoices(discord.ui.View):
    def __init__(self, author, no_all=False):
        super().__init__(timeout=120)
        self.author = author
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.select(
        placeholder="Choose a category",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Time Attack", value="ta"),
            discord.SelectOption(label="Mildcore", value="mc"),
            discord.SelectOption(label="Hardcore", value="hc"),
            discord.SelectOption(label="Bonus", value="bo"),
            discord.SelectOption(label="All", value="all"),
        ],
    )
    async def callback(
        self, select: discord.ui.select, interaction: discord.Interaction
    ):
        self.value = int(select.values[0])
        self.clear_items()
        self.stop()


class TournamentChoicesNoAll(discord.ui.View):
    def __init__(self, author, no_all=False):
        super().__init__(timeout=120)
        self.author = author
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.select(
        placeholder="Choose a category",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Time Attack", value="ta"),
            discord.SelectOption(label="Mildcore", value="mc"),
            discord.SelectOption(label="Hardcore", value="hc"),
            discord.SelectOption(label="Bonus", value="bo"),
        ],
    )
    async def callback(
        self, select: discord.ui.select, interaction: discord.Interaction
    ):
        self.value = select.values[0]
        self.clear_items()
        self.stop()


class GuidePaginator(discord.ui.View):
    def __init__(self, links: [str], author: discord.Member):
        super().__init__(timeout=120)
        self.pages = links
        self.author = author
        self._curr_page = 0
        if len(self.pages) == 1:
            self.first.disabled = True
            self.back.disabled = True
            self.next.disabled = True
            self.last.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.button(label="First", emoji="⏮")
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.pages) == 1:
            button.disabled = True
        self._curr_page = 0
        await interaction.response.edit_message(content=self.pages[0], view=self)

    @discord.ui.button(label="Back", emoji="◀")
    async def back(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.pages) == 1:
            button.disabled = True
        if self._curr_page == 0:
            self._curr_page = len(self.pages) - 1
        else:
            self._curr_page -= 1
        await interaction.response.edit_message(
            content=self.pages[self._curr_page], view=self
        )

    @discord.ui.button(label="Next", emoji="▶")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.pages) == 1:
            button.disabled = True
        if self._curr_page == len(self.pages) - 1:
            self._curr_page = 0
        else:
            self._curr_page += 1
        await interaction.response.edit_message(
            content=self.pages[self._curr_page], view=self
        )

    @discord.ui.button(label="Last", emoji="⏭")
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.pages) == 1:
            button.disabled = True
        self._curr_page = len(self.pages) - 1
        await interaction.response.edit_message(content=self.pages[-1], view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.stop()


class BracketToggle(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.dropdown = CategoryDropdown()
        self.bracket = False
        self.bracket_cat = None
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.button(
        label="Bracket Mode Currently Off", style=discord.ButtonStyle.primary
    )
    async def toggle(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.bracket is False:
            self.bracket = True
            button.label = "Bracket Mode Currently On"
            button.style = discord.ButtonStyle.success
            self.add_item(self.dropdown)
            await interaction.response.edit_message(view=self)
        else:
            self.bracket = False
            button.label = "Bracket Mode Currently Off"
            button.style = discord.ButtonStyle.primary
            self.remove_item(self.dropdown)
            self.dropdown.bracket_cat = None
            await interaction.response.edit_message(view=self)


class CategoryDropdown(discord.ui.Select):
    def __init__(self, max_values=1):
        self.bracket_cat = None
        options = [
            discord.SelectOption(label="Time Attack", value="ta"),
            discord.SelectOption(label="Mildcore", value="mc"),
            discord.SelectOption(label="Hardcore", value="hc"),
            discord.SelectOption(label="Bonus", value="bo"),
        ]
        super().__init__(
            placeholder="Choose a category...",
            min_values=1,
            max_values=max_values,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if len(self.values) == 1:
            self.bracket_cat = self.values[0]
        else:
            self.bracket_cat = self.values


class MissionCategories(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.category = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.select(
        options=[
            discord.SelectOption(label="General", value="general"),
            discord.SelectOption(label="Easy", value="easy"),
            discord.SelectOption(label="Medium", value="medium"),
            discord.SelectOption(label="Hard", value="hard"),
            discord.SelectOption(label="Expert", value="expert"),
        ],
        placeholder="Choose a category...",
        min_values=1,
        max_values=1,
    )
    async def callback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):

        self.category = select.values[0]


class StartEndToggle(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.end = True
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.button(
        label="Currently Editing Start Time", style=discord.ButtonStyle.primary
    )
    async def toggle(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.end is False:
            self.end = True
            button.label = "Currently Editing End Time"
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
        else:
            self.end = False
            button.label = "Currently Editing Start Time"
            button.style = discord.ButtonStyle.primary
            await interaction.response.edit_message(view=self)


class ClearView(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.dropdown = CategoryDropdown(max_values=4)
        self.add_item(self.dropdown)
        self.author = author
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message(f"Cleared", ephemeral=True)
        self.value = True
        self.clear_items()
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(f"Not cleared.", ephemeral=True)
        self.value = False
        self.clear_items()
        self.stop()


class ScheduleView(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.schedule = False
        self.mentions = []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.button(
        label="Scheduled Annoucement Off", style=discord.ButtonStyle.primary
    )
    async def toggle(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.schedule is False:
            self.schedule = True
            button.label = "Scheduled Annoucement On"
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
        else:
            self.schedule = False
            button.label = "Scheduled Annoucement Off"
            button.style = discord.ButtonStyle.primary
            await interaction.response.edit_message(view=self)

    @discord.ui.select(
        options=[
            discord.SelectOption(label="Time Attack", value="ta"),
            discord.SelectOption(label="Mildcore", value="mc"),
            discord.SelectOption(label="Hardcore", value="hc"),
            discord.SelectOption(label="Bonus", value="bo"),
            discord.SelectOption(label="Trifecta", value="tr"),
            discord.SelectOption(label="Bracket", value="br"),
        ],
        placeholder="Choose which roles to be mentioned...",
        min_values=1,
        max_values=6,
    )
    async def callback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.mentions = select.values


class RemoveMissions(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.category = None
        self.author = author
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message(f"Missions removed.", ephemeral=True)
        self.value = True
        self.clear_items()
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(f"Nothing changed.", ephemeral=True)
        self.value = False
        self.clear_items()
        self.stop()

    @discord.ui.select(
        options=[
            discord.SelectOption(label="General", value="general"),
            discord.SelectOption(label="Easy", value="easy"),
            discord.SelectOption(label="Medium", value="medium"),
            discord.SelectOption(label="Hard", value="hard"),
            discord.SelectOption(label="Expert", value="expert"),
        ],
        placeholder="Choose which categories to remove.",
        min_values=1,
        max_values=5,
    )
    async def callback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.category = select.values
