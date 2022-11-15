import copy
import logging

from ckan import model
import ckan.lib.helpers as h
from ckan.lib.mailer import MailerException
import ckan.plugins.toolkit as tk

from ckanext.subakdc.verification import NAMESPACE
from ckanext.subakdc.verification.utils import generate_verification_code

log = logging.getLogger(__name__)

@tk.chained_action
def user_create(action_func, context, data_dict):
    """
    Intercepts the user_create call and adds an email verification code into the
    plugin_extras field on the user model
    """
    user = action_func(context, data_dict)
    user_obj = _get_user_obj(context)
    
    plugin_extras = _init_plugin_extras(user_obj.plugin_extras)
    plugin_extras[NAMESPACE]['code'] = generate_verification_code()
    user_obj.plugin_extras = plugin_extras

    if not context.get('defer_commit'):
        user_model = context.get('model', model)
        user_model.Session.commit()
            
    _send_verification_email(user_obj, plugin_extras[NAMESPACE]['code'])
    
    return user

@tk.chained_action
def user_update(action_func, context, data_dict):
    """
    Intercepts the user_update call to update/clear email verification code if necessary
    """
    user_id = tk.get_or_bust(data_dict, 'id')
    user_model = context.get('model', model)
    user_obj = user_model.User.get(user_id)

    if user_obj is not None and "email_verification_code" in data_dict:
        code = data_dict['email_verification_code']
        data_dict = tk.get_action("user_show")(context.copy(), {"id": user_id})
        plugin_extras = _init_plugin_extras(user_obj.plugin_extras)
        plugin_extras[NAMESPACE]['code'] = code
        data_dict["plugin_extras"] = plugin_extras

    return action_func(context, data_dict)

def _send_verification_email(user, code):
    site_name = tk.config.get('ckan.site_title')
    verify_link = tk.url_for("verification.email_verification", code=code, _external=True)
    body = tk.render('emails/verify_user.txt', {"site_name": site_name, "user_name": user.name, "verify_link": verify_link})
    try:
        tk.mail_recipient(user.name, 
                        user.email, 
                        subject=f"Verify your email for {site_name}",
                        body=body)
        h.flash_notice(f"Please follow the confirmation link sent to your email address ({user.email}) to fully activate your account")
    except MailerException:
        h.flash_error(f"We could not send a confirmation link to your email address to activate your account. Please get in touch with the {site_name} team to resolve this issue")

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