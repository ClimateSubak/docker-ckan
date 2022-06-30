import enum
from sqlalchemy import types, Column, Enum, ForeignKey, MetaData, Table
from sqlalchemy.orm import mapper

from ckan import model
from ckan.model.meta import metadata


class VoteTypeEnum(enum.Enum):
    up = 1
    down = 2


user_dataset_votes_table = Table(
    "user_dataset_votes",
    metadata,
    Column(
        "object_id",
        types.UnicodeText,
        ForeignKey("package.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "user_id",
        types.UnicodeText,
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column("vote_type", Enum(VoteTypeEnum), nullable=False),
)


class UserDatasetVotes(object):
    @classmethod
    def getUserVoteForDataset(cls, user_id, dataset_id):
        item = (
            model.Session.query(cls)
            .filter(cls.user_id == user_id)
            .filter(cls.object_id == dataset_id)
            .first()
        )
        if not item:
            return None

        return item


mapper(UserDatasetVotes, user_dataset_votes_table)


def init_tables():
    metadata.create_all(model.meta.engine)
