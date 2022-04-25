from flask import Blueprint

import ckan.plugins as p
import ckan.plugins.toolkit as tk


def showcase_view():
    """A simple view function"""
    return tk.render("showcase/index.html", extra_vars={})


class ShowcasePlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    p.implements(p.IConfigurer)

    # ------- IBlueprint method implementations ------- #
    def get_blueprint(self):
        """Return a Flask Blueprint object to be registered by the app."""

        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)
        blueprint.template_folder = "templates"

        rules = [
            ("/showcase", "showcase_view", showcase_view),
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        return blueprint

    # ------- IConfigurer method implementations ------- #
    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
