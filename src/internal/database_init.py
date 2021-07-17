from typing import Union

from motor.motor_asyncio import AsyncIOMotorClient
from umongo import Instance

instance: Union[Instance, None] = None


def init(dburl, dbname):
    """Initialize a database instance."""
    global instance

    client = AsyncIOMotorClient(dburl)

    instance = Instance(client[dbname])
