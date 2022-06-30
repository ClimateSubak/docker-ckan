# Temporary in-memory storage of votes
# TODO replace with db storage of votes
up_votes = []
down_votes = []


def user_has_upvoted_dataset(pkg_id):
    return pkg_id in up_votes


def user_has_downvoted_dataset(pkg_id):
    return pkg_id in down_votes
