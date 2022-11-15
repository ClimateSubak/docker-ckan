import logging

import ckan.plugins.toolkit as tk

from ckanext.subakdc.verification import NAMESPACE

log = logging.getLogger(__name__)

@tk.chained_auth_function
def package_create(next_auth, context, data_dict=None):   
    user_obj = context.get("auth_user_obj")
    
    if _is_unverified_user(user_obj):
        return {"success": False}
    
    return next_auth(context, data_dict)

@tk.chained_auth_function
def organization_create(next_auth, context, data_dict=None):   
    user_obj = context.get("auth_user_obj")
    
    if _is_unverified_user(user_obj):
        return {"success": False}
    
    return next_auth(context, data_dict)

def _is_unverified_user(user_obj):
    return user_obj.plugin_extras is not None and NAMESPACE in user_obj.plugin_extras and "code" in user_obj.plugin_extras[NAMESPACE] and user_obj.plugin_extras[NAMESPACE]["code"] != None