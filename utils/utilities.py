from typing import List, NoReturn

import discord


async def delete_messages(cache: List) -> NoReturn:
    while len(cache):
        try:
            await cache[0].delete()
            del cache[0]
        except discord.HTTPException:
            pass


def star_emoji(stars):
    if 10 > stars >= 0:
        return "<:upper:787788134620332063>"
    elif 15 > stars >= 10:
        return "<:ds2:873791529876082758>"
    elif 20 > stars >= 15:
        return "<:ds3:873791529926414336>"
    else:
        return "<:ds4:873791530018701312>"
