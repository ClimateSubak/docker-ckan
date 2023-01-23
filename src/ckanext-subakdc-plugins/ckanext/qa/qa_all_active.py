import logging
from collections import OrderedDict

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
    def generate(cls, org):
        action_is_running = cls.run_action()

        fields = ["id", "title", "organization"]

        report = cls.build(fields, action_is_running=action_is_running)

        if org is not None and org != "":
            report["table"] = list(
                filter(lambda row: cls.filter_by_org(row, org), report["table"])
            )

        report["table"].sort(key=lambda row: row["title"])

        if len(report["table"]) > MAX_REPORT_ROWS_TO_DISPLAY:
            report["table"] = report["table"][0:MAX_REPORT_ROWS_TO_DISPLAY]
            report["data_truncated"] = True

        return report

    @classmethod
    def filter_by_org(cls, row, org):
        return row["organization"]["name"] == org

    @classmethod
    def should_show_in_report(cls, value):
        # This method is not actually evaluated as qa_property_name is None
        return True


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
