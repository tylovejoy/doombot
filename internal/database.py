from umongo import Document, EmbeddedDocument
from umongo.fields import (
    BooleanField,
    DateTimeField,
    DictField,
    FloatField,
    IntegerField,
    ListField,
    StringField,
    UrlField,
    EmbeddedField,
    BaseField,
)

from internal.database_init import instance


@instance.register
class TimeAttackData(EmbeddedDocument):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    name = StringField(required=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)



@instance.register
class MildcoreData(EmbeddedDocument):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    name = StringField(required=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)


@instance.register
class HardcoreData(EmbeddedDocument):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    name = StringField(required=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)




@instance.register
class BonusData(EmbeddedDocument):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    name = StringField(required=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)


@instance.register
class TournamentRecords(EmbeddedDocument):
    """Records."""

    ta = ListField(EmbeddedField(TimeAttackData), allow_none=True)
    mc = ListField(EmbeddedField(MildcoreData), allow_none=True)
    hc = ListField(EmbeddedField(HardcoreData), allow_none=True)
    bo = ListField(EmbeddedField(BonusData), allow_none=True)


@instance.register
class TournamentMaps(EmbeddedDocument):
    """Records."""

    ta = DictField()
    mc = DictField()
    hc = DictField()
    bo = DictField()



@instance.register
class TournamentData(Document):
    """MapData database document."""

    tournament_id = IntegerField()
    name = StringField()

    schedule_start = DateTimeField()
    schedule_end = DateTimeField()

    embed_dict = DictField()

    maps = EmbeddedField(TournamentMaps)
    records = EmbeddedField(TournamentRecords)
    missions = DictField()

    class Meta:
        """MongoDb database collection name."""

        collection_name = "TournamentData"


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
