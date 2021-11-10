import sys
from logging import getLogger
import os

from PIL import Image, ImageDraw, ImageFont
import io



class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

search = dotdict({"rank": {"ta": "Grandmaster", "mc": "Diamond", "hc": "Gold", "bo": "Unranked"}})
user = dotdict({"name": "mebula", "discriminator": 6662, "id": 123123123})
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
d.rounded_rectangle(inner_box, radius=20, fill=(31, 34, 37, 255))
with io.BytesIO() as avatar_binary:
    #await user.avatar.save(fp=avatar_binary)
    avatar = Image.open("data/test.png")
    avatar.thumbnail((200, 200))
    av_mask = Image.new("L", avatar.size, 0)
    draw = ImageDraw.Draw(av_mask)
    draw.ellipse((0, 0, 200, 200), fill=255)
    a_height = avatar.size[1]
    img.paste(avatar, (x_offset * 4, (y - a_height)//2), av_mask)
x_name = 200 + x_offset * 7

# Rank boxes
box_start = x_name + x_offset + 30
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

# Username/Discriminator
name_font = ImageFont.truetype("data/futura.ttf", 50)
disc_font = ImageFont.truetype("data/futura.ttf", 25)
name = d.text((x_name, 175), user.name[:12], fill=(255, 255, 255), font=name_font)
x_disc = x_name + d.textlength(user.name[:12], font=name_font) + x_offset

d.text((x_disc, 198), f"#{user.discriminator}", fill=(255, 255, 255), font=disc_font)

# XP
xp_start = 650
xp_font = ImageFont.truetype("data/futura.ttf", 30)
xp_length = xp_start + d.textlength("Total XP:", font=xp_font) + 10
xp_title = d.text((xp_start, 195), "Total XP:", fill=(255, 255, 255), font=xp_font)
xp_amt = d.text((xp_length, 195), "111.1k", fill=(255, 255, 255), font=xp_font)

# Highest Position
xp_circle_r_pad = 100
xp_circle_dia = 160
xp_circle_centered = bo_box_x2 + (x - bo_box_x2) // 2 - xp_circle_dia // 2

color = ()
place = 0
#all_users = await ExperiencePoints().find({}, sort=[("xp", -1)]).to_list(None)
# for i, u in enumerate(all_users):
    # if u.user_id == user.id:
    #     place = i + 1
place = 1
if place == 1:
    color = (255, 215, 0, 200)
elif place == 2:
    color = (192, 192, 192, 255)
elif place == 3:
    color = (160, 82, 45, 255)
else:
    color = (9, 10, 11, 255)



# (x - (x_offset * 4), (y - 200)//2)

place_circle_x1 = x - (x_offset * 4) - 200
place_circle_x2 = x - (x_offset * 4)
place_circle_y1 = (y - 200)//2
place_circle_y2 = (y - 200)//2 + 200

d.ellipse((x - (x_offset * 4) - 200, (y - 200)//2, x - (x_offset * 4), (y - 200)//2 + 200), fill=color)
place_font = ImageFont.truetype("data/futura.ttf", 120)
if len(str(place)) >= 2:
    place_font = ImageFont.truetype("data/futura.ttf", 90)

place_length = d.textlength(str(place), font=place_font)
place_offset = place_circle_x1 + (place_circle_x2 - place_circle_x1) // 2 - place_length // 2

ascent, descent = place_font.getmetrics()
(width, baseline), (offset_x, offset_y) = place_font.font.getsize(str(place))

place_h_offset = place_circle_y1 + (place_circle_y2 - place_circle_y1) // 2 - (ascent - offset_y)

number_offset = 0
if len(str(place)) == 2:
    number_offset = 3
elif len(str(place)) == 3:
    number_offset = 5

d.text((place_offset - number_offset, place_h_offset + 13), str(place), fill=(255, 255, 255, 255), font=place_font)

img.show()