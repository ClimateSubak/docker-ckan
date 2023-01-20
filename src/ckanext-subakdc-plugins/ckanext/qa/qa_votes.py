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
    def generate(cls, order):
        action_is_running = cls.run_action()
        
        fields = ["id", "title", "organization"]
        computed_fields = {"votes": lambda pkg: cls.get_num_votes(pkg)}
        report = cls.build(fields, computed_fields,
                           action_is_running=action_is_running)
        
        report['table'].sort(key=lambda row: row["votes"], 
                             reverse=(order == 'desc'))
        
        if len(report["table"]) > MAX_REPORT_ROWS_TO_DISPLAY:
            report["table"] = report["table"][0:MAX_REPORT_ROWS_TO_DISPLAY]
            report["data_truncated"] = True
            
        return report
    
    @classmethod
    def get_num_votes(cls, pkg):
        if "subak_votes" in pkg:
            return int(pkg['subak_votes'], 10)
        
        return 0
    
    @classmethod
    def should_show_in_report(cls, value):
        # This method is not actually evaluated as qa_property_name is None
        return True

qa_votes_report_info = {
    'name': 'datasets-by-votes',
    'description': 'Most upvoted/downvoted datasets',
    "option_defaults": OrderedDict({"order": 'asc'}),
    "option_combinations": {"order": ['asc', 'desc']},
    'generate': QaVotesReport.generate,
    'template': 'report/qa_votes.html',
}