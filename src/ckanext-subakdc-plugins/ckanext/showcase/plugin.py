import logging
import json
import os

from flask import Blueprint

import ckan.plugins as p
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)


def list_showcases():
    """
    Returns a list of showcases based on the filenames in the topics directory
    """
    showcases = []
    dirpath = os.path.join(os.path.dirname(__file__), "topics")
    for filename in os.listdir(dirpath):
        if filename.endswith(".json"):
            showcases.append(filename.replace(".json", ""))

    return showcases


def get_showcase(slug):
    """
    Read showcase information from JSON file and return as a dict
    """
    dirpath = os.path.join(os.path.dirname(__file__), "topics")
    filename = f"{slug}.json"
    filepath = os.path.join(dirpath, filename)
    with open(filepath) as f:
        showcase = json.load(f)

    return showcase


def showcase_view(slug):
    """
    View function for showcase show page
    """
    showcase = get_showcase(slug)
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
