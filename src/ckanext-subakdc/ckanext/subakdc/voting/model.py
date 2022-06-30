import enum
import logging
from sqlalchemy import types, Column, Enum, ForeignKey, Table

from ckan import model
from ckan.model.meta import metadata, mapper

log = logging.getLogger(__name__)


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
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def create(cls, user_id, dataset_id, vote_type):
        if vote_type == "up":
            vote_type = VoteTypeEnum.up
        else:
            vote_type = VoteTypeEnum.down

        vote = UserDatasetVotes.getUserVoteForDataset(
            user_id=user_id, dataset_id=dataset_id
        )
        log.debug(vote)
        if vote is None:
            vote = cls(user_id=user_id, object_id=dataset_id, vote_type=vote_type)
            model.Session.add(vote)
            state = "new"
        else:
            # If vote type hasn't changed
            if vote.vote_type == vote_type:
                model.Session.delete(vote)
                state = "cancelled"
            else:
                vote.vote_type = vote_type
                state = "switched"

        model.Session.flush()

        log.debug(state)
        return state

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
