from flask import Blueprint, render_template, request

import ckan.plugins.toolkit as tk

# Create Blueprint for plugin
voting = Blueprint("voting", __name__)


def view(pkg_id, vote_type):
    # Get the required API actions
    show_package = tk.get_action("package_show")
    patch_package = tk.get_action("package_patch")

    # Get the full package
    pkg = show_package({"ignore_auth": True, "user": None}, {"id": pkg_id})

    # Only consider packages that are datasets
    if pkg.get("type", None) == "dataset":

        # Get current vote count for package
        n_votes = (
            int(pkg["subak_votes"])
            if "subak_votes" in pkg and pkg["subak_votes"] is not None
            else 0
        )

        # Determine new vote count for package
        if vote_type == "up":
            # try:
            #     down_votes.remove(pkg_id)
            # except ValueError:
            #     pass
            # up_votes.append(pkg_id)
            n_votes = n_votes + 1
        elif vote_type == "down":
            # try:
            #     up_votes.remove(pkg_id)
            # except ValueError:
            #     pass
            # down_votes.append(pkg_id)
            n_votes = n_votes - 1

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
