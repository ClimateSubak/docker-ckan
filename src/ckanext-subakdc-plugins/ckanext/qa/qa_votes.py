import logging
from collections import OrderedDict

from ckanext.qa.config import MAX_REPORT_ROWS_TO_DISPLAY
from ckanext.qa.interfaces import IQaReport
from ckanext.qa.qa_actions import QaHideDatasetsAction

log = logging.getLogger(__name__)

QA_ACTIONS = [ QaHideDatasetsAction ]


class QaVotesReport(IQaReport):
    qa_property_name = None
    qa_actions = QA_ACTIONS
    
    @classmethod
    def generate(cls, order='asc', page=1):
        action_is_running = cls.run_action()
        
        # computed_fields = {"votes": lambda pkg: cls.get_num_votes(pkg)}
        report = cls.build(sort=f'subak_votes {order}, name asc', action_is_running=action_is_running)
            
        return report


qa_votes_report_info = {
    'name': 'datasets-by-votes',
    'description': 'Most upvoted/downvoted datasets',
    "option_defaults": OrderedDict({"order": 'asc'}),
    "option_combinations": {"order": ['asc', 'desc']},
    'generate': QaVotesReport.generate,
    'template': 'report/qa_votes.html',
}