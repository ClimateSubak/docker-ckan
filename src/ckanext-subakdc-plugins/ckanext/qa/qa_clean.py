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
        """
        True if duplicate formats in files, licenses when case is standardised
        """

        # get all file formats
        # get all licenses

        try:
            # sample tag
            # tag: {'display_name': 'subscribable', 'id': '74a4934d-c5a9-4d41-809e-fca05c156cdc', 'name': 'subscribable', 'state': 'active', 'vocabulary_id': None}

            formats = []

            # file format
            for resource in pkg["resources"]:
                formats_to_clean = ["web-optimised PDF"]
                if resource["format"] in formats_to_clean:
                    formats.append(resource["format"])
                if "." in resource["format"]:
                    formats.append(resource["format"])

            # License
            # TODO standardise license

            if len(formats) > 0:
                return True
            return False

        except Exception as e:
            log.error(f"Could not evaluate pkg in QaCleanTask: {e}")
            return False


class QaCleanReport(IQaReport):
    qa_property_name = QA_PROPERTY_NAME
    qa_actions = QA_ACTIONS

    @classmethod
    def generate(cls):
        action_is_running = cls.run_action()

        fields = ['id', 'title', 'num_resources']
        report =  cls.build(fields, action_is_running=action_is_running)
        
        report['table'].sort(key=lambda row: row['title'])
        return report

    @classmethod
    def should_show_in_report(cls, value):
        # Only show in report if value is set to true
        if value is False:
            return False
        else:
            return True


qa_clean_report_info = {
    'name': 'datasets-need-cleaning',
    'description': 'Datasets with common formatting errors in tags, licenses, or file formats',
    'option_defaults': None,
    'option_combinations': None,
    'generate': QaCleanReport.generate,
    'template': 'report/qa_clean.html',
}