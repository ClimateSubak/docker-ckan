import logging

from ckan.lib.helpers import license_options

from ckanext.qa.qa_no_resources import QaNoResourcesTask, qa_no_resources_report_info
from ckanext.qa.qa_stale import QaStaleTask, qa_stale_report_info
from ckanext.qa.qa_schema_issues import QaSchemaIssuesTask, qa_schema_issues_report_info, schema_qa_field_options_helper

log = logging.getLogger(__name__)

tasks = { 'no-resources': QaNoResourcesTask,
          'stale': QaStaleTask,
          'schema-issues': QaSchemaIssuesTask }

reports = [ qa_no_resources_report_info,
            qa_stale_report_info,
            qa_schema_issues_report_info ]

helpers = { 'schema_qa_field_options': schema_qa_field_options_helper,
            'qa_license_options': lambda: [(license[1], license[0]) for license in license_options()] }

def is_sysadmin(user, _):
    return user is not None and user.sysadmin

# Force all reports to be availale only to superadmins
for report in reports:
    report['authorize'] = is_sysadmin
