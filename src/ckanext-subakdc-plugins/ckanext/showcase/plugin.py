import logging
import json
import os

from flask import Blueprint

from ckan.logic import NotFound
import ckan.plugins as p
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)


def list_showcases():
    """
    Returns a list of showcases based on the filenames in the topics directory
    """
    showcases = []
    dirpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topics")
    for filename in os.listdir(dirpath):
        if filename.endswith(".json"):
            showcases.append(filename.replace(".json", ""))

    return showcases


def get_showcase(slug):
    """
    Read showcase information from JSON file and return as a dict
    """
    dirpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topics")
    filename = f"{slug}.json"
    filepath = os.path.join(dirpath, filename)
    with open(filepath) as f:
        showcase = json.load(f)

    return showcase


def hydrate_showcase(showcase_dict):
    """
    Takes dictized output from JSON file and adds extra information (for pkg_dicts for top datasets)
    """
    package_search = tk.get_action("package_search")
    pkgs = package_search({}, {"q": showcase_dict["data"]["search_query"], "rows": 0})
    showcase_dict["data"]["count"] = pkgs["count"]

    showcase_dict["top_datasets"] = list(
        map(get_package, showcase_dict["top_datasets"])
    )
    for k, app in enumerate(showcase_dict["data_applications"]):
        showcase_dict["data_applications"][k]["dataset"] = get_package(app["dataset"])

    showcase_dict["highlighted_vis"]["dataset"] = get_package(
        showcase_dict["highlighted_vis"]["dataset"]
    )

    return showcase_dict


def get_package(name):
    show_package = tk.get_action("package_show")
    try:
        pkg = show_package({"ignore_auth": True, "user": None}, {"id": name})
    except NotFound:
        log.debug(f"Package not found for name={name}")
        return None

    return pkg


def showcase_view(slug):
    """
    View function for showcase show page
    """
    showcase = get_showcase(slug)
    showcase = hydrate_showcase(showcase)
    return tk.render("showcase/showcase_base.html", extra_vars={"showcase": showcase})


class ShowcasePlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    p.implements(p.IConfigurer)

    # ------- IBlueprint method implementations ------- #
    def get_blueprint(self):
        """
        Return a Flask Blueprint object to be registered by the app.
        """

        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)
        blueprint.template_folder = "templates"

        # blueprint.add_url_rule(f'/showcase', view_func=, strict_slashes=False)

        for slug in list_showcases():
            blueprint.add_url_rule(
                f"/showcase/{slug}",
                view_func=lambda: showcase_view(slug),
                strict_slashes=False,
            )

        return blueprint

    # ------- IConfigurer method implementations ------- #
    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
