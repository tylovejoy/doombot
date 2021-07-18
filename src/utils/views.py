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

    @discord.ui.button(
        label="Verify", style=discord.ButtonStyle.green, custom_id="verify"
    )
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
            discord.SelectOption(label="Time Attack", value="0"),
            discord.SelectOption(label="Mildcore", value="1"),
            discord.SelectOption(label="Hardcore", value="2"),
            discord.SelectOption(label="Bonus", value="3"),
            discord.SelectOption(label="All", value="4"),
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
            discord.SelectOption(label="Time Attack", value="0"),
            discord.SelectOption(label="Mildcore", value="1"),
            discord.SelectOption(label="Hardcore", value="2"),
            discord.SelectOption(label="Bonus", value="3"),
        ],
    )
    async def callback(
        self, select: discord.ui.select, interaction: discord.Interaction
    ):
        self.value = int(select.values[0])
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
