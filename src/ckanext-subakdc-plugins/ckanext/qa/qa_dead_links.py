from datetime import datetime
import logging
import re

import requests

from ckanext.qa.interfaces import IQaTask, IQaReport
from ckanext.qa.qa_actions import QaHideDatasetsAction

log = logging.getLogger(__name__)

QA_PROPERTY_NAME = "qa_dead_links"
QA_ACTIONS = [ QaHideDatasetsAction ]

def url_is_live(url):
    try:
        # Set to stream=True so that we don't wait for response body, only check the response headers.
        # Timeout reasoning here: https://requests.readthedocs.io/en/latest/user/advanced/#timeouts
        with requests.get(url, stream=True, timeout=3.05) as r:
            r.raise_for_status()
        
        return True
    
    # Catch exception for if any 4XX or 5XX error is thrown or timeout is exceeded
    except requests.exceptions.RequestException as e:
        # log.debug(e)
        return False

def extract_links(text):
    return re.findall(r"(https?://[-a-zA-Z0-9@:%_\+.~#?&/=]+)", text)

def find_dead_links(text):
    dead_links = [] 
    links = extract_links(text)
    for link in links:
        if not url_is_live(link):
            dead_links.append(link)
            
    return dead_links if len(dead_links) > 0 else None


class QaDeadLinksTask(IQaTask):
    qa_property_name = QA_PROPERTY_NAME
    
    @classmethod
    def evaluate(cls, pkg):
        dead_links = {}
        try:
            # Check the source URL
            source = pkg.get("url")
            if source is not None:
                links = find_dead_links(source)
                if links is not None:
                    dead_links["source"] = links
            
            # Check links in the description
            description = pkg["notes"]
            links = find_dead_links(description)
            if links is not None:
                dead_links["description"] = links
            
            # Check the resources URLs
            resources = pkg["resources"]
            res_dead_links = []
            for res in resources:
                links = find_dead_links(res["url"])
                if links is not None:
                    res_dead_links += links
            if len(res_dead_links) > 0:
                dead_links["resources"] = res_dead_links
                
            # Check links in the applications
            apps = pkg.get("subak_data_applications")
            if apps is not None:
                app_dead_links = []
                for app in apps:
                    links = find_dead_links(app["url"])
                    if links is not None:
                        app_dead_links += links
                if len(app_dead_links) > 0:
                    dead_links["applications"] = app_dead_links
            
            upstream_sources = pkg.get("subak_data_sources")
            if upstream_sources is not None:
                links = find_dead_links(upstream_sources)
                if links is not None:
                    dead_links["upstream_sources"] = links

            if len(dead_links.keys()) > 0:
                return { "has_dead_links": True, "dead_links": dead_links }
            else:
                return { "has_dead_links": False }
                    
        except Exception as e:
            log.error(f"Could not evaluate pkg in QaDeadLinksTask: {e}")
            return { "has_dead_links": False }
            
            
class QaDeadLinksReport(IQaReport):
    qa_property_name = QA_PROPERTY_NAME
    qa_actions = QA_ACTIONS
    
    @classmethod
    def generate(cls, page=1):
        action_is_running = cls.run_action()
        
        fq = f'extras_subak_qa:"has_dead_links\\": true"'
        report = cls.build(fq=fq, sort="name asc", action_is_running=action_is_running)
       
        return report

qa_dead_links_report_info = {
    "name": "datasets-with-dead-links",
    "description": f"This report lists datasets that link to sources that no longer exist",
    "option_defaults": None,
    "option_combinations": None,
    "generate": QaDeadLinksReport.generate,
    "template": 'report/qa_dead_links.html'
}