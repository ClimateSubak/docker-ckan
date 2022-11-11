import copy

from ckan import model
import ckan.plugins.toolkit as tk

from ckanext.subakdc.verification.utils import generate_verification_code

NAMESPACE = "verification"

@tk.chained_action
def user_create(action_func, context, data_dict):
    """
    Intercepts the user_create call and adds an email verification code into the
    plugin_extras field on the user model
    """
    user = action_func(context, data_dict)
    user_obj = _get_user_obj(context)
    
    plugin_extras = _init_plugin_extras(user_obj.plugin_extras)
    plugin_extras[NAMESPACE]['code'] = generate_verification_code(user_obj.name)
    user_obj.plugin_extras = plugin_extras

    if not context.get('defer_commit'):
        user_model = context.get('model', model)
        user_model.Session.commit()
        
    user['verification_code'] = plugin_extras[NAMESPACE]['code']
        
    return user

def _get_user_obj(context):
    if 'user_obj' in context:
        return context['user_obj']
    
    user = context.get('user')
    m = context.get('model', model)
    user_obj = m.User.get(user)
    if not user_obj:
        raise tk.ObjectNotFound("User not found")
    
    return user_obj

def _init_plugin_extras(plugin_extras):
    out_dict = copy.deepcopy(plugin_extras)
    if not out_dict:
        out_dict = {}
    if NAMESPACE not in out_dict:
        out_dict[NAMESPACE] = {}
    
    return out_dict