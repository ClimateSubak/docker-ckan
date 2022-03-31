import logging

import ckan.plugins.toolkit as tk

from ckanext.qa.interfaces import IQaAction

log = logging.getLogger(__name__)


class QaHideDatasetsAction(IQaAction):
    name = 'hide_datasets'
    form_button_text = 'Hide selected datasets'
    
    @classmethod
    def run(cls, pkg_ids):
        # Get the required API action
        delete_package = tk.get_action('package_delete')    
        
        # Loop over all the provided package ids and call delete API action 
        # N.B. The CKAN delete package API doesn't actually delete the package,
        # but just sets the state property to 'deleted' in the DB so it no longer
        # shows up via API calls or in the web frontend
        for pkg_id in pkg_ids:
            try:
                delete_package({ 'ignore_auth': True, 'user': None }, 
                               { 'id': pkg_id })
            except Exception as e:
                log.error(f"Could not patch package in QaHideDatasetsAction.run: {pkg_id}, {e}")


class QaUpdateDatasetsAction(IQaAction):
    name = 'update_datasets'
    form_button_text = 'Update selected datasets'
    snippet = 'report/snippets/qa-update-action.html'
    
    @classmethod
    def run(cls, pkg_ids):
        log.debug(tk.request.form)
        # # Get the required API action
        # patch_package = tk.get_action('package_patch')    
        
        # # Loop over all the provided package ids and call patch API action 
        # for pkg_id in pkg_ids:
        #     try:
        #         patch_fields = patch_fields.update({ 'id': pkg_id })
        #         patch_package({ 'ignore_auth': True, 'user': None }, patch_fields)
        #     except Exception as e:
        #         log.error(f"Could not patch package in QaUpdateDatasetsAction.run: {pkg_id}, {e}")
