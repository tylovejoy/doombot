import sys
from logging import getLogger
from typing import Optional

import discord
from discord.ext import commands

from internal.database import SuggestionStars

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


def star_emoji(stars):
    if 5 > stars >= 0:
        return "\N{WHITE MEDIUM STAR}"
    elif 10 > stars >= 5:
        return "\N{GLOWING STAR}"
    elif 25 > stars >= 10:
        return "\N{DIZZY SYMBOL}"
    else:
        return "\N{SPARKLES}"


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

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> Optional[None]:
        if payload.channel_id != self.suggestion_channel.id and payload.emoji != "⭐":
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

        if entry.stars < 4:
            return

        message: discord.Message = await self.suggestion_channel.get_partial_message(
            payload.message_id
        ).fetch()

        if entry.starboard_id == 0:
            embed = discord.Embed(
                description=(message.content),
                color=0xF7BD00,
            )
            user: discord.Member = self.bot.get_user(payload.user_id)
            embed.set_author(name=user.name, icon_url=user.avatar.url)
            embed.add_field(name="Original", value=f"[Jump!]({entry.jump})")
            starboard_message = await self.starboard_channel.send(
                f"{star_emoji(entry.stars)} **{entry.stars}** {message.channel.mention}",
                embed=embed,
            )
            entry.starboard_id = starboard_message.id
            await entry.commit()
        else:
            starboard_message = self.starboard_channel.get_partial_message(
                entry.starboard_id
            )
            await starboard_message.edit(
                content=f"{star_emoji(entry.stars)} **{entry.stars}** {message.channel.mention}"
            )


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Suggestions(bot))
