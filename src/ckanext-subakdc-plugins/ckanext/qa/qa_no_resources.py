import logging

from ckanext.qa.interfaces import IQaTask, IQaReport
from ckanext.qa.qa_actions import QaHideDatasetsAction

log = logging.getLogger(__name__)

QA_PROPERTY_NAME = 'qa_no_resources'
QA_ACTIONS = [ QaHideDatasetsAction ]


class QaNoResourcesTask(IQaTask):
    qa_property_name = QA_PROPERTY_NAME
    
    @classmethod
    def evaluate(cls, pkg):
        # True if no resources, False if 1 or more resources
        try:
            return len(pkg['resources']) == 0
        except Exception as e:
            log.error(f"Could not evaluate pkg in QaNoResourcesTask: {e}")
            return False
            
            
class QaNoResourcesReport(IQaReport):
    qa_property_name = QA_PROPERTY_NAME
    qa_actions = QA_ACTIONS
    
    @classmethod
    def generate(cls, page=1):
        action_is_running = cls.run_action()
        
        fq = f'extras_subak_qa:"qa_no_resources\\": true"'
        report = cls.build(fq=fq, sort="name asc", action_is_running=action_is_running)
        
        return report

qa_no_resources_report_info = {
    'name': 'datasets-with-no-resources',
    'description': 'Datasets with no resources',
    'option_defaults': None,
    'option_combinations': None,
    'generate': QaNoResourcesReport.generate,
    'template': 'report/qa_no_resources.html',
}