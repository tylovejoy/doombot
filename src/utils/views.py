from copy import deepcopy
from typing import List

import discord


class Confirm(discord.ui.View):
    def __init__(self, name):
        super().__init__()
        self.value = None
        self.name = name

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
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"{self.name} rejected.", ephemeral=True
        )
        self.value = False
        self.stop()


class Paginator(discord.ui.View):
    def __init__(self, embeds: [discord.Embed], message: discord.Message = None):
        super().__init__()
        self.pages = embeds
        self._curr_page = 0
        self.close = False

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

    @discord.ui.button(label="First", emoji="⏮")
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction):
        self._curr_page = 0
        await interaction.response.edit_message(
            embed=self.formatted_pages[0], view=self
        )

    @discord.ui.button(label="Back", emoji="◀")
    async def back(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self._curr_page == 0:
            self._curr_page = len(self.pages) - 1
        else:
            self._curr_page -= 1
        await interaction.response.edit_message(
            embed=self.formatted_pages[self._curr_page], view=self
        )

    @discord.ui.button(label="Next", emoji="▶")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self._curr_page == len(self.pages) - 1:
            self._curr_page = 0
        else:
            self._curr_page += 1
        await interaction.response.edit_message(
            embed=self.formatted_pages[self._curr_page], view=self
        )

    @discord.ui.button(label="Last", emoji="⏭")
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction):
        self._curr_page = len(self.pages) - 1
        await interaction.response.edit_message(
            embed=self.formatted_pages[-1], view=self
        )

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.close = True
        self.stop()
