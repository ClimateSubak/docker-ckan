import logging

import ckan.plugins as p

import ckanext.security.auth_functions as auth

log = logging.getLogger(__name__)


class SecurityPlugin(p.SingletonPlugin):
    p.implements(p.IAuthFunctions, inherit=True)

    # ------- IAuthFunctions method implementations ------- #
    def get_auth_functions(self):
        auth_functions = {"user_list": auth.user_list, "user_show": auth.user_show}

        return auth_functions
