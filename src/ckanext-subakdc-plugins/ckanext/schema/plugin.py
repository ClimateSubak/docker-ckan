import logging
import json
from os import path
import ckan.plugins as p

log = logging.getLogger(__name__)


def get_countries_dict():
    with open(path.join(path.dirname(__file__), "countries-iso-3166.json")) as f:
        countries = json.load(f)

    return list(map(lambda c: {"value": c["alpha-2"], "label": c["name"]}, countries))


def get_country_name_from_code(code):
    with open(path.join(path.dirname(__file__), "countries-iso-3166.json")) as f:
        countries = json.load(f)
    codes_to_names = {c["alpha-2"]: c["name"] for c in countries}
    if code == "[]" or code is None:
        return None
    return codes_to_names[code]


class SchemaPlugin(p.SingletonPlugin):
    p.implements(p.ITemplateHelpers)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    # ------- ITemplateHelpers method implementations ------- #

    def get_helpers(self):
        """
        Helper function to extract the freshness score from the package dict
        """
        helpers = {
            "scheming_countries_choices": get_countries_dict,
            "scheming_code_to_name": get_country_name_from_code,
        }
        return helpers

    # ------- IFacets method implementations ------- #
    def dataset_facets(self, facets_dict, package_type):
        """
        Adds custom facets from schema to search facets
        """
        facets_dict["subak_countries"] = "Country"
        facets_dict["subak_geo_region"] = "Region"
        facets_dict["subak_temporal_start"] = "Earliest Date"
        facets_dict["subak_temporal_end"] = "Latest Date"
        return facets_dict

    # ------- IPackageController method implementations ------- #
    def before_index(self, data_dict):
        data_dict["subak_countries"] = json.loads(
            data_dict.get("subak_countries", "[]")
        )
        return data_dict
