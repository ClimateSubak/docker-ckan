import logging
import json
import re
import requests
from markdownify import markdownify as md

from ckan.logic import ValidationError, NotFound
from ckan.plugins import toolkit as tk

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters import HarvesterBase

log = logging.getLogger(__name__)

def is_acceptable_dataset(dataset):
    """
    Filters out any datasets that:
        - have no files 
        - have only a single docx file
    """
    if 'files' not in dataset or len(dataset['files']) == 0:
        return False

    if len(dataset['files']) == 1:
        file_types = ['doc', 'docx']
        if any(map(lambda x: dataset['files'][0]['name'].lower().endswith(x), file_types)):
            return False
    
    return True

def format_package_title(title):
    """
    Removes prefixes that look like Table_1_ or DataSheet1_ etc
    Removes suffixes that look like .docx or .XLSX etc
    """
    title = re.sub(r'.*_(.*)', r'\1', title)
    title = re.sub(r'(.*)\..*', r'\1', title)
    return title
    

class EuropaHarvester(HarvesterBase):
    """
    A Harvester for datasets hosted on Figshare
    """
    config = None
    base_url = "https://api.figshare.com/v2"

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
            "name": "figshare",
            "title": "figshare",
            "description": "Harvests remote figshare datasets",
            "form_config_interface": "Text",
        }

    def validate_config(self, config):
        return config

    def get_original_url(self, harvest_object_id):
        return ""

    def modify_package_dict(self, package_dict, harvest_object):
        return package_dict

    def gather_stage(self, harvest_job):
        log.debug("FigshareHarvester gather_stage")

        self._set_config(harvest_job.source.config)

        search_query = self.config.get(
            "figshare_search_query", "climate"
        )

        more_datasets = True
        package_ids = []
        page_size = 500
        n = 1
        while more_datasets:
            # Search datasets on Figshare
            # API docs: https://docs.figshare.com/#articles_search
            url = f"{self.base_url}/articles/search"
            r = requests.post(url, json={"search_for": search_query, "item_type": 3, "page_size": page_size, "page": n})
            if r.status_code == 400:
                break
            
            datasets = r.json()

            log.debug(f"query={search_query}")
            log.debug(f"n datasets={len(datasets)}")

            for ds in datasets:
                # package_ids.append(ds["id"])
                package_ids.append(ds["url"])

            more_datasets = len(datasets) == page_size
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
        log.debug("FigshareHarvester fetch_stage")

        self._set_config(harvest_object.job.source.config)

        fetch_url = harvest_object.guid
        dataset = {}

        try:
            r = requests.get(fetch_url)
            dataset = r.json()

        except Exception as e:
            log.exception(f"Could not load URL: {fetch_url}")
            return self._save_object_error(
                f"Could not load URL: {fetch_url}", harvest_object
            )
        
        if not is_acceptable_dataset(dataset):
            return 'unchanged'

        content = {}

        # Transform Figshare schema to CKAN schema
        title = ""
        if "title" in dataset.keys():
            name = dataset["title"]
            content.update({"name": name})
            
            title = format_package_title(name)
            content.update({"title": title})

        # There is no consistent way to identify the publishing org from the API response
        # Sometimes it can be listed in the author field, a custom field or extracted from
        # the figshare_url but not easily discernable without human discretion
        # if (
        #     "creators" in dataset.keys()
        #     and len(dataset["creators"]) > 0
        #     and "affiliation" in dataset["creators"][0]
        # ):
        #     publisher = dataset["creators"][0]["affiliation"]
        #     content.update({"owner_org": publisher})
        #     content.update({"author": publisher})

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
            content.update({"license_id": dataset["license"]["name"]})

        if "tags" in dataset.keys():
            tags = [{"name": tag.strip()} for tag in dataset["tags"]]
            content.update({"tags": tags})

        if "created_date" in dataset.keys():
            # Ignore milliseconds and timezone adjustments
            content.update({"metadata_created": re.split(r"\.|\+", dataset["created_date"])[0]})

        if "modified_date" in dataset.keys():
            # Ignore milliseconds and timezone adjustments
            content.update({"metadata_modified": re.split(r"\.|\+", dataset["modified_date"])[0]})

        if "figshare_url" in dataset.keys():
            content.update({"url": dataset["figshare_url"]})
            
        if "citation" in dataset.keys():
            content.update({"author": dataset["citation"]})

        content.update({"id": dataset['doi']})

        if "files" in dataset and len(dataset["files"]) > 0:
            resources = []
            for f in dataset['files']:
                resource = {}
                resource.update(
                    {
                        "url": f["download_url"],
                        "format": re.split(r"\.", f["name"])[-1],
                    }
                )

                resource.update({"name": f["name"]})

                if "modified_date" in dataset.keys():
                    # Ignore milliseconds and timezone adjustments
                    resource.update(
                        {"last_modified": re.split(r"\.|\+", dataset["modified_date"])[0][0:-1]})
            
                resources.append(resource)

            content.update({"resources": resources})

        # Save the fetched contents in the HarvestObject
        harvest_object.content = json.dumps(content)
        harvest_object.save()

        return True

    def import_stage(self, harvest_object):
        log.debug("FigshareHarvester import_stage")

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
