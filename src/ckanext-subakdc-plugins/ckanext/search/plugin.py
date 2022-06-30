import logging
import json
import re

import ckan.plugins as p

log = logging.getLogger(__name__)


class SearchPlugin(p.SingletonPlugin):
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    # ------- IFacets method implementations ------- #
    def dataset_facets(self, facets_dict, package_type):
        """
        Adds custom facets from schema to search facets
        """
        facets_dict["subak_countries"] = "Country"
        facets_dict["subak_geo_region"] = "Region"
        facets_dict["subak_temporal_start"] = "Dataset coverage from"
        facets_dict["subak_temporal_end"] = "Dataset coverage to"
        return facets_dict

    # ------- IPackageController method implementations ------- #
    def before_index(self, data_dict):
        data_dict["subak_countries"] = json.loads(
            data_dict.get("subak_countries", "[]")
        )
        return data_dict

    def before_search(self, search_params):
        fq = search_params.get("fq", "")

        if "subak_temporal_start" in fq:
            start = re.search(r'subak_temporal_start:"(.*?)"', fq)[1]
            start = f"{start}-01-01T00:00:00Z"
        else:
            start = "*"

        if "subak_temporal_end" in fq:
            end = re.search(r'subak_temporal_end:"(.*?)"', fq)[1]
            end = f"{end}-12-31T23:59:59Z"
        else:
            end = "*"

        # Remove the subak_temporal_* fields from fq
        _fq = re.sub(r'subak_temporal_start:"(.*?)"', "", fq)
        _fq = re.sub(r'subak_temporal_end:"(.*?)"', "", _fq)

        if "subak_temporal_start" in fq or "subak_temporal_end" in fq:
            # Show datasets if subak_temporal_start or subak_temporal_end fall within
            # the specified date range
            fq = f"{_fq} + (subak_temporal_start:[{start} TO {end}] OR subak_temporal_end:[{start} TO {end}])"

        search_params["fq"] = fq

        # Apply boosting function to amend the relevancy score based on up/down votes
        # TODO this may need to be tweaked but currently a linear function: 0.5 * subak_votes + 0
        # As we should expect subak_votes to be low, perhaps the linear coefficient could be higher
        # N.b the boosting function is additive. ie. new_score = score + boost
        search_params["bf"] = "linear(subak_votes,0.5,0)"

        return search_params
