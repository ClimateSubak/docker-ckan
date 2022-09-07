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


class ZenodoHarvester(HarvesterBase):
    """
    A Harvester for datasets hosted on Zenodo
    """

    config = None
    base_url = "https://zenodo.org/api"

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
            "name": "zenodo",
            "title": "zenodo",
            "description": "Harvests remote zenodo datasets",
            "form_config_interface": "Text",
        }

    def validate_config(self, config):
        return config

    def get_original_url(self, harvest_object_id):
        return ""

    def modify_package_dict(self, package_dict, harvest_object):
        return package_dict

    def gather_stage(self, harvest_job):
        log.debug("ZenodoHarvester gather_stage")

        keyword = "climate"  # About 9000 records in Zenodo as of Sep '22

        # 10K rows is max for single Zenodo API query
        url = f"{self.base_url}/records?q={keyword}&type=dataset"
        r = requests.get(url)
        res = r.json()
        datasets = res["hits"]["hits"]

        package_ids = []
        for ds in datasets:
            package_ids.append(ds["id"])

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
        log.debug("ZenodoHarvester fetch_stage")

        self._set_config(harvest_object.job.source.config)

        fetch_url = f"{self.base_url}/records/{harvest_object.guid}"
        dataset = {}

        try:
            r = requests.get(fetch_url)
            res = r.json()
            dataset = res["metadata"]
            has_records = len(res["files"]) > 0

        except Exception as e:
            log.exception(f"Could not load URL: {fetch_url}")
            self._save_object_error(e.message, harvest_object)

        content = {}

        # Transform zenodo schema to CKAN schema
        title = ""
        if "title" in dataset.keys():
            title = dataset["title"]
            content.update({"title": title})

        if "creators" in dataset.keys() and len(dataset["creators"]) > 0:
            publisher = dataset["creators"][0]["affiliation"]
            content.update({"owner_org": publisher})
            content.update({"author": publisher})

        if "description" in dataset.keys():
            description = md(dataset["description"])

            # If empty description just use title otherwise CKAN will not
            # import as notes field mustn't be empty
            if len(description.strip()) == 0:
                description = title

            content.update({"notes": description})
        else:
            content.update({"notes": title})

        if "license" in dataset.keys():
            content.update({"license_id": dataset["license"]["id"]})

        if "keywords" in dataset.keys():
            tags = [{"name": tag.strip()} for tag in dataset["keyword"]]
            content.update({"tags": tags})

        if "updated" in dataset.keys():
            # Ignore milliseconds and timezone adjustments
            content.update(
                {"metadata_modified": re.split(r"\.|\+", dataset["updated"])[0]}
            )

        content.update(
            {"url": f"{self.base_url.replace('/api', '')}/record/{harvest_object.guid}"}
        )

        # TODO Add data sources from dataset['references']

        content.update({"id": harvest_object.guid})

        if has_records == True:
            resource = {}
            resource.update(
                {
                    "url": f"{self.base_url}/api/v2/catalog/datasets/{harvest_object.guid}/exports/csv?delimiter=,&list_separator=|",
                    "format": "csv",
                }
            )

            if "title" in dataset.keys():
                resource.update({"name": dataset["title"]})

            if "data_processed" in dataset.keys():
                # Ignore milliseconds and timezone adjustments
                resource.update(
                    {"last_modified": re.split(r"\.|\+", dataset["data_processed"])[0]}
                )

            if "fields" in dataset and len(dataset["fields"]) > 0:
                fields = []
                for field in dataset["fields"]:
                    fields.append({"name": field["name"]})

                resource.update({"subak_data_fields": fields})

            content.update({"resources": [resource]})

        # Save the fetched contents in the HarvestObject
        harvest_object.content = json.dumps(content)
        harvest_object.save()

        return True

    def import_stage(self, harvest_object):
        log.debug("ZenodoHarvester import_stage")

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
