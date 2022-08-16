import logging
import json
import re
import requests
import yaml
from markdownify import markdownify as md

from ckan.logic import ValidationError, NotFound
from ckan.plugins import toolkit as tk

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters import HarvesterBase

log = logging.getLogger(__name__)


class ASDIHarvester(HarvesterBase):
    """
    A Harvester specifically for the Amazon Sustainability Data Initiative (ASDI)
    ASDI datasets are hosted on Amazon's Open Data Registry on Github
    """

    config = None

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
            "name": "asdi",
            "title": "asdi",
            "description": "Harvests AWS Open Data Registry Amazon Sustainability Data Initiative (ASDI) datasets",
            "form_config_interface": "Text",
        }

    def validate_config(self, config):
        return config

    def get_original_url(self, harvest_object_id):
        return ""

    def modify_package_dict(self, package_dict, harvest_object):
        return package_dict

    def gather_stage(self, harvest_job):
        log.info("ASDIHarvester gather_stage (%s)" % harvest_job.source.url)
        self._set_config(harvest_job.source.config)

        url = (
            "https://api.github.com/repos/awslabs/open-data-registry/contents/datasets"
        )
        r = requests.get(
            url, params={"Header": "Accept: application/vnd.github.v3+json"}
        )
        files = [d["download_url"] for d in r.json()]

        object_ids = []

        for counter, file_url in enumerate(files[:50]):
            if counter % 10 == 0:
                log.info(f"Processing {counter} of {len(files)}")
            try:
                r = requests.get(file_url)
                res = yaml.safe_load(r.content)

                # filter only Amazon Sustainability Data Initiative (ASDI) datasets
                if "Collabs" not in res:
                    continue
                if not "ASDI" in res["Collabs"]:
                    continue

                dataset = res
                has_records = "Resources" in res
                has_uses = "DataAtWork" in res
                name_slug = file_url.strip("/").split("/")[-1].rstrip(".yaml")

                content = {}
                # Transform ASDI schema to CKAN schema
                content.update({"url": f"https://registry.opendata.aws/{name_slug}/"})
                content.update({"id": name_slug})

                title = ""
                if "Name" in dataset.keys():
                    title = dataset["Name"]
                    content.update({"title": title})

                if "Description" in dataset.keys():
                    description = md(dataset["Description"])

                    # Append Documentation as we don't have a field for it
                    if "Documentation" in dataset.keys():
                        description += md("<br><h3>Documentation</h3><br>") + md(
                            dataset["Documentation"]
                        )

                    # Append UpdateFrequency because it is markdown text, not our vocabulary
                    if "UpdateFrequency" in dataset.keys():
                        description += md("<br><h3>Update Frequency</h3><br>") + md(
                            dataset["UpdateFrequency"]
                        )

                    # Append Citation because it is markdown text, not our vocabulary
                    if "Citation" in dataset.keys():
                        description += md("<br><h3>Citation</h3><br>") + md(
                            dataset["Citation"]
                        )

                    # Append Citation because it is markdown text, not our vocabulary
                    if "License" in dataset.keys():
                        description += md("<br><h3>License</h3><br>") + md(
                            dataset["License"]
                        )

                    # If empty description just use title otherwise CKAN will not
                    # import as notes field mustn't be empty
                    if len(description.strip()) == 0:
                        description = title

                    content.update({"notes": description})
                else:
                    content.update({"notes": title})

                if "Contact" in dataset.keys():
                    content.update({"author": dataset["Contact"]})

                if "ManagedBy" in dataset.keys():
                    content.update({"owner_org": dataset["ManagedBy"]})

                if "Tags" in dataset.keys():
                    tags = [{"name": tag.strip()} for tag in dataset["Tags"]]
                    content.update({"tags": tags})

                if has_records:
                    resources = {}

                    for resource in dataset["Resources"]:
                        r = {"name": dataset["Name"]}
                        if "Description" in resource.keys():
                            r["description"] = f"{resource['Description']}"
                        if "Type" in resource.keys():
                            r["format"] = f"{resource['Type']}"
                        if "Explore" in resource.keys():
                            r["url"] = f"{resource['Explore']}"
                        elif "ARN" in resource.keys():
                            r["url"] = f"{resource['ARN']}"

                        resources.update(r)

                    content.update({"resources": [resources]})

                if has_uses:
                    data_applications = []
                    if (
                        "Tutorials" in dataset["DataAtWork"]
                        and dataset["DataAtWork"]["Tutorials"]
                    ):
                        for t in dataset["DataAtWork"]["Tutorials"]:
                            data_applications.append(
                                {
                                    "category": "tutorials",
                                    "title": t["Title"],
                                    "url": t["URL"],
                                    "author": t["AuthorName"],
                                }
                            )
                    if (
                        "Tools & Applications" in dataset["DataAtWork"]
                        and dataset["DataAtWork"]["Tools & Applications"]
                    ):
                        for t in dataset["DataAtWork"]["Tools & Applications"]:
                            data_applications.append(
                                {
                                    "category": "tools_and_applications",
                                    "title": t["Title"],
                                    "url": t["URL"],
                                    "author": t["AuthorName"],
                                }
                            )
                    if (
                        "Publications" in dataset["DataAtWork"]
                        and dataset["DataAtWork"]["Publications"]
                    ):
                        for t in dataset["DataAtWork"]["Publications"]:
                            data_applications.append(
                                {
                                    "category": "publications",
                                    "title": t["Title"],
                                    "url": t["URL"],
                                    "author": t["AuthorName"],
                                }
                            )

                    content.update({"subak_data_applications": data_applications})

                # Save the fetched contents in the HarvestObject
                obj = HarvestObject(
                    guid=name_slug, job=harvest_job, content=json.dumps(content)
                )
                obj.save()
                object_ids.append(obj.id)

            except Exception as e:
                log.exception(f"Could not load ASDI file: {file_url}")
                self._save_object_error(e, harvest_job)

        try:
            return object_ids
        except Exception as e:
            log.exception(f"Could not load ASDI datasets")
            self._save_object_error(e, harvest_job)

    def fetch_stage(self, harvest_object):
        return True

    def import_stage(self, harvest_object):
        log.debug("ASDIHarvester import_stage")

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
                        for g in self.config["default_groups"]
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
                    # orgs represented as markdown links e.g. [NOAA](http://www.noaa.gov/)
                    match = re.match("\[[\D\d.]+\]", remote_org.lower())
                    if match:
                        name = match.group().lstrip("[").rstrip("]")
                    else:
                        log.info(f"Organization {remote_org.lower()} does not have name as a formatted markdown link")
                        name = remote_org.title()

                    org_name = re.sub(r"[^\s\w]", "", name).replace(
                        " ", "-"
                    )
                    if len(org_name) > 100:
                        org_name = org_name[:100]

                    try:
                        org = tk.get_action("organization_show")(
                            {"ignore_auth": True, "user": None}, {"id": org_name}
                        )
                        validated_org = org["id"]
                    except NotFound:
                        log.info(f"Organization {org_name} is not available")
                        if remote_orgs == "create":
                            try:
                                org = tk.get_action("organization_create")(
                                    {
                                        "ignore_auth": True,
                                        "user": self._get_user_name(),
                                    },
                                    {"name": org_name, "title": name.title()},
                                )

                                log.info(
                                    f"Organization {name} has been newly created"
                                )
                                validated_org = org["id"]

                            except ValidationError as e:
                                log.error(f"Could not get remote org {name}, {e}")

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
