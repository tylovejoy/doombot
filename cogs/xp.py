import sys
from logging import getLogger
import os
import discord
from PIL import Image, ImageDraw, ImageFont
import io
from discord.ext import commands

from internal.database import ExperiencePoints

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


class XP(commands.Cog, name="XP"):
    """XP"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if commands are used in rank channel."""
        if (
            ctx.channel.id
            in (
                constants_bot.RANK_CHANNEL_ID,
                constants_bot.RANK_CHANNEL_ID,
            )
            or (ctx.guild is None)
        ):
            return True

    @commands.command(
        name="rank",
    )
    async def _create_rank_card(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        if user is None:
            user = ctx.author

        search = await ExperiencePoints().find_one({"user_id": user.id})

        logo_fp = {
            "Unranked": "data/unranked_rank.png",
            "Gold": "data/gold_rank.png",
            "Diamond": "data/diamond_rank.png",
            "Grandmaster": "data/grandmaster_rank.png"
        }

        logo = Image.open(logo_fp[search.rank])
        rank_logo_offset = 0
        if search.rank == "Unranked":
            logo.thumbnail((105, 105))
            rank_logo_offset = 8
        elif search.rank == "Gold":
            logo.thumbnail((100, 100))
            rank_logo_offset = 11
        elif search.rank == "Diamond":
            logo.thumbnail((130, 130))
        elif search.rank == "Grandmaster":
            logo.thumbnail((140, 140))

        x = 934
        y = 282

        y_offset = 10
        x_offset = 10

        inner_box = (x_offset, y_offset, x - x_offset, y - y_offset)

        img = Image.new("RGBA", (x, y), color=(0, 0, 0, 0))

        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle(inner_box, radius=20, fill=(9, 10, 11, 127))
        with io.BytesIO() as avatar_binary:
            await user.avatar.save(fp=avatar_binary)
            avatar = Image.open(avatar_binary)
            avatar.thumbnail((200, 200))
            av_mask = Image.new("L", avatar.size, 0)
            draw = ImageDraw.Draw(av_mask)
            draw.ellipse((0, 0, 200, 200), fill=255)
            a_height = avatar.size[1]
            img.paste(avatar, (x_offset * 4, (y - a_height)//2), av_mask)
        x_name = 200 + x_offset * 7

        img.paste(logo, (x_name + x_offset * 3 + rank_logo_offset, 50), logo)

        name_font = ImageFont.truetype("data/futura.ttf", 50)
        disc_font = ImageFont.truetype("data/futura.ttf", 25)

        name = d.text((x_name, 175), user.name[:12], fill=(255, 255, 255), font=name_font)
        x_disc = x_name + d.textlength(user.name[:12], font=name_font) + x_offset

        d.text((x_disc, 198), f"#{user.discriminator}", fill=(255, 255, 255), font=disc_font)

        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename="rank_card.png"))


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(XP(bot))
