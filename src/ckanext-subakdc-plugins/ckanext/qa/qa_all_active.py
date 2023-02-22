import logging
from collections import OrderedDict

from ckan.plugins import toolkit as tk
from ckanext.report import lib

from ckanext.qa.config import MAX_REPORT_ROWS_TO_DISPLAY
from ckanext.qa.interfaces import IQaReport
from ckanext.qa.qa_actions import QaHideDatasetsAction, QaUpdateDatasetsAction

log = logging.getLogger(__name__)

QA_ACTIONS = [QaHideDatasetsAction, QaUpdateDatasetsAction]


class QaAllActiveReport(IQaReport):
    qa_property_name = None
    qa_actions = QA_ACTIONS

    @classmethod
    def generate(cls, org, page=1):
        action_is_running = cls.run_action()

        fields = ["id", "title", "organization"]
        report = cls.build(fields, sort_key=lambda row: row["title"], action_is_running=action_is_running)

        return report

    @classmethod
    def should_show_in_report(cls, pkg):
        options = tk.request.params
        should_show = True
        if "org" in options and options.get("org") is not None and options.get("org") != "" and pkg["organization"]["name"] != options.get("org"):
            should_show = False
        
        return should_show


qa_all_active_report_info = {
    "name": "all-active-datasets",
    "description": f"This report lists all the active datasets in the data catalogue",
    "option_defaults": OrderedDict({"org": None}),
    "option_combinations": lambda: {
        "org": org for org in lib.all_organizations(include_none=True)
    },
    "generate": QaAllActiveReport.generate,
    "template": "report/qa_all_active.html",
}
