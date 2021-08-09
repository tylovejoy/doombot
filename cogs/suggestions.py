import sys
from logging import getLogger
from typing import Optional

import discord
from discord.ext import commands

from internal.database import SuggestionStars
from utils.utilities import star_emoji

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


class Suggestions(commands.Cog, name="Suggestions"):
    """Starboard"""

    def __init__(self, bot):
        self.bot = bot
        self.suggestion_channel = self.bot.get_channel(
            constants_bot.SUGGESTIONS_CHANNEL_ID
        )
        self.starboard_channel = self.bot.get_channel(
            constants_bot.SUGGESTIONS_STARBOARD_ID
        )

    @commands.Cog.listener(name="on_message")
    async def add_react_suggestion(self, message: discord.Message):
        if message.channel.id != constants_bot.SUGGESTIONS_CHANNEL_ID:
            return
        await message.add_reaction(emoji="<:upper:787788134620332063>")

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def suggestion_reactions(
        self, payload: discord.RawReactionActionEvent
    ) -> Optional[None]:
        if payload.user_id == constants_bot.BOT_ID:
            return
        if payload.channel_id != constants_bot.SUGGESTIONS_CHANNEL_ID:
            return
        if payload.emoji != discord.PartialEmoji.from_str(
            "<:upper:787788134620332063>"
        ):
            return

        entry: SuggestionStars = await SuggestionStars.search(payload.message_id)
        if entry is None:
            entry = SuggestionStars(
                **{
                    "message_id": payload.message_id,
                    "stars": 0,
                    "jump": f"https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}",
                    "starboard_id": 0,
                    "reacted": [],
                }
            )
        elif payload.user_id in entry.reacted:
            return

        entry.stars += 1
        entry.reacted = entry.reacted + [payload.user_id]
        await entry.commit()
        if entry.stars < 6:
            return

        message: discord.Message = await self.suggestion_channel.get_partial_message(
            payload.message_id
        ).fetch()
        logger.info(message)
        if entry.starboard_id == 0:
            embed = discord.Embed(
                description=message.content,
                color=0xF7BD00,
            )
            embed.set_author(
                name=message.author.name, icon_url=message.author.avatar.url
            )
            embed.add_field(name="Original", value=f"[Jump!]({entry.jump})")
            starboard_message: discord.Message = await self.starboard_channel.send(
                f"{star_emoji(entry.stars)} **{entry.stars}**",
                embed=embed,
            )
            entry.starboard_id = starboard_message.id
            await entry.commit()
            await starboard_message.start_thread(
                name=message.content[:100], auto_archive_duration=1440
            )

        else:
            starboard_message = self.starboard_channel.get_partial_message(
                entry.starboard_id
            )
            await starboard_message.edit(
                content=f"{star_emoji(entry.stars)} **{entry.stars}**"
            )


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Suggestions(bot))
