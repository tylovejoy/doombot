import asyncio
import re
import sys

import discord
from aiostream import stream
from discord.ext import commands
from pymongo.collation import Collation

from internal.database import WorldRecords
from utils.embeds import doom_embed
from utils.form import Form
from utils.map_utils import map_code_regex
from utils.pb_utils import display_record, time_convert
from utils.views import Confirm, Verification

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


class SubmitPersonalBest(commands.Cog, name="Personal best submission/deletion"):
    """Commands to submit and delete personal bests."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if channel is RECORD_CHANNEL."""
        if (
            ctx.channel.id == constants_bot.RECORD_CHANNEL_ID
            or ctx.channel.id == constants_bot.HARDCORE_RECORD_CHANNEL_ID
        ):
            return True

    # Submit personal best records
    @commands.command(
        help=(
            "Submit personal bests. Upload a screenshot with this message for proof!\n"
            "Use this command without arguments for a simpler submission!\n"
            "Also updates a personal best if it is faster.\n\n"
            "<record> must be in HH:MM:SS.SS format! You can omit the hours or minutes.\n\n"
            "Use quotation marks around level names that have spaces.\n\n"
            "A list of previously submitted level names will appear on confirmation message."
        ),
        brief="Submit personal best",
    )
    async def submitpb(self, ctx, map_code=None, level=None, record=None):
        """Submit personal best to database."""

        if not ctx.message.attachments:
            await ctx.send(
                "Screenshot must be attached to your message.", delete_after=10
            )
            return

        if not any([map_code, level, record]):
            form = Form(ctx, "Personal Best Submission Wizard")

            form.add_question(
                question="What is the map code (Only letters A-Z and numbers 0-9 allowed)?",
                key="map_code",
                validation=map_code_regex,
            )
            form.add_question(
                question="What level is it?",
                key="level",
            )
            form.add_question(
                question="What is your personal best record (HH:MM:SS.ss format)?",
                key="record",
                validation=time_convert,
            )

            result = await form.execute()

            if result is None:
                await ctx.send("Personal best submission cancelled.")
                return

            map_code = result.map_code
            level = result.level
            record = result.record

        map_code = map_code.upper()
        level = level.upper()
        record_in_seconds = time_convert(record)

        # Find currently associated levels
        level_checker = {}
        async for entry in (
            WorldRecords.find({"code": map_code})
            .sort([("level", 1), ("record", 1)])
            .collation(Collation(locale="en_US", numericOrdering=True))
        ):
            if entry.level.upper() not in level_checker.keys():
                level_checker[entry.level.upper()] = None

        # init embed
        embed = doom_embed(title=f"New Submission - {ctx.author.name}")
        embed.add_field(
            name="Currently submitted level names:",
            value=f"{', '.join(level_checker) if level_checker else 'N/A'}",
        )

        # Finds document
        submission = await WorldRecords.find_one(
            {
                "code": map_code,
                "level": re.compile(f"^{re.escape(level)}$", re.IGNORECASE),
                "posted_by": ctx.author.id,
            }
        )

        # If document is found, verifies if submitted time is faster (if verified).
        if (
            submission
            and record_in_seconds >= submission.record
            and submission.verified is True
        ):
            await ctx.channel.send("Personal best needs to be faster to update.")
            return

        # Create new PB document, if none exists.
        if not submission:
            submission = WorldRecords(
                **dict(
                    code=map_code,
                    name=ctx.author.name,
                    record=record_in_seconds,
                    level=level,
                    posted_by=ctx.author.id,
                    message_id=ctx.message.id,
                    url=ctx.message.jump_url,
                    verified=False,
                )
            )

        # Verification embed for user.
        embed.add_field(
            name=f"{submission.name}",
            value=(
                f"> Code: {submission.code}\n"
                f"> Level: {submission.level.upper()}\n"
                f"> Record: {display_record(record_in_seconds)}\n"
            ),
            inline=False,
        )
        img = await ctx.message.attachments[0].to_file(use_cached=True)
        embed.set_image(url=f"attachment://{img.filename}")

        # Confirmation
        view = Confirm("Submission", ctx.message.author)
        msg = await ctx.send("Is this correct?", embed=embed, view=view, file=img)
        await view.wait()
        embed.remove_field(0)
        if view.value:
            channel = self.bot.get_channel(constants_bot.HIDDEN_VERIFICATION_CHANNEL)

            # Try to fetch hidden_msg.
            try:
                hidden_msg = await channel.fetch_message(submission.hidden_id)
                if hidden_msg:
                    await hidden_msg.delete()
            # If not found, HTTPException is thrown, safely ignore
            except discord.errors.HTTPException:
                pass
            finally:
                # await msg.edit(content="Submission accepted")

                # New hidden message
                hidden_msg = await channel.send(
                    f"{ctx.author.name} needs verification!\n{submission.code} - "
                    f"Level {submission.level} - "
                    f"{display_record(record_in_seconds)}\n"
                    f"{ctx.message.jump_url}"
                )

                # Update submission
                submission.record = record_in_seconds
                submission.message_id = msg.id
                submission.url = ctx.message.jump_url
                submission.name = ctx.author.name
                submission.verified = False
                submission.hidden_id = hidden_msg.id

                # Save document
                await submission.commit()

                # Find top 10 records and display submission's place in top 10.
                top_10 = (
                    WorldRecords.find(
                        {
                            "code": map_code,
                            "level": re.compile(f"^{re.escape(level)}$", re.IGNORECASE),
                        }
                    )
                    .sort("record", 1)
                    .limit(10)
                )
                en = stream.enumerate(top_10)
                async with en.stream() as streamer:
                    async for rank, entry in streamer:
                        if submission:
                            if entry.pk == submission.pk:
                                await ctx.channel.send(
                                    f"Your rank is {rank + 1} on the unverified scoreboard."
                                )

                verify = Verification(msg, self.bot)

                try:
                    await ctx.message.delete()
                except Exception:
                    pass
                await msg.edit(
                    content="Waiting to be verified...", embed=embed, view=verify
                )
                await verify.wait()

                if verify.verify:
                    await msg.edit(content="Verified.", view=verify)
                elif not verify.verify:
                    await msg.edit(content="Verification rejected", view=verify)
                else:
                    await msg.edit(content="Verification error", view=verify)

        elif not view.value:
            await msg.edit(
                content="Submission has not been accepted.",
                view=view,
                embed=embed,
                delete_after=15,
            )
            await ctx.message.delete()
        elif view.value is None:
            await msg.edit(
                content="Submission timed out! Submission has not been accepted.",
                view=view,
                embed=embed,
                delete_after=15,
            )
            await ctx.message.delete()

    # Delete pb
    @commands.command(
        help="Delete personal best record for a particular map code.\n<name> will default to your own.\nThis is only required for when a mod deletes another person's personal best.\nOnly original posters and mods can delete a personal best.",
        brief="Delete personal best record",
    )
    async def deletepb(self, ctx, map_code, level, name=""):
        """Delete personal best from database."""
        author = ctx.message.author
        await ctx.message.delete()
        map_code = map_code.upper()
        level = level.upper()

        # Searches for author PB if none provided
        if name == "":
            name = ctx.author.name
            name_id = ctx.author.id
            search = await WorldRecords.find_one(
                {
                    "code": map_code,
                    "level": re.compile(re.escape(level), re.IGNORECASE),
                    "$or": [{"posted_by": name_id}, {"name": name}],
                }
            )
        else:
            search = await WorldRecords.find_one(
                {
                    "code": map_code,
                    "level": re.compile(re.escape(level), re.IGNORECASE),
                    "name": name,
                }
            )

        if not search:
            m = await ctx.channel.send(
                "Provided arguments might not exist. Personal best deletion was unsuccesful."
            )
            await asyncio.sleep(10)
            await m.delete()
            return

        if search.posted_by != ctx.author.id:
            if not bool(
                any(
                    role.id in constants_bot.ROLE_WHITELIST for role in ctx.author.roles
                )
            ):
                m = await ctx.channel.send(
                    "You do not have sufficient permissions. Personal best was not deleted."
                )
                await asyncio.sleep(10)
                await m.delete()
                return

        embed = doom_embed(title="Personal Best Deletion")
        embed.add_field(
            name=f"Name: {search.name}",
            value=(
                f"> Code: {search.code}\n"
                f"> Level: {search.level.upper()}\n"
                f"> Record: {display_record(search.record)}\n"
            ),
            inline=False,
        )

        view = Confirm("Deletion", author)
        msg = await ctx.send("Do you want to delete this?", embed=embed, view=view)
        await view.wait()

        if view.value:
            await msg.edit(
                content="Personal best deleted succesfully.", delete_after=20
            )
            channel = self.bot.get_channel(constants_bot.HIDDEN_VERIFICATION_CHANNEL)

            # Try to fetch hidden_msg.
            try:
                hidden_msg = await channel.fetch_message(search.hidden_id)
                if hidden_msg:
                    await hidden_msg.delete()
            # If not found, HTTPException is thrown, safely ignore
            except discord.errors.HTTPException:
                pass
            finally:
                await search.delete()

        elif not view.value:
            await msg.edit(content="Personal best was not deleted.", delete_after=20)
        elif view.value is None:
            await msg.edit(
                content="Deletion timed out! Personal best has not been deleted.",
                delete_after=20,
            )


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(SubmitPersonalBest(bot))
