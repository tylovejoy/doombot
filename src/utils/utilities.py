from typing import List, NoReturn

import discord


async def delete_messages(cache: List) -> NoReturn:
    while len(cache):
        try:
            await cache[0].delete()
            del cache[0]
        except discord.HTTPException:
            pass
