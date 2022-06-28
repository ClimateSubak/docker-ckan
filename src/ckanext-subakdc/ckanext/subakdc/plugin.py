import logging
from urllib.parse import urlparse
from flask import Blueprint, render_template, request

import ckan.plugins as p
import ckan.plugins.toolkit as tk

HOMEPAGE_TAGS = [
    "co2",
    "energy",
    "agriculture",
    "wind",
    "solar",
    "electricity",
    "crude oil",
]
SUBAK_COOP_GROUP_NAME = "data-cooperative"

log = logging.getLogger(__name__)

# Temporary in-memory storage of votes
# TODO replace with db storage of votes
up_votes = []
down_votes = []


def vote_handler(pkg_id, vote_type):
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
            try:
                down_votes.remove(pkg_id)
            except ValueError:
                pass
            up_votes.append(pkg_id)
            n_votes = n_votes + 1
        elif vote_type == "down":
            try:
                up_votes.remove(pkg_id)
            except ValueError:
                pass
            down_votes.append(pkg_id)
            n_votes = n_votes - 1

        # Update the vote count on the package
        patch_package(
            {"ignore_auth": True, "user": None},
            {"id": pkg["id"], "subak_votes": n_votes},
        )

    size = request.args.get("size", default="small")
    return render_template("snippets/voting.html", pkg_id=pkg_id, size=size)


def homepage_tags():
    tags = tk.g.search_facets["tags"]["items"]
    filtered_tags = list(filter(lambda tag: tag["name"] in HOMEPAGE_TAGS, tags))

    return filtered_tags


def is_url(text):
    try:
        res = urlparse(text)
        return all([res.scheme, res.netloc])
    except:
        return False


def get_subak_coop_group_from_dataset(pkg):
    if "groups" not in pkg or not (pkg["groups"]):
        return None

    groups = list(
        filter(lambda grp: grp["name"] == SUBAK_COOP_GROUP_NAME, pkg["groups"])
    )

    if len(groups) < 1:
        return None
    else:
        return groups[0]


def get_subak_coop_orgs():
    group_package_show = tk.get_action("group_package_show")
    # organization_show = tk.get_action("organization_show")

    pkgs = group_package_show(
        {"ignore_auth": True, "user": None}, {"id": SUBAK_COOP_GROUP_NAME}
    )

    orgs = list(
        {pkg["organization"]["name"]: pkg["organization"] for pkg in pkgs}.values()
    )

    if len(orgs) < 1:
        return None
    else:
        return orgs


class SubakdcPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)

    # ------- IBlueprint method implementations ------- #
    def get_blueprint(self):
        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)
        # blueprint.template_folder = u'templates'

        blueprint.add_url_rule(
            "/dataset/<string:pkg_id>/vote/<string:vote_type>",
            "dataset_vote",
            vote_handler,
            methods=["POST"],
        )

        return blueprint

    # ------- IConfigurer method implementations ------- #
    def update_config(self, config):
        tk.add_template_directory(config, "templates")
        tk.add_public_directory(config, "public")
        tk.add_resource("./assets", "ckanext-subakdc")

    # ------- ITemplateHelpers method implementations ------- #
    def get_helpers(self):
        """
        Helper function to define homepage quick explore tags
        """
        return {
            "homepage_quick_explore_tags": homepage_tags,
            "get_subak_coop_group_from_dataset": get_subak_coop_group_from_dataset,
            "get_subak_coop_orgs": get_subak_coop_orgs,
            "user_has_upvoted_dataset": lambda pkg_id: pkg_id in up_votes,
            "user_has_downvoted_dataset": lambda pkg_id: pkg_id in down_votes,
        }
