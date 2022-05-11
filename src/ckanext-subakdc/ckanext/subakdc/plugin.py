import logging
from urllib.parse import urlparse

import ckan.plugins as p
import ckan.plugins.toolkit as tk

HOMEPAGE_TAGS = [
    "CO2",
    "Energy",
    "Agriculture",
    "Wind",
    "Solar",
    "Electricity",
    "Crude Oil",
]

log = logging.getLogger(__name__)


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

    groups = list(filter(lambda grp: grp["name"] == "data-cooperative", pkg["groups"]))

    if len(groups) < 1:
        return None
    else:
        return groups[0]


class SubakdcPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)

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
        }
