import asyncio
from logging import getLogger
from typing import Any, Callable, List, NoReturn, Optional, Union

from discord.ext import commands

from utils.embeds import doom_embed
from utils.utilities import delete_messages

logger = getLogger(__name__)


class FormResponse:
    """@DynamicAttrs"""

    def __init__(self, data: List) -> None:
        data = dict((key, d[key]) for d in data for key in d)
        for d in data.keys():
            if isinstance(data[d], dict):
                setattr(self, d, data[d]["response"])
            else:
                setattr(self, d, data[d])


class Form:
    def __init__(self, ctx: commands.Context, title: str, timeout=120):
        self._ctx = ctx
        self._bot = ctx.bot
        self._questions = []
        self._message_cache = []
        self.title = title
        self.timeout = timeout

    def add_question(
        self,
        question: str,
        key: str,
        validation: Optional[Callable[[Any], bool]] = None,
    ) -> NoReturn:
        questions = {"question": question, "response": None}
        if validation:
            questions["validation"] = validation
        questions = {key: questions}
        self._questions.append(questions)

    async def execute(
        self, channel: commands.Context.channel = None
    ) -> Union[FormResponse, None]:
        if channel is None:
            channel = self._ctx.channel

        q_list = []

        for idx, question in enumerate(self._questions):

            embed = doom_embed(
                title=f"{self._ctx.author}'s Form Submission",
                desc=question[list(question.keys())[0]]["question"],
            )
            embed.set_author(name=f"{self.title}: {idx + 1}/{len(self._questions)}")
            q_list.append([embed, question])

        for embed, question in q_list:
            prompt = await channel.send(embed=embed)
            self._message_cache.append(prompt)

            def check(m):
                return m.channel == prompt.channel and m.author == self._ctx.author

            response_msg = await self._bot.wait_for(
                "message",
                check=check,
                timeout=self.timeout,
            )
            if response_msg is None:
                break
            self._message_cache.append(response_msg)
            response = response_msg.content

            if response.lower() in ["cancel", "stop", "quit"]:
                await delete_messages(self._message_cache)
                return None

            q = question[list(question.keys())[0]]
            if "validation" in q.keys():
                while True:
                    if q["validation"](response):
                        q["response"] = response
                        break
                    else:
                        retry_msg = await channel.send(
                            f"That is not valid. Try again.",
                        )
                        self._message_cache.append(retry_msg)
                        msg = await self._bot.wait_for(
                            "message", check=check, timeout=self.timeout
                        )
                        response = msg.content
                        self._message_cache.append(msg)
            else:
                q["response"] = response
            await delete_messages(self._message_cache)
        return FormResponse(self._questions)
