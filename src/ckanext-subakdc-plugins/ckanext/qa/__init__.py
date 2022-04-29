import logging

from ckan.lib.helpers import license_options

from ckanext.qa.qa_all_active import qa_all_active_report_info
from ckanext.qa.qa_no_resources import QaNoResourcesTask, qa_no_resources_report_info
from ckanext.qa.qa_stale import QaStaleTask, qa_stale_report_info
from ckanext.qa.qa_schema_issues import QaSchemaIssuesTask, qa_schema_issues_report_info, schema_qa_field_options_helper
from ckanext.qa.qa_clean import QaCleanTask, qa_clean_report_info
from ckanext.qa.qa_orphan_orgs import QaOrphanOrgsTask, qa_orphan_orgs_report_info

log = logging.getLogger(__name__)

tasks = { 'no-resources': QaNoResourcesTask,
          'stale': QaStaleTask,
          'schema-issues': QaSchemaIssuesTask,
          'clean': QaCleanTask,
          'orphan-orgs': QaOrphanOrgsTask }

reports = [ qa_all_active_report_info,
            qa_no_resources_report_info,
            qa_stale_report_info,
            qa_schema_issues_report_info,
            qa_clean_report_info,
            qa_orphan_orgs_report_info ]

helpers = { 'schema_qa_field_options': schema_qa_field_options_helper,
            'schema_qa_default_field_option': lambda: list(schema_qa_field_options_helper().keys())[0],
            'qa_license_options': lambda: [(license[1], license[0]) for license in license_options()] }

def is_sysadmin(user, _):
    return user is not None and user.sysadmin

# Force all reports to be available only to super-admins
for report in reports:
    report['authorize'] = is_sysadmin
