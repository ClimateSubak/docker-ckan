import ckan.plugins.toolkit as tk

from ckanext.subakdc.verification.auth import _is_unverified_user

def user_unverified():    
    return _is_unverified_user(tk.g.userobj)