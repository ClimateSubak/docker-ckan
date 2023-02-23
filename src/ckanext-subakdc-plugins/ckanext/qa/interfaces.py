from abc import ABC, abstractmethod
import logging
import math

import ckan.plugins.toolkit as tk

from ckanext.qa.config import MAX_REPORT_ROWS_TO_DISPLAY
from ckanext.qa.utils import get_all_pkgs

log = logging.getLogger(__name__)


class IQaTask(ABC):
    """
    A task that operates over all or a subset of entities and produces a QA property for each entity e.g. A “broken links” task to test all links associated with a dataset
    """

    qa_property_name = ""
    qa_actions = []

    @classmethod
    @abstractmethod
    def evaluate(cls, pkg):
        """
        Runs an evaluation over the entity and sets the QA property based on the result
        """
        pass


class IQaReport(ABC):
    """
    A tabular report generated with the ckanext-report plugin that gathers the QA property for all entities for a
    given QA task. e.g. Details a summary of all entities with 'Broken links'
    """

    qa_property_name = ""
    qa_actions = []

    @classmethod
    def get_qa_actions(cls):
        return [action.get_action() for action in cls.qa_actions]
    
    @classmethod
    def iter_pages(cls, page, pages):
        num_page_to_display = 10
        mid_point = num_page_to_display // 2
        if page < mid_point:
            return list(range(min(pages+1, num_page_to_display)))
        elif page > pages - mid_point:
            return list(range(pages-num_page_to_display+1, pages+1))
        else:
            return list(range(page-mid_point, page+mid_point))

    @classmethod
    def build(
        cls, fields=None, computed_fields=None, sort_key=None, sort_reverse=False, action_is_running=False, limit=500
    ):
        """
        Builds the report table

        Args:
            fields (list, optional): The fields within each pkg to display in the report. Defaults to None.
            computed_fields (dict, optional): Extra fields that are computed when the report is run - dict key is field title/label, dict value is callable (which is passed a pkg dict). Defaults to None.
            action_is_running (boolean, optional): Indicates whether an action is running in the background which will affect the results of this report

        Returns:
            dict: report table dict
        """
        page = int(tk.request.args.get("page", 1))
        assert page > 0, "Page number must be great than 0"
        
        # TODO this is quite inefficient, but is much simpler
        # than building custom DB queries for each report.
        pkgs = get_all_pkgs()
        n_pkgs = len(pkgs)

        # Build report table detailing packages with no resources
        report_table = []
        if fields is None:
            fields = ["id", "title"]

        for pkg in pkgs:
            if (cls.qa_property_name is None or ("subak_qa" in pkg and cls.qa_property_name in pkg["subak_qa"])) and cls.should_show_in_report(pkg):
                report_fields = {k: pkg[k] for k in fields}
                if computed_fields is not None:
                    for title, field in computed_fields.items():
                        report_fields[title] = field(pkg)

                report_table.append(report_fields)
        
        if sort_key is not None:
            report_table.sort(key=sort_key, reverse=sort_reverse)
        
        n_rows = len(report_table)
        report_table = report_table[(page-1)*MAX_REPORT_ROWS_TO_DISPLAY:page*MAX_REPORT_ROWS_TO_DISPLAY]
        pages = math.ceil(n_rows / MAX_REPORT_ROWS_TO_DISPLAY)

        return {
            "table": list(report_table),
            "pagination": {
                "page": page,
                "per_page": MAX_REPORT_ROWS_TO_DISPLAY,
                "pages": pages,
                "has_prev": page > 1,
                "has_next": page < pages,
                "prev_num": page - 1, 
                "next_num": page + 1,
                "iter_pages": cls.iter_pages(page, pages)
            },
            "n_rows": n_rows,
            "n_packages": n_pkgs,
            "qa_actions": cls.get_qa_actions(),
            "action_is_running": action_is_running,
        }

    @classmethod
    def run_action(cls):
        """
        Determine which QA action to run based on the button that was clicked in the
        report and run the QA action as a background job. This should be called by
        the generate method in this class before building the report table.
        """
        actions = list(filter(lambda item: item.startswith("action."), tk.request.form))
        if len(actions) == 0:
            return False

        pkg_ids = tk.request.form.getlist("id")
        if len(pkg_ids) == 0:
            return False

        action_name = actions[0].split(".", 1)[1]
        for action in cls.qa_actions:
            if action.name == action_name:
                action.run_job(pkg_ids, form_vars=tk.request.form.to_dict(flat=False))
                return True

    @classmethod
    @abstractmethod
    def generate(cls, page=1):
        """
        This method gets called from ckanext-report when generting report.
        It should define some fields and call cls.build
        """
        pass

    @classmethod
    @abstractmethod
    def should_show_in_report(cls, value):
        """
        Evaluate value against some condition and return True if item should show
        in the report, False if not
        """
        pass


class IQaAction(ABC):
    """
    An action that can be taken using information in the QA report to modify the
    entities for a given QA task. e.g. Remove the links, or mark the datasets as
    'stale'. A QA action should also be able to be run from the command line as
    a CKAN command
    """

    name = ""
    form_button_text = ""
    snippet = None

    @classmethod
    def get_action(cls):
        """
        Returns a dict of the name and form_button_text to be used in the report
        template
        """
        action = {
            "name": f"action.{cls.name}",
            "form_button_text": cls.form_button_text,
        }

        if cls.snippet is not None:
            action["snippet"] = cls.snippet

        return action

    @classmethod
    def run_job(cls, pkg_ids, form_vars):
        func = cls.run
        tk.enqueue_job(func, [pkg_ids, form_vars], rq_kwargs={"timeout": 3600})

    @classmethod
    @abstractmethod
    def run(cls, pkg_ids, form_vars):
        """
        Runs an action over the pkg_ids (e.g. deleting all packages in the list)
        """
        pass
