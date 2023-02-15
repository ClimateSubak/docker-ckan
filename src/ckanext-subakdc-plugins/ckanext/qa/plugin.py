import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckanext.report.interfaces import IReport
from ckanext.qa import actions, reports, helpers
from ckanext.qa.cli import get_commands


class QAPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IActions)
    p.implements(p.IClick)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    p.implements(IReport)
    
    # ------- IActions method implementations ------- #
    def get_actions(self):
        return {
            "package_create": actions.package_create,
            'package_update': actions.package_update,
        }

    # ------- IClick method implementations ------- #
    def get_commands(self):
        return get_commands()

    # ------- IConfigurer method implementations ------- #
    def update_config(self, config):
        tk.add_template_directory(config, "templates")

    # ------- ITemplateHelpers method implementations ------- #
    def get_helpers(self):
        return helpers

    # ------- IReport method implementations ------- #
    def register_reports(self):
        return reports
