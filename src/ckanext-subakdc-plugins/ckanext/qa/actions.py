import logging

import ckan.plugins.toolkit as tk

from ckanext.qa import tasks
from ckanext.qa.qa import QaTaskRunner

log = logging.getLogger(__name__)


def run_qa_tasks_on_package(pkg):
    runner = QaTaskRunner(list(tasks.values()))
    func = runner.run_on_single_package
    tk.enqueue_job(func, [pkg.get("id")])    

@tk.chained_action
def package_create(action_func, context, data_dict):
    """
    Intercepts the package_create call and adds starts job to run QA tasks
    """
    pkg = action_func(context, data_dict)            
    
    run_qa_tasks_on_package(pkg)
        
    return pkg

@tk.chained_action
def package_update(action_func, context, data_dict):
    """
    Intercepts the package_update call and adds starts job to run QA tasks
    N.B. this will not intercept package_patch calls and therefore doesn't 
    get caught in loop when package_patch is called when the QA tasks run
    """
    pkg = action_func(context, data_dict)            
    
    # Only run QA tasks if the ignore_qa flag is false or empty
    if not context.get('ignore_qa', False):
        run_qa_tasks_on_package(pkg)
        
    return pkg

