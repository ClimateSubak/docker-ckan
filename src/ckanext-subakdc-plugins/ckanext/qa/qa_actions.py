import logging

import ckan.plugins.toolkit as tk

from ckanext.qa.interfaces import IQaAction

log = logging.getLogger(__name__)


class QaHideDatasetsAction(IQaAction):
    name = 'hide_datasets'
    form_button_text = 'Hide selected datasets'
    
    @classmethod
    def run(cls, pkg_ids, form_vars):
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
    def run(cls, pkg_ids, form_vars):
        # Get the required API action
        patch_package = tk.get_action('package_patch')
        
        # Get just the fields that need patching
        patch_fields = cls.filter_form_fields(form_vars)
    
        # Loop over all the provided package ids and call patch API action
        for pkg_id in pkg_ids:
            try:
                patch_fields.update({ 'id': pkg_id })
                patch_package({ 'ignore_auth': True, 'user': None }, patch_fields)
            except Exception as e:
                log.error(f"Could not patch package in QaUpdateDatasetsAction.run: {pkg_id}, {e}")
                
    @classmethod
    def filter_form_fields(cls, form_vars):
        # Filter out id and action fields from POST vars
        fields = { field[0]:field[1] for field in filter(lambda field: field[0] != 'id' and not(field[0].startswith('action.')), 
                                                         form_vars.items()) }
        
        # Filter empty fields
        patch_fields = {}
        for key, value in fields.items():
            if value[0] == '' or (key == 'license_id' and value[0] == 'notspecified'):
                continue
                
            patch_fields[key] = value
        
        return patch_fields   


class QaCleanDatasetsAction(IQaAction):
    name = 'sanitise_datasets'
    form_button_text = 'Fix formatting issues for selected datasets'

    @classmethod
    def run(cls, pkg_ids, form_vars):
        package_show = tk.get_action('package_show')
        resource_patch = tk.get_action('resource_patch')

        # Loop over all the provided package ids and call patch API action
        for pkg_id in pkg_ids:
            try:
                package = package_show({ 'ignore_auth': True, 'user': None }, { 'id': pkg_id })
                for resource in package['resources']:
                    # patch the format if it is not a valid format
                    new_format = resource['format'].replace('.', '').upper()
                    resource_patch({ 'ignore_auth': True, 'user': None }, { 'id': resource['id'], 'format': new_format })

            except Exception as e:
                log.error(f"Could not patch package in QaCleanDatasetsAction.run: {pkg_id}, {e}")


class QaDeleteOrgsAction(IQaAction):
    name = 'hide_datasets'
    form_button_text = 'Hide selected datasets'

    @classmethod
    def run(cls, pkg_ids, form_vars):
        # Get the required API action
        delete_package = tk.get_action('package_delete')

        # Loop over all the provided package ids and call delete API action
        # N.B. The CKAN delete package API doesn't actually delete the package,
        # but just sets the state property to 'deleted' in the DB so it no longer
        # shows up via API calls or in the web frontend
        for pkg_id in pkg_ids:
            try:
                delete_package({'ignore_auth': True, 'user': None},
                               {'id': pkg_id})
            except Exception as e:
                log.error(f"Could not patch package in QaHideDatasetsAction.run: {pkg_id}, {e}")
