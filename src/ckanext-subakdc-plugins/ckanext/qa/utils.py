import logging

import ckan.plugins.toolkit as tk

from ckanext.qa.config import MAX_REPORT_ROWS_TO_DISPLAY

log = logging.getLogger(__name__)
    
def get_all_pkgs():
    """
    Calls the CKAN API and returns all the packages in the database
    along with the associated resources
    """
    get_packages = tk.get_action('current_package_list_with_resources')
    
    # Query the API using cursor to find all packages
    page = 0
    all_pkgs = []
    while (True):
        pkgs = get_packages({ 'ignore_auth': True, 'user': None }, 
                            { 'limit': 100, 'offset': page*100 })
        if len(pkgs) > 0:
            all_pkgs = all_pkgs + pkgs
            page += 1
        else:
            break
        
    return all_pkgs

def search_pkgs(fq=None, sort=None, page=1):
    """
    Calls the CKAN API and returns all the packages in the database
    along with the associated resources
    """
    package_search = tk.get_action('package_search')
    pkgs = package_search({ 'ignore_auth': True, 'user': None }, 
                          { 'rows': MAX_REPORT_ROWS_TO_DISPLAY, 
                            'start': (page - 1)*MAX_REPORT_ROWS_TO_DISPLAY,
                            'fq': '' if fq is None else fq,
                            'sort': 'score desc' if sort is None else sort })
    
    return pkgs['results'], pkgs['count']

def get_qa_properties(pkg):
    """
    Read, decode and return the JSON qa dict on the package model
    """
    qa = {}
    if 'subak_qa' in pkg and pkg['subak_qa'] is not None:
        qa = pkg['subak_qa']
        
    return qa
