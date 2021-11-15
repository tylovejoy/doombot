import math
import sys
from logging import getLogger
import os
import discord
from PIL import Image, ImageDraw, ImageFont
import io
from discord.ext import commands
from utils.embeds import doom_embed
from internal.database import ExperiencePoints

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot

logger = getLogger(__name__)


def format_xp(xp):
    if xp > 999:
        xp = str(float(xp)/1000)[:-2] + "k"
    return str(xp)


def find_level(player_xp):
    total = 0
    for level in range(101):
        total += (5 * (level ** 2) + (50 * level) + 100)
        if total > player_xp:
            return level


def find_portrait(level) -> str:
    number = str(math.ceil(level % 20 / 4) + 1)
    if level <= 20:
        filename = "bronze" + number + ".png"
    elif 20 <= level < 40:
        filename = "silver" + number + ".png"
    elif 40 <= level < 60:
        filename = "gold" + number + ".png"
    elif 60 <= level < 80:
        filename = "platinum" + number + ".png"
    elif 80 <= level < 100:
        filename = "diamond" + number + ".png"
    else:
        filename = "diamond5.png"
    return filename


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
    async def _rank_card(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        if user is None:
            user = ctx.author
        search = await ExperiencePoints().find_one({"user_id": user.id})
        if not search:
            search = self._create_db_entry(ctx.author.id)

        name = user.name[10:] + "#" + user.discriminator
        if search.alias:
            name = search.alias

        logo_fp = {
            "Unranked": "data/ranks/bronze.png",
            "Gold": "data/ranks/gold.png",
            "Diamond": "data/ranks/diamond.png",
            "Grandmaster": "data/ranks/grandmaster.png"
        }

        ta_logo = Image.open(logo_fp[search.rank["ta"]]).convert("RGBA")
        mc_logo = Image.open(logo_fp[search.rank["mc"]]).convert("RGBA")
        hc_logo = Image.open(logo_fp[search.rank["hc"]]).convert("RGBA")
        bo_logo = Image.open(logo_fp[search.rank["bo"]]).convert("RGBA")

        ta_logo.thumbnail((100, 100))
        mc_logo.thumbnail((100, 100))
        hc_logo.thumbnail((100, 100))
        bo_logo.thumbnail((100, 100))
        old_x = 15
        old_y = 66
        x = 1165
        y = 348
        y_offset = 10
        x_offset = 10
        inner_box = (0, 0, x, y)

        img = Image.new("RGBA", (x, y), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        rank_card = Image.open("data/rankcard_bg.png").convert("RGBA")
        img.paste(rank_card)

        with io.BytesIO() as avatar_binary:
            await user.avatar.save(fp=avatar_binary)
            avatar = Image.open(avatar_binary).convert("RGBA")
            avatar.thumbnail((200, 200))
            av_mask = Image.new("L", avatar.size, 0)
            draw = ImageDraw.Draw(av_mask)
            draw.ellipse((0, 0, 200, 200), fill=255)
            a_height = avatar.size[1]
            img.paste(avatar, (x_offset * 4 + old_x, (y - a_height)//2), av_mask)

        # Portrait PFP
        level = find_level(search.xp)
        portrait_file = find_portrait(level)
        portrait = Image.open("data/portraits/" + portrait_file).convert("RGBA")
        img.paste(portrait, (-60, -30), portrait)


        rank_x_offset = 50
        rank_y_offset = 37
        ta_box_xy = (375 + old_x - rank_x_offset, 98 + old_y//2 - rank_y_offset)
        mc_box_xy = (508 + old_x - rank_x_offset, 98 + old_y//2 - rank_y_offset)
        hc_box_xy = (641 + old_x - rank_x_offset, 98 + old_y//2 - rank_y_offset)
        bo_box_xy = (774 + old_x - rank_x_offset, 98 + old_y//2 - rank_y_offset)

        img.paste(ta_logo, ta_box_xy, ta_logo)
        img.paste(mc_logo, mc_box_xy, mc_logo)
        img.paste(hc_logo, hc_box_xy, hc_logo)
        img.paste(bo_logo, bo_box_xy, bo_logo)

        # Username/Discriminator
        name_font = ImageFont.truetype("data/fonts/segoeui.ttf", 50)
        name_pos = x // 2 - d.textlength(name, font=name_font) // 2 + old_x
        d.text((name_pos, 155 + old_y//2), name, fill=(255, 255, 255), font=name_font)

        # XP
        xp_font = ImageFont.truetype("data/fonts/segoeui.ttf", 40)
        xp = format_xp(search.xp)
        xp_length = x // 2 - d.textlength(f"Total XP: {xp}", font=xp_font) // 2 + old_x
        d.text((xp_length, 215 + old_y//2), f"Total XP: {xp}", fill=(255, 255, 255), font=xp_font)

        # Highest Position
        xp_circle_r_pad = 100
        xp_circle_dia = 160

        place = 0
        all_users = await ExperiencePoints().find({}, sort=[("xp", -1)]).to_list(None)
        for i, u in enumerate(all_users):
            if u.user_id == user.id:
                place = i + 1
        if place == 1:
            pos_portrait_f = "gold_position.png"
        elif place == 2:
            pos_portrait_f = "silver_position.png"
        elif place == 3:
            pos_portrait_f = "bronze_position.png"
        else:
            pos_portrait_f = "no_position.png"

        color = (9, 10, 11, 255)

        place_circle_x1 = x - (x_offset * 4) - 200
        place_circle_x2 = x - (x_offset * 4)
        place_circle_y1 = (y - 200) // 2
        place_circle_y2 = (y - 200) // 2 + 200

        d.ellipse((place_circle_x1, place_circle_y1, place_circle_x2, place_circle_y2), fill=color)

        if len(str(place)) == 1:
            place_font = ImageFont.truetype("data/fonts/segoeui.ttf", 120)
        elif len(str(place)) == 2:
            place_font = ImageFont.truetype("data/fonts/segoeui.ttf", 110)
        else:
            place_font = ImageFont.truetype("data/fonts/segoeui.ttf", 100)

        place_x = place_circle_x1 + (place_circle_x2 - place_circle_x1) // 2 - d.textlength(str(place), font=place_font) // 2

        ascent, descent = place_font.getmetrics()
        (width, baseline), (offset_x, offset_y) = place_font.font.getsize(str(place))

        place_y = y // 2 - (ascent - offset_y)

        d.text((place_x, place_y), str(place), fill=(255, 255, 255, 255),
               font=place_font)

        pos_portrait = Image.open("data/portraits/" + pos_portrait_f).convert("RGBA")
        img.paste(pos_portrait, (x - 350, -28), pos_portrait)

        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename="rank_card.png"))

    @commands.command(
        name="shop",
    )
    async def _shop(self, ctx):
        embed = doom_embed(
            title="The DoomBot Store", 
            desc="Select a category in the dropdown to browse!",
        )

    @commands.command(
        name="changerank",
    )
    async def _change_rank(self, ctx, user: discord.Member, category, rank):
        if not user:
            await ctx.send("User doesn't exist.", delete_after=10)
        t_cat = ["ta", "mc", "hc", "bo"]
        if category not in t_cat:
            await ctx.send(f"Category must be \"{', '.join(t_cat)}\"", delete_after=10)
        ranks = ["unranked", "gold", "diamond", "grandmaster"]
        if rank.lower() not in ranks:
            await ctx.send(f"Rank must be \"{', '.join(ranks)}\"", delete_after=10)
        
        search = await ExperiencePoints().find_one({"user_id": user.id})

        if not search:
            search = self._create_db_entry(ctx.author.id)
        
        search.rank[category] = rank.capitalize()
        await search.commit()

    @commands.command(
        name="setname",
    )
    async def _set_display_name(self, ctx, name):
        search = await ExperiencePoints().find_one({"user_id": ctx.author.id})
        if not search:
            search = self._create_db_entry(ctx.author.id)
        
        search.alias = name
        await search.commit()
        await ctx.send(f"Display name has ben set to \"{name}\"", delete_after=10)


    async def _create_db_entry(self, user_id):
        search = ExperiencePoints(**{
            "user_id": user_id,
            "rank": {
                "ta": "Unranked",
                "mc": "Unranked",
                "hc": "Unranked",
                "bo": "Unranked",
            },
            "xp_avg": {
                "ta": [None, None, None, None, None],
                "mc": [None, None, None, None, None],
                "hc": [None, None, None, None, None],
                "bo": [None, None, None, None, None],
            },
            "xp": 0,
            "coins": 0,
        })
        await search.commit()
        return search


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(XP(bot))
