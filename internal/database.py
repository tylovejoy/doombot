from umongo import Document
from umongo.fields import (
    BooleanField,
    DateTimeField,
    DictField,
    FloatField,
    IntegerField,
    ListField,
    StringField,
    UrlField,
)

from internal.database_init import instance


@instance.register
class BonusData(Document):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    name = StringField(required=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "BonusData"


@instance.register
class HardcoreData(Document):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    name = StringField(required=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "HardcoreData"


@instance.register
class MapData(Document):
    """MapData database document."""

    code = StringField(required=True, unique=True)
    creator = StringField(required=True)
    map_name = StringField(required=True)
    posted_by = IntegerField(required=True)
    type = ListField(StringField(), required=True)
    desc = StringField()

    class Meta:
        """MongoDb database collection name."""

        collection_name = "MapData"


@instance.register
class Guides(Document):
    code = StringField(require=True)
    guide = ListField(UrlField(), required=False)
    guide_owner = ListField(IntegerField(), required=False)

    class Meta:
        collection_name = "Guides"


@instance.register
class MildcoreData(Document):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    name = StringField(required=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "MildcoreData"


@instance.register
class Schedule(Document):
    """MapData database document."""

    schedule = DateTimeField(required=True)
    mentions = StringField(required=True)

    title = StringField(required=True)

    start_time = DateTimeField(required=False)
    embed_dict = DictField(required=False)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "Schedule"


@instance.register
class TimeAttackData(Document):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    name = StringField(required=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "TimeAttackData"


@instance.register
class TournamentData(Document):
    """MapData database document."""

    tournament_id = IntegerField(required=True)
    signups_open = BooleanField(required=True)
    annoucement_id = IntegerField(required=True)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "TournamentData"


@instance.register
class WorldRecords(Document):
    """WorldRecords database document."""

    code = StringField(required=True)
    name = StringField(required=True)
    posted_by = IntegerField(required=True)
    message_id = IntegerField(required=True)
    url = StringField(required=True)
    level = StringField(required=True)
    record = FloatField(required=True)
    verified = BooleanField(require=True)
    hidden_id = IntegerField(required=True)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "WorldRecords"


@instance.register
class Stars(Document):
    """Starboard database document."""

    message_id = IntegerField(required=True)
    stars = IntegerField(required=True)
    jump = StringField(required=True)
    starboard_id = IntegerField(required=True)
    reacted = ListField(IntegerField())

    class Meta:
        """MongoDb database collection name."""

        collection_name = "Starboard"

    @classmethod
    async def search(cls, _id):
        return await cls.find_one({"message_id": _id})


@instance.register
class SuggestionStars(Document):
    """SuggestionStars database document."""

    message_id = IntegerField(required=True)
    stars = IntegerField(required=True)
    jump = StringField(required=True)
    starboard_id = IntegerField(required=True)
    reacted = ListField(IntegerField())

    class Meta:
        """MongoDb database collection name."""

        collection_name = "Suggestions"

    @classmethod
    async def search(cls, _id):
        return await cls.find_one({"message_id": _id})


@instance.register
class TopThree(Document):
    """Top Three (podium) for weekly tournaments database document."""

    ta_podium = ListField(IntegerField())
    mc_podium = ListField(IntegerField())
    hc_podium = ListField(IntegerField())
    bonus_podium = ListField(IntegerField())

    class Meta:
        """MongoDb database collection name."""

        collection_name = "TopThree"
