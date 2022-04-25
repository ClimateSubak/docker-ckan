import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckanext.report.interfaces import IReport

from ckanext.qa import tasks, reports, helpers
from ckanext.qa.cli import get_commands
from ckanext.qa.qa import QaTaskRunner


def run_qa_tasks_on_package(pkg):
    runner = QaTaskRunner(list(tasks.values()))
    func = runner.run_on_single_package
    tk.enqueue_job(func, [pkg.get("id")])


class QAPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IClick)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IPackageController, inherit=True)
    p.implements(IReport)

    # ------- IClick method implementations ------- #
    def get_commands(self):
        return get_commands()

    # ------- IConfigurer method implementations ------- #
    def update_config(self, config):
        tk.add_template_directory(config, "templates")

    # ------- ITemplateHelpers method implementations ------- #
    def get_helpers(self):
        return helpers

    # ------- IPackageController method implementations ------- #
    def after_create(self, context, pkg_dict):
        run_qa_tasks_on_package(pkg_dict)

    def after_update(self, context, pkg_dict):
        run_qa_tasks_on_package(pkg_dict)

    # ------- IReport method implementations ------- #
    def register_reports(self):
        return reports
