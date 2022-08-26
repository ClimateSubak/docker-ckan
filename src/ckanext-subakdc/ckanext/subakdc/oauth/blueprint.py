import logging

from flask import Blueprint
import ckan.plugins.toolkit as tk

from ckanext.subakdc.oauth.OAuth2 import OAuth2

log = logging.getLogger(__name__)

oauth = OAuth2()

# Create Blueprint for plugin
oauth_blueprint = Blueprint("oauth", __name__)


def login_view():
    return oauth.challenge()


def authorize_view():
    # TODO error handling
    # try:
    # log.debug(tk.request)
    token = oauth.get_token()
    user = oauth.identify(token)
    response = oauth.remember_user(user.name)
    # except:
    #     pass

    return response


oauth_blueprint.add_url_rule(
    "/oauth/login",
    "login",
    login_view,
)

oauth_blueprint.add_url_rule(
    "/oauth/authorize",
    "authorize",
    authorize_view,
)


def get_blueprints():
    return [oauth_blueprint]
