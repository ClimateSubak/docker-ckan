import logging
import ckan.plugins.toolkit as tk

from ckanext.subakdc.voting.model import VoteTypeEnum, UserDatasetVotes

log = logging.getLogger(__name__)


def user_has_upvoted_dataset(pkg_id):
    vote = UserDatasetVotes.getUserVoteForDataset(
        user_id=tk.g.userobj.id, dataset_id=pkg_id
    )
    return vote is not None and vote.vote_type == VoteTypeEnum.up


def user_has_downvoted_dataset(pkg_id):
    vote = UserDatasetVotes.getUserVoteForDataset(
        user_id=tk.g.userobj.id, dataset_id=pkg_id
    )
    return vote is not None and vote.vote_type == VoteTypeEnum.down
