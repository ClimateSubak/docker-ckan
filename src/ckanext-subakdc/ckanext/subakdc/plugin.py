import logging
from urllib.parse import urlparse

import ckan.plugins as p
import ckan.plugins.toolkit as tk

import ckanext.subakdc.oauth.blueprint as oauth
import ckanext.subakdc.custom_pages.blueprint as custom_pages
from ckanext.subakdc.verification import actions, auth
import ckanext.subakdc.verification.blueprint as verification
from ckanext.subakdc.verification.helpers import user_unverified
from ckanext.subakdc.voting.cli import get_commands
import ckanext.subakdc.voting.blueprint as voting
from ckanext.subakdc.voting.helpers import (
    user_has_upvoted_dataset,
    user_has_downvoted_dataset,
)

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


def homepage_tags():
    tags = tk.g.search_facets["tags"]["items"]
    list_tags = tk.get_action('tag_list')
    tags = list_tags({}, {"all_fields": True})    
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

    try:
        pkgs = group_package_show(
            {"ignore_auth": True, "user": None}, {"id": SUBAK_COOP_GROUP_NAME}
        )
    except:
        return None

    orgs = list(
        {pkg["organization"]["name"]: pkg["organization"] for pkg in pkgs}.values()
    )

    if len(orgs) < 1:
        return None
    else:
        return orgs
    
def get_schema_field(schema_fields, field_name):
    field = list(filter(lambda f: f['field_name'] == field_name, schema_fields))[0]
    return field
    

class SubakdcPlugin(p.SingletonPlugin):
    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.IBlueprint)
    p.implements(p.IClick)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    
    # ------- IActions method implementations ------- #
    def get_actions(self):
        return {
            "user_create": actions.user_create,
            'user_update': actions.user_update,
        }
        
    # ------- IAuthFunctions method implementations ------- #
    def get_auth_functions(self):
        return {
            "package_create": auth.package_create,
            "organization_create": auth.organization_create,
        }

    # ------- IBlueprint method implementations ------- #
    def get_blueprint(self):
        return verification.get_blueprints() + oauth.get_blueprints() + custom_pages.get_blueprints() + voting.get_blueprints()

    # ------- IClick method implementations ------- #
    def get_commands(self):
        return get_commands()

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
            "get_schema_field": get_schema_field,
            "get_subak_coop_group_from_dataset": get_subak_coop_group_from_dataset,
            "get_subak_coop_orgs": get_subak_coop_orgs,
            "user_has_upvoted_dataset": user_has_upvoted_dataset,
            "user_has_downvoted_dataset": user_has_downvoted_dataset,
            "user_unverified": user_unverified,
        }
