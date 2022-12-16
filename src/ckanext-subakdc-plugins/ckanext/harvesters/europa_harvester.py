import logging
import json
from os import path
import re
import requests
from markdownify import markdownify as md

from ckan.logic import ValidationError, NotFound
from ckan.plugins import toolkit as tk

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters import HarvesterBase

log = logging.getLogger(__name__)

def get_countries():
    with open(path.join(path.dirname(__file__), "..", "countries-iso-3166.json")) as f:
        countries = json.load(f)
    
    return list(map(lambda c: {"value": c["alpha-2"], "label": c["name"]}, countries))
    

class EuropaHarvester(HarvesterBase):
    """
    A Harvester for datasets hosted on data.europa.eu
    """
    config = None
    base_url = "https://data.europa.eu/api/hub/search"

    def _set_config(self, config_str):
        if config_str:
            self.config = json.loads(config_str)

            if "api_version" in self.config:
                self.api_version = self.config["api_version"]

            log.debug("Using config: %r", self.config)
        else:
            self.config = {}

    def info(self):
        return {
            "name": "data.europa.eu",
            "title": "data.europa.eu",
            "description": "Harvests remote data.europa.eu datasets",
            "form_config_interface": "Text",
        }

    def validate_config(self, config):
        return config

    def get_original_url(self, harvest_object_id):
        return ""

    def modify_package_dict(self, package_dict, harvest_object):
        return package_dict

    def gather_stage(self, harvest_job):
        log.debug("EuropaHarvester gather_stage")

        self._set_config(harvest_job.source.config)

        search_query = self.config.get(
            "europa_search_query", "climate"
        )
        
        log.debug(f"query={search_query}")

        more_datasets = True
        package_ids = []
        page_size = 500
        max_datasets = 10000
        n = 0
        while more_datasets:
            # Search datasets on data.europa.eu
            # API docs: https://data.europa.eu/api/hub/search/#tag/Search/operation/searchGet
            url = f"{self.base_url}/search?q={search_query}&limit={page_size}&page={n}&includes=id"
            r = requests.get(url)
            if r.status_code == 400:
                break
            
            res = r.json()
            datasets = res["result"]["results"]

            log.debug(f"page={n}")
            log.debug(f"n datasets={len(datasets)}")

            for ds in datasets:
                # package_ids.append(ds["id"])
                package_ids.append(ds["id"])

            more_datasets = len(datasets) == page_size and len(package_ids) < max_datasets
            # more_datasets = False

            n += 1

        log.debug(f"total datasets={len(package_ids)}")

        try:
            object_ids = []
            if len(package_ids) > 0:
                for package_id in package_ids:
                    obj = HarvestObject(guid=package_id, job=harvest_job)
                    obj.save()
                    object_ids.append(obj.id)

                return object_ids

            else:
                self._save_gather_error(
                    f"No packages received for URL: {url}, {harvest_job}"
                )
                return None

        except Exception as e:
            self._save_gather_error(e.message, harvest_job)

    def fetch_stage(self, harvest_object):
        log.debug("EuropaHarvester fetch_stage")

        self._set_config(harvest_object.job.source.config)

        dataset = {}
        try:
            url = f"{self.base_url}/datasets/{harvest_object.guid}"
            res = requests.get(url).json()
            dataset = res["result"]

        except Exception as e:
            log.exception(f"Could not load URL: {url}")
            return self._save_object_error(
                f"Could not load URL: {url}", harvest_object
            )

        content = {}
        content.update({ "id": f"europa-{harvest_object.guid}" })

        # Transform data.europa.eu schema to CKAN schema
        # Title
        try:
            title = dataset["title"]["en"]
        except:
            try:
                title = dataset["title"][list(dataset["title"].keys())[0]]
            except:
                title = ""
        
        content.update({"title": title})

        # Publisher
        try:
            publisher = dataset["catalog"]["publisher"]["name"]
            content.update({"owner_org": publisher})
            content.update({"author": publisher})
        except KeyError:
            pass

        # Description
        try:
            description = dataset["description"]["en"]
        except:
            try:
                description = dataset["description"][list(dataset["description"].keys())[0]]
            except:
                description = ""
        
        description = md(description)

        # If empty description just use title otherwise CKAN will not
        # import as notes field mustn't be empty
        if len(description.strip()) == 0:
            description = title

        content.update({"notes": description})

        # License
        try:
            license = dataset["license"]["name"]
            content.update({"license_id": license})
        except KeyError:
            pass

        # Tags
        tags = []
        try:
            keywords = dataset["keywords"]
            if keywords is not None:
                for kw in keywords:
                    if kw["language"] == "en":
                        tags.append(kw["label"])
        except KeyError:
            pass
                    
        try:
            categories = dataset["categories"]
            if categories is not None:
                for category in categories:
                    tags = tags + [tag.strip() for tag in category["label"]["en"].split(",")]
        except KeyError:
            pass
        
        # empty tag to bypass validation error on no tags
        if len(tags) == 0:
            tags = ["no-tag"]
            
        tags = [{"name": tag.strip()} for tag in set(tags)]
        content.update({"tags": tags})

        # Country
        try:
            countries = get_countries()
            country_codes = [c['value'] for c in countries]
            c = dataset['country']["id"].upper()
            if c in country_codes:
                content.update({ "subak_countries": [c] })
        except KeyError:
            pass

        # Source URL
        try:
            source = dataset["resource"]
            content.update({"url": source})
        except KeyError:
            pass

        # Resources
        resources = []
        if "distributions" in dataset:
            for f in dataset['distributions']:
                try:
                    resource = {}
                    resource.update(
                        {
                            "url": f["access_url"],
                            "format": f["format"]["label"]
                        }
                    )
                    
                    name = content.get("title", "")
                    if "description" in f:
                        name = f["description"]["en"]
                    elif "title" in f:
                        name = f["title"]["en"]
                        
                    resource.update({"name": name})

                    # Drop Z character at the end of the timestamp
                    modified_at = dataset["catalog_record"]["modified"][:-1]
                    resource.update({"last_modified": modified_at})
                
                    resources.append(resource)
                except KeyError:
                    pass

        content.update({"resources": resources})

        # print(content)
        # Save the fetched contents in the HarvestObject
        harvest_object.content = json.dumps(content)
        harvest_object.save()

        return True

    def import_stage(self, harvest_object):
        log.debug("EuropaHarvester import_stage")

        if not harvest_object:
            log.error("No harvest object received")
            return False

        if harvest_object.content is None:
            self._save_object_error(
                f"Empty content for object {harvest_object.id}, {harvest_object}, Import"
            )
            return False

        self._set_config(harvest_object.job.source.config)

        try:
            package_dict = json.loads(harvest_object.content)

            # Set default tags if needed
            default_tags = self.config.get("default_tags", [])
            if default_tags:
                if "tags" not in package_dict:
                    package_dict["tags"] = []
                package_dict["tags"].extend(
                    [t for t in default_tags if t not in package_dict["tags"]]
                )

            # Set default groups if needed
            default_groups = self.config.get("default_groups", [])
            if default_groups:
                if "groups" not in package_dict:
                    package_dict["groups"] = []
                existing_group_ids = [g["id"] for g in package_dict["groups"]]
                package_dict["groups"].extend(
                    [
                        g
                        for g in self.config["default_group_dicts"]
                        if g["id"] not in existing_group_ids
                    ]
                )

            # Set org
            source_dataset = tk.get_action("package_show")(
                {"ignore_auth": True, "user": None}, {"id": harvest_object.source.id}
            )
            local_org = source_dataset.get("owner_org")

            remote_orgs = self.config.get("remote_orgs", None)
            if remote_orgs not in ("only_local", "create"):
                # Assign dataset to the source organization
                package_dict["owner_org"] = local_org

            else:
                if "owner_org" not in package_dict:
                    package_dict["owner_org"] = None

                # check if remote org exist locally, otherwise remove
                validated_org = None
                remote_org = package_dict["owner_org"]

                if remote_org:
                    org_name = re.sub(r"[^\s\w]", "", remote_org.lower()).replace(
                        " ", "-"
                    )
                    try:
                        org = tk.get_action("organization_show")(
                            {"ignore_auth": True, "user": None}, {"id": org_name}
                        )
                        validated_org = org["id"]
                    except NotFound:
                        log.info(f"Organization {remote_org} is not available")
                        if remote_orgs == "create":
                            try:
                                org = tk.get_action("organization_create")(
                                    {
                                        "ignore_auth": True,
                                        "user": self._get_user_name(),
                                    },
                                    {"name": org_name, "title": remote_org},
                                )

                                log.info(
                                    f"Organization {remote_org} has been newly created"
                                )
                                validated_org = org["id"]

                            except ValidationError as e:
                                log.error(f"Could not get remote org {remote_org}, {e}")

                package_dict["owner_org"] = validated_org or local_org

            result = self._create_or_update_package(
                package_dict, harvest_object, package_dict_form="package_show"
            )
            return result

        except ValidationError as e:
            self._save_object_error(
                "Invalid package with GUID %s: %r"
                % (harvest_object.guid, e.error_dict),
                harvest_object,
                "Import",
            )
        except Exception as e:
            self._save_object_error("%s" % e, harvest_object, "Import")
