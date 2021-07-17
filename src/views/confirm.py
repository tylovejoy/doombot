import discord


class Confirm(discord.ui.View):
    def __init__(self, embed):
        super().__init__()
        self.value = None
        self.embed = embed

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "Submission accepted.", ephemeral=True, embed=self.embed
        )
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Submission rejected.", ephemeral=True, embed=self.embed
        )
        self.value = False
        self.stop()
