from datetime import datetime
import logging
import math

from collections import OrderedDict

from ckanext.qa.interfaces import IQaTask, IQaReport
from ckanext.qa.qa_actions import QaUpdateDatasetsAction

log = logging.getLogger(__name__)

QA_PROPERTY_NAME = 'qa_schema_issues'
QA_ACTIONS = [ QaUpdateDatasetsAction ]
FIELDS = {
    'subak_overview': 'Overview',
    'subak_primary_taxonomy_category': 'Primary taxonomy category',
    'tag_string': 'Keywords',
    'subak_temporal_start': 'Start date',
    'subak_temporal_end': 'End date',
    'subak_temporal_resolution': 'Time resolution',
    'subak_geo_region': 'Geographic region',
    'subak_countries': 'Countries',
    'subak_spatial_resolution': 'Spatial resolution',
    'license_id': 'License',
    'url': 'Source',
    'author': 'Contact',
    'subak_update_frequency': 'Update frequency',
    'subak_data_sources': 'Data sources'
}


class QaSchemaIssuesTask(IQaTask):
    qa_property_name = QA_PROPERTY_NAME
    
    @classmethod
    def evaluate(cls, pkg):
        issues = {}
        
        if pkg.get('subak_overview', '') == '':
            issues['subak_overview'] = 'empty'
            
        if pkg.get('subak_primary_taxonomy_category', '') == '':
            issues['subak_primary_taxonomy_category'] = 'empty'
        
        if len(pkg.get('tags', [])) == 0:
            issues['tag_string'] = 'empty'
        
        # temporal
        if pkg.get('subak_temporal_start', '') == '':
            issues['subak_temporal_start'] = 'empty'
        
        if pkg.get('subak_temporal_end', '') == '':
            issues['subak_temporal_end'] = 'empty'

        if pkg.get('subak_temporal_resolution', '') == '':
            issues['subak_temporal_resolution'] = 'empty'
        
        # spatial
        if pkg.get('subak_geo_region', '') == '':
            issues['subak_geo_region'] = 'empty'
        
        if len(pkg.get('subak_countries', [])) == 0:
            issues['subak_countries'] = 'empty'
        
        if pkg.get('subak_spatial_resolution', '') == '':
            issues['subak_spatial_resolution'] = 'empty'
        
        # other meta
        if pkg.get('license_id', '') == '':
            issues['license_id'] = 'empty'
        
        if pkg.get('url', '') == '':
            issues['url'] = 'empty'
        
        if pkg.get('author', '') == '':
            issues['author'] = 'empty'
            
        if pkg.get('subak_update_frequency', '') == '':
            issues['subak_update_frequency'] = 'empty'
        
        if pkg.get('subak_data_sources', '') == '':
            issues['subak_data_sources'] = 'empty'
            
        if len(issues) == 0:
            return { 'has_issues': False }
        else:
            return { 'has_issues': True, 'issues': issues }
            
            
class QaSchemaIssuesReport(IQaReport):
    qa_property_name = QA_PROPERTY_NAME
    qa_actions = QA_ACTIONS
    
    @classmethod
    def generate(cls, field):
        field = None if field == '' else field
        action_is_running = cls.run_action()
        
        table_fields = ['id', 'title']
        computed_fields = { 'issues': lambda pkg: cls.get_issues(pkg, field) }
       
        report = cls.build(table_fields, computed_fields, action_is_running=action_is_running)
        
        if field is not None:
            report['table'] = list(filter(lambda row: cls.filter_by_field(row, field), report['table']))
        
        return report
    
    @classmethod
    def get_issues(cls, pkg, field):
        try:
            fields = pkg['subak_qa'][QA_PROPERTY_NAME]['issues']
            if field and field in fields:
                return { field: fields[field] }
                
            return fields
        except ValueError:
            return None
        
    @classmethod
    def filter_by_field(cls, row, field):
        return field in row['issues']
    
    @classmethod
    def should_show_in_report(cls, value):
        # Only show in report if value `has_issues` item is set to true
        return value.get('has_issues', False)
    
    
def schema_qa_field_options_helper():
    return FIELDS

qa_schema_issues_report_info = {
    'name': 'schema-issues-datasets',
    'title': 'Datasets with schema issues',
    'description': f"This report highlights datasets where schema attributes are invalid or missing",
    'option_defaults': OrderedDict({'field': None }),
    'option_combinations': lambda: { 'field': FIELDS[field] for field in FIELDS},
    'generate': QaSchemaIssuesReport.generate,
    'template': 'report/qa_schema_issues.html'
}
