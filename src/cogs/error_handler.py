"""
Copyright ©️: 2020 Seniatical / _-*™#7519
License: Apache 2.0
A permissive license whose main conditions require preservation of copyright and license notices.
Contributors provide an express grant of patent rights.
Licensed works, modifications, and larger works may be distributed under different terms and without source code.
FULL LICENSE CAN BE FOUND AT:
    https://www.apache.org/licenses/LICENSE-2.0.html
Any violation to the license, will result in moderate action
You are legally required to mention (original author, license, source and any changes made)
"""
import asyncio
import io
import traceback
from inspect import Parameter

import discord
from discord.ext import commands

_errors = (
    "ArithmeticError",
    "AssertionError",
    "BaseException",
    "BlockingIOError",
    "BrokenPipeError",
    "BufferError",
    "BytesWarning",
    "ChildProcessError",
    "ConnectionAbortedError",
    "ConnectionError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "DeprecationWarning",
    "EOFError",
    "EnvironmentError",
    "FileExistsError",
    "FileNotFoundError",
    "FloatingPointError",
    "FutureWarning",
    "GeneratorExit",
    "IOError",
    "ImportError",
    "ImportWarning",
    "UnexpectedQuoteError",
    "IndentationError",
    "IndexError",
    "InterruptedError",
    "IsADirectoryError",
    "KeyError",
    "KeyboardInterrupt",
    "LookupError",
    "MemoryError",
    "ModuleNotFoundError",
    "NameError",
    "NotADirectoryError",
    "NotImplemented",
    "NotImplementedError",
    "OSError",
    "OverflowError",
    "PendingDeprecationWarning",
    "PermissionError",
    "ProcessLookupError",
    "RecursionError",
    "ReferenceError",
    "ResourceWarning",
    "RuntimeError",
    "RuntimeWarning",
    "StopAsyncIteration",
    "StopIteration",
    "SyntaxError",
    "SyntaxWarning",
    "SystemError",
    "SystemExit",
    "TabError",
    "TimeoutError",
    "True",
    "TypeError",
    "UnboundLocalError",
    "UnicodeDecodeError",
    "UnicodeEncodeError",
    "UnicodeError",
    "UnicodeTranslateError",
    "UnicodeWarning",
    "UserWarning",
    "ValueError",
    "Warning",
    "WindowsError",
    "ZeroDivisionError",
)


async def convert(time):
    days = time // (24 * 3600)
    time = time % (24 * 3600)
    hours = time // 3600
    time %= 3600
    minutes = time // 60
    time %= 60
    seconds = time
    if days:
        if hours:
            return f"**{days}** Days and **{hours}** Hours."
        if minutes:
            return f"**{days}** Days and **{minutes}** Minutes."
        return f"**{days}** Days."
    if hours:
        if minutes:
            return f"**{hours}** Hours and **{minutes}** Minutes."
        return f"**{hours}** Hours and **{seconds}** Seconds."
    if minutes:
        if seconds:
            return f"**{minutes}** Minutes and **{seconds}** Seconds."
        return f"**{minutes}** Minutes."
    return f"**{seconds}** Seconds."


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):  # noqa: C901
        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.CommandOnCooldown):
            time = error.retry_after
            time = await convert(round(time))
            message = f"The command **{ctx.command.name}** is on cooldown for {time}"
            return await ctx.message.reply(
                embed=discord.Embed(
                    description=f"<a:ChumpyNo:866364385554464768> {message}",
                    colour=discord.Colour.red(),
                ).set_footer(
                    text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
                ),
                mention_author=False,
                delete_after=15,
            )

        elif isinstance(error, commands.DisabledCommand):
            if not ctx.command.enabled:
                return await ctx.message.reply(
                    embed=discord.Embed(
                        description="<a:ChumpyNo:866364385554464768> This command has been disabled by one of our owners - Most likely due to a bug.",
                        colour=discord.Colour.red(),
                    ).set_footer(
                        text="Invoked by {}".format(ctx.author),
                        icon_url=ctx.author.avatar,
                    ),
                    mention_author=False,
                    delete_after=15,
                )

            return await ctx.message.reply(
                embed=discord.Embed(
                    description="<a:ChumpyNo:866364385554464768> This command has been disabled. Re-enable it use it again!",
                    colour=discord.Colour.red(),
                ).set_footer(
                    text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
                ),
                mention_author=False,
                delete_after=15,
            )

        elif isinstance(error, commands.MissingRequiredArgument):
            ctx.command.reset_cooldown(ctx)
            prefix_ = ctx.prefix if not ctx.prefix == f"<@!{ctx.bot.user.id}>" else "-"

            params = [ctx.command.clean_params[i] for i in ctx.command.clean_params]
            listed_message = ["```{}{} ".format(prefix_, ctx.command.name), "```"]
            for param in params:
                if param.default == Parameter.empty:
                    listed_message.insert(-1, "<" + param.name + "> ")
                else:
                    listed_message.insert(
                        -1, "[" + param.name + "={}] ".format(param.default)
                    )

            listed_message.insert(-1, "\n" + error.args[0])

            missing = error.param
            try:
                index = listed_message.index("<" + missing.name + "> ", 0)
            except ValueError:
                index = listed_message.index("[" + missing.name + "] ", 0)

            listed_message.insert(-2, "\n")
            for i in range(index):
                listed_message.insert(-2, (" " * (len(listed_message[index - 1]) - 3)))
            listed_message.insert(-2, "^" * len("<" + missing.name + ">"))
            embed = discord.Embed(
                description="".join(listed_message), colour=discord.Colour.red()
            ).set_footer(
                text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
            )
            await ctx.send(embed=embed, delete_after=15)

        elif isinstance(error, commands.errors.NSFWChannelRequired):
            embed = discord.Embed(
                title="Error 404!",
                colour=discord.Color.red(),
                description="You must use this command in a channel marked as **NSFW**.",
                timestamp=ctx.message.created_at,
            ).set_footer(
                text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
            )
            embed.set_image(url="https://i.imgur.com/cy9t3XN.gif")
            await ctx.message.reply(embed=embed, delete_after=15)

        elif isinstance(error, commands.errors.NotOwner):
            await ctx.message.reply(
                "Only **nebula#6669** can use this command.",
                mention_author=False,
                delete_after=15,
            )

        elif isinstance(error, commands.errors.MemberNotFound):
            await ctx.message.reply(
                embed=discord.Embed(
                    description=f"<a:ChumpyNo:866364385554464768> Member named **{error.argument}** was not found!",
                    colour=discord.Colour.red(),
                ).set_footer(
                    text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
                ),
                mention_author=False,
                delete_after=15,
            )
            ctx.command.reset_cooldown(ctx)

        elif isinstance(error, commands.errors.UserNotFound):
            await ctx.message.reply(
                embed=discord.Embed(
                    description=f"<a:ChumpyNo:866364385554464768> Member named **{error.argument}** was not found!",
                    colour=discord.Colour.red(),
                ).set_footer(
                    text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
                ),
                mention_author=False,
                delete_after=15,
            )
            ctx.command.reset_cooldown(ctx)

        elif isinstance(error, commands.errors.ChannelNotFound):
            ctx.command.reset_cooldown(ctx)
            await ctx.message.reply(
                embed=discord.Embed(
                    description="<a:ChumpyNo:866364385554464768> Channel named **{}** cannot be found! Retry with a valid channel.".format(
                        error.argument
                    ),
                    colour=discord.Colour.red(),
                ).set_footer(
                    text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
                ),
                mention_author=False,
                delete_after=15,
            )

        elif isinstance(error, commands.errors.RoleNotFound):
            ctx.command.reset_cooldown(ctx)
            await ctx.message.reply(
                embed=discord.Embed(
                    description="<a:ChumpyNo:866364385554464768> Role named **{}** cannot be found!".format(
                        error.argument
                    ),
                    colour=discord.Colour.red(),
                ).set_footer(
                    text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
                ),
                mention_author=False,
                delete_after=15,
            )

        elif isinstance(error, commands.errors.CheckFailure):
            ctx.command.reset_cooldown(ctx)
            await ctx.message.reply(
                embed=discord.Embed(
                    description="<a:ChumpyNo:866364385554464768> Either you don't have permission to use this or you're in the wrong channel!",
                    colour=discord.Colour.red(),
                ).set_footer(
                    text="Invoked by {}".format(ctx.author), icon_url=ctx.author.avatar
                ),
                mention_author=False,
                delete_after=15,
            )

        else:
            if ctx.command.name.lower() == "eval_fn":
                return

            error = traceback.format_exception(
                etype=type(error), value=error, tb=error.__traceback__
            )
            error = "".join(error)

            if error.endswith("Missing Permissions"):
                try:
                    return await ctx.send(
                        "I am missing permissions inorder to run this command. I cannot identify the correct one.",
                        delete_after=15,
                    )
                except discord.errors.Forbidden:
                    return

            channel = self.bot.get_channel(849878847310528523)
            if len(error) < 1850:
                await channel.send(
                    "**Error in the command {}**, Located from `{}` by user `{}`\n```\n".format(
                        ctx.command.qualified_name,
                        ctx.guild.name,
                        ctx.author,
                    )
                    + error
                    + "\n```"
                )
            else:
                await channel.send(
                    content="**Error in the command {}**, Located from `{}` by user `{}`\n".format(
                        ctx.command.qualified_name, ctx.guild.name, ctx.author
                    )
                    + "\n",
                    file=discord.File(
                        fp=io.BytesIO(error.encode(errors="ignore")),
                        filename="error.log",
                    ),
                )

            try:
                await ctx.send(
                    "**An unknown error has occurred. It has been reported automatically!",
                    delete_after=10,
                )
            except discord.errors.Forbidden:
                pass

        try:
            await asyncio.sleep(10)
            await ctx.message.delete()
        except discord.HTTPException:
            pass


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
