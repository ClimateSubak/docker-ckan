import json
import logging

import ckan.plugins.toolkit as tk

from ckanext.qa.utils import get_all_pkgs, get_qa_properties

log = logging.getLogger(__name__)


class QaTaskRunner:
    tasks = []

    def __init__(self, tasks):
        self.tasks = tasks

    def run(self):
        """
        Runs QA tasks over all packages. Starts a new job for each each package and runs run_on_single_package to update QA properties on the package
        """
        # Get all packages and associated resources
        pkgs = get_all_pkgs()

        for pkg in pkgs:
            func = self.run_on_single_package
            tk.enqueue_job(func, [pkg.get("id")])

    def run_on_single_package(self, pkg_id):
        """
        Runs whenever a package is created/updated. Runs all QA tasks against the package
        and sets the qa property in the subak_qa dict on the model
        """

        # Get the required API actions
        show_package = tk.get_action("package_show")
        patch_package = tk.get_action("package_patch")

        # Get the full package
        pkg = show_package({"ignore_auth": True, "user": None}, {"id": pkg_id})

        # Skip any packages that aren't datasets
        if pkg.get("type", None) != "dataset":
            return

        # Get the current QA properties
        qa = get_qa_properties(pkg)

        # Clone qa properties and evaluate the package against all the qa tasks,
        new_qa = qa.copy()
        for task in self.tasks:
            new_qa[task.qa_property_name] = task.evaluate(pkg)

        # Only patch the package if the qa properties have changed
        if qa != new_qa:
            patch_package(
                {"ignore_auth": True, "user": None},
                {"id": pkg["id"], "subak_qa": json.dumps(new_qa)},
            )
