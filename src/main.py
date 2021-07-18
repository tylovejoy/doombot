import asyncio
import json
import logging
import os

import internal.database_init
from internal.bot import Bot

logger = logging.getLogger()
logger.setLevel(logging.INFO)

consoleHandle = logging.StreamHandler()
consoleHandle.setLevel(logging.INFO)
consoleHandle.setFormatter(
    logging.Formatter("%(name)-18s :: %(levelname)-8s :: %(message)s")
)
logger.addHandler(consoleHandle)


def load_config():
    """Load config and .env file."""
    from os.path import dirname, join

    from dotenv import load_dotenv

    # Create .env file path.
    dotenv_path = join("..", ".env")

    # Load file from the path.
    load_dotenv(dotenv_path)

    with open("data/config.json", "r", encoding="utf-8-sig") as doc:
        return json.load(doc)


async def run():
    """Where the bot gets started.
    If you wanted to create an database connection pool
    or other session for the bot to use,
    it's recommended that you create it here and pass it to the bot as a kwarg.
    """

    def get_config_var(env_name, config_path, config_name, **kwargs):
        """Attempt to get a variable from the env file.
        If no env variable, from the config key, and finally,
        if none found, return the fallback value.
        """
        v = os.getenv(env_name, config_path.get(config_name, kwargs.get("fallback")))

        if v is None and kwargs.get("error", False):
            raise KeyError(
                f"Failed to get configuration key. Env name: {env_name}, Config name: {config_name}"
            )

        return v

    config = load_config()

    internal.database_init.init(
        get_config_var(
            "MONGO_CONNECTION_STRING", config, "mongoConnectionString", error=True
        ),
        get_config_var(
            "MONGO_DATABASE_NAME",
            config,
            "mongoDbName",
            fallback="dpytemplate_default_db",
        ),
    )

    bot = Bot(
        config=config,
        prefix=config["prefix"],
        description=config["description"],
        case_insensitive=config["case_insensitive"],
    )

    bot.config = config
    token = get_config_var("BOT_TOKEN", config, "token", error=True)
    await bot.start(token)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
