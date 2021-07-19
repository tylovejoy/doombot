import datetime

import dateparser
from discord.ext import wizards

from internal.database import Schedule


class TournamentWizard(wizards.Wizard):
    """EmbedWizard"""

    def __init__(self):
        self.result = {}
        super().__init__(cleanup_after=True, timeout=30.0)

        self.schedule = Schedule()

    # register an action, so users can type "stop" or "cancel" to stop
    # the wizard
    @wizards.action("stop", "cancel")
    async def cancel_wizard(self, message):
        await self.send("Wizard Cancelled.")
        await self.stop(wizards.StopReason.CANCELLED)

    @wizards.step(
        "What should the title be? (Type `stop` or `cancel` to end at any time.)",
        position=1,
    )
    async def embed_title(self, message):
        self.result["title"] = message.content
        self.schedule.title = message.content

    @wizards.step(
        "What should the description be? (Type `stop` or `cancel` to end at any time.)",
        timeout=180.0,  # override the default timeout of 30
        position=2,
    )
    async def embed_description(self, message):
        length = len(message.content)
        if length > 2000:
            await self.send(
                f"That description is {length} chars, but the maximum is 2000."
            )
            return await self.do_step(self.embed_description)  # redo the step
        self.result["description"] = message.content

    @wizards.step(
        "Do you want to schedule this tournament to start at a specific time? 1 for Yes, 2 for No.",
        position=3,
    )
    async def start_time(self, message):
        self.result.setdefault("start_time", None)
        self.result.setdefault("start_time_datetime", None)
        if message.content == "2":
            pass  # move on to the next step
        elif message.content == "1":
            start_time = await self.do_step(self.schedule_tournament)

            self.result["start_time"] = start_time
            start_time = dateparser.parse(
                start_time, settings={"PREFER_DATES_FROM": "future"}
            )

            self.schedule.start_time = start_time.isoformat()
            self.result["start_time_datetime"] = start_time
            self.result["start_time"] = message.content

    @wizards.step(
        "When should the tournament begin (time from now)? (Type `stop` or `cancel` to end at any time.)",
        call_internally=False,
    )
    async def schedule_tournament(self, message):
        return message.content

    @wizards.step("How long will the tournament/round last?", position=4)
    async def time_limit(self, message):
        self.result.setdefault("time_limit", None)
        start_time = self.result.get("start_time", None)

        final = dateparser.parse(
            message.content, settings={"PREFER_DATES_FROM": "future"}
        )

        final_date = final.isoformat()

        if start_time:
            delta = final - datetime.datetime.now()
            final_date = self.result["start_time_datetime"] + delta
            final_date = final_date.isoformat()

        self.schedule.schedule = final_date
        self.result["time_limit"] = message.content

    @wizards.step(
        "Type `1` to add a tournament category (or any additional field), or `2` to move on. (Type `stop` or `cancel` to end at any time.)",
        position=5,
    )
    async def embed_fields(self, message):
        self.result.setdefault("fields", [])
        if message.content == "2":
            pass  # move on to the next step
        elif message.content == "1":
            field_name = await self.do_step(self.embed_field_name)
            field_value = await self.do_step(self.embed_field_value)

            self.result["fields"].append((field_name, field_value))

            # repeat the step, so users can add multiple fields
            return await self.do_step(self.embed_fields)
        else:
            await self.send("Please choose `1` or `2`.")
            return await self.do_step(self.embed_fields)

    @wizards.step(
        "What is the tournament category (or additional field title)? This is used a map code section. (Type `stop` or `cancel` to end at any time.)",
        call_internally=False,
        timeout=180.0,
    )
    async def embed_field_name(self, message):
        return message.content

    @wizards.step(
        "List the map, map code, and creator (or additional field contents). (Type `stop` or `cancel` to end at any time.)",
        call_internally=False,
        timeout=180.0,
    )
    async def embed_field_value(self, message):
        return message.content

    @wizards.step(
        "Who should be mentioned? (Type `stop` or `cancel` to end at any time.)",
        position=6,
        timeout=60.0,
    )
    async def embed_mentions(self, message):
        self.result.setdefault("mentions", None)
        self.result["mentions"] = "".join([x for x in message.content])
        self.schedule.mentions = self.result["mentions"]
