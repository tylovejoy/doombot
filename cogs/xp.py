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

        ta_logo = Image.open(logo_fp[search.rank["ta"]])
        mc_logo = Image.open(logo_fp[search.rank["mc"]])
        hc_logo = Image.open(logo_fp[search.rank["hc"]])
        bo_logo = Image.open(logo_fp[search.rank["bo"]])

        diamond_y_offset = 0
        ta_gold_x_offset = 0
        mc_gold_x_offset = 0
        hc_gold_x_offset = 0
        bo_gold_x_offset = 0
        ta_ur_x_offset = 0
        mc_ur_x_offset = 0
        hc_ur_x_offset = 0
        bo_ur_x_offset = 0
        if search.rank["ta"] == "Unranked":
            ta_logo.thumbnail((105, 105))
            ta_ur_x_offset = 8
        elif search.rank["ta"] == "Gold":
            ta_logo.thumbnail((90, 90))
            ta_gold_x_offset = 15
        elif search.rank["ta"] == "Diamond":
            ta_logo.thumbnail((115, 115))
        elif search.rank["ta"] == "Grandmaster":
            ta_logo.thumbnail((120, 120))

        if search.rank["mc"] == "Unranked":
            mc_logo.thumbnail((105, 105))
            mc_ur_x_offset = 8
        elif search.rank["mc"] == "Gold":
            mc_logo.thumbnail((90, 90))
            mc_gold_x_offset = 15
        elif search.rank["mc"] == "Diamond":
            mc_logo.thumbnail((115, 115))
        elif search.rank["mc"] == "Grandmaster":
            mc_logo.thumbnail((120, 120))

        if search.rank["hc"] == "Unranked":
            hc_logo.thumbnail((105, 105))
            hc_ur_x_offset = 8
        elif search.rank["hc"] == "Gold":
            hc_logo.thumbnail((90, 90))
            hc_gold_x_offset = 15
        elif search.rank["hc"] == "Diamond":
            hc_logo.thumbnail((115, 115))
        elif search.rank["hc"] == "Grandmaster":
            hc_logo.thumbnail((120, 120))

        if search.rank["bo"] == "Unranked":
            bo_logo.thumbnail((105, 105))
            bo_ur_x_offset = 8
        elif search.rank["bo"] == "Gold":
            bo_logo.thumbnail((90, 90))
            bo_gold_x_offset = 15
        elif search.rank["bo"] == "Diamond":
            bo_logo.thumbnail((115, 115))
        elif search.rank["bo"] == "Grandmaster":
            bo_logo.thumbnail((120, 120))

        x = 1150
        y = 282

        y_offset = 10
        x_offset = 10

        inner_box = (0, 0, x, y)

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

        # Rank boxes
        box_start = x_name + x_offset
        box_pad = 15
        box_size = 120

        ta_box_x1 = box_start
        ta_box_x2 = box_start + box_size
        ta_box = (ta_box_x1, 40, ta_box_x2, 40 + box_size)

        mc_box_x1 = box_start + box_pad + box_size
        mc_box_x2 = box_start + box_pad + box_size * 2
        mc_box = (mc_box_x1, 40, mc_box_x2, 40 + box_size)

        hc_box_x1 = box_start + box_pad * 2 + box_size * 2
        hc_box_x2 = box_start + box_pad * 2 + box_size * 3
        hc_box = (hc_box_x1, 40, hc_box_x2, 40 + box_size)

        bo_box_x1 = box_start + box_pad * 3 + box_size * 3
        bo_box_x2 = box_start + box_pad * 3 + box_size * 4
        bo_box = (bo_box_x1, 40, bo_box_x2, 40 + box_size)

        d.rounded_rectangle(ta_box, radius=20, fill=(9, 10, 11, 240))
        d.rounded_rectangle(mc_box, radius=20, fill=(9, 10, 11, 240))
        d.rounded_rectangle(hc_box, radius=20, fill=(9, 10, 11, 240))
        d.rounded_rectangle(bo_box, radius=20, fill=(9, 10, 11, 240))

        rank_font = ImageFont.truetype("data/futura.ttf", 35)

        ta_offset = ta_box_x1 + 60 - d.textlength("TA", font=rank_font)//2
        d.text((ta_offset, 20), "TA", fill=(255, 255, 255), font=rank_font)

        mc_offset = mc_box_x1 + 60 - d.textlength("MC", font=rank_font) // 2
        d.text((mc_offset, 20), "MC", fill=(255, 255, 255), font=rank_font)

        hc_offset = hc_box_x1 + 60 - d.textlength("HC", font=rank_font) // 2
        d.text((hc_offset, 20), "HC", fill=(255, 255, 255), font=rank_font)

        bo_offset = bo_box_x1 + 60 - d.textlength("BO", font=rank_font) // 2
        d.text((bo_offset, 20), "BO", fill=(255, 255, 255), font=rank_font)

        img.paste(ta_logo, (ta_box_x1 + ta_gold_x_offset + ta_ur_x_offset, 60), ta_logo)
        img.paste(mc_logo, (mc_box_x1 + mc_gold_x_offset + mc_ur_x_offset, 60), mc_logo)
        img.paste(hc_logo, (hc_box_x1 + hc_gold_x_offset + hc_ur_x_offset, 60), hc_logo)
        img.paste(bo_logo, (bo_box_x1 + bo_gold_x_offset + bo_ur_x_offset, 60), bo_logo)


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
