import logging

from ckanext.qa.interfaces import IQaTask, IQaReport
from ckanext.qa.qa_actions import QaDeleteOrgsAction
from ckanext.qa.utils import get_all_orgs

log = logging.getLogger(__name__)

QA_PROPERTY_NAME = 'qa_orphan_orgs'
QA_ACTIONS = [QaDeleteOrgsAction]


class QaOrphanOrgsTask(IQaTask):
    qa_property_name = QA_PROPERTY_NAME

    @classmethod
    def evaluate(cls, pkg):
        # True if no resources, False if 1 or more resources
        try:
            return len(pkg['resources']) == 0
        except Exception as e:
            log.error(f"Could not evaluate pkg in QaOrphanOrgsTask: {e}")
            return False


class QaOrphanOrgsReport(IQaReport):
    qa_property_name = QA_PROPERTY_NAME
    qa_actions = QA_ACTIONS

    @classmethod
    def generate(cls):
        action_is_running = cls.run_action()

        report = cls.build(action_is_running=action_is_running)

        report['table'].sort(key=lambda row: row['name'])
        return report

    @classmethod
    def should_show_in_report(cls, value):
        # Only show in report if value is set to true
        if value is None:
            return False
        else:
            return value

    @classmethod
    def build(cls, action_is_running=False):

        orgs = get_all_orgs()

        report = {
            'title': 'Orphan Orgs',
            'table': [],
            'action_is_running': action_is_running,
        }


        return report


qa_orphan_orgs_report_info = {
    'name': 'orgs-with-no-datasets-or-users',
    'description': 'Organisations with no datasets or users',
    'option_defaults': None,
    'option_combinations': None,
    'generate': QaOrphanOrgsReport.generate,
    'template': 'report/qa_orphan_orgs.html',
}