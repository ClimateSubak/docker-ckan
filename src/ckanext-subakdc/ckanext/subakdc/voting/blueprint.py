from flask import Blueprint, render_template, request

import ckan.plugins.toolkit as tk

from ckanext.subakdc.voting.model import UserDatasetVotes

# Create Blueprint for plugin
voting = Blueprint("voting", __name__)


def view(pkg_id, vote_type):
    # Get the required API actions
    show_package = tk.get_action("package_show")
    patch_package = tk.get_action("package_patch")

    # Get the full package
    pkg = show_package({"ignore_auth": True, "user": None}, {"id": pkg_id})

    # Only consider packages that are datasets and only if user is logged in
    if pkg.get("type", None) == "dataset" and tk.g.userobj is not None:

        # Get current vote count for package
        n_votes = (
            int(pkg["subak_votes"])
            if "subak_votes" in pkg and pkg["subak_votes"] is not None
            else 0
        )

        # Create vote record against user/dataset
        vote_state = UserDatasetVotes.create(
            user_id=tk.g.userobj.id, dataset_id=pkg["id"], vote_type=vote_type
        )

        # Determine new vote count for package
        if vote_state == "new":
            vote_change = 1
        elif vote_state == "cancelled":
            vote_change = -1
        elif vote_state == "switched":
            vote_change = 2

        if vote_type == "up":
            n_votes = n_votes + vote_change
        elif vote_type == "down":
            n_votes = n_votes - vote_change

        # Update the vote count on the package
        patch_package(
            {"ignore_auth": True, "user": None},
            {"id": pkg["id"], "subak_votes": n_votes},
        )

    size = request.args.get("size", default="small")
    return render_template("snippets/voting.html", pkg_id=pkg_id, size=size)


voting.add_url_rule(
    "/dataset/<string:pkg_id>/vote/<string:vote_type>",
    "dataset_vote",
    view,
    methods=["POST"],
)


def get_blueprints():
    return [voting]
