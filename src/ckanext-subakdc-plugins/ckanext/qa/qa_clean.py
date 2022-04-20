import logging

from ckanext.qa.interfaces import IQaTask, IQaReport
from ckanext.qa.qa_actions import QaCleanDatasetsAction

log = logging.getLogger(__name__)

QA_PROPERTY_NAME = 'qa_clean'
QA_ACTIONS = [QaCleanDatasetsAction]


class QaCleanTask(IQaTask):
    qa_property_name = QA_PROPERTY_NAME

    @classmethod
    def evaluate(cls, pkg):
        return False

        # True if duplicate formats in files, licenses when case is standardised
        # get all tags
        # get all file formats
        # get all licenses

        # try:
        #     for tag in pkg['package_tags']:
        #         if any(char.isupper() for char in tag) or '_' in tag or '-' in tag:
        #             return True
        #     return False
        #
        # except Exception as e:
        #     log.error(f"Could not evaluate pkg in QaSanitiseTask: {e}")
        #     return False


class QaCleanReport(IQaReport):
    qa_property_name = QA_PROPERTY_NAME
    qa_actions = QA_ACTIONS

    @classmethod
    def generate(cls):
        action_is_running = cls.run_action()

        fields = ['id', 'title', 'num_resources']
        return cls.build(fields, action_is_running=action_is_running)

    @classmethod
    def should_show_in_report(cls, value):
        # Only show in report if value is set to true
        if value is None:
            return False
        else:
            return value


qa_clean_report_info = {
    'name': 'datasets-need-sanitising',
    'description': 'Datasets with common formatting errors in tags, licenses, or file formats',
    'option_defaults': None,
    'option_combinations': None,
    'generate': QaCleanReport.generate,
    'template': 'report/qa_clean.html',
}