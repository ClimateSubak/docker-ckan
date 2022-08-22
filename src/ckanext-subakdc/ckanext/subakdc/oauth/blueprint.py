import logging

from flask import Blueprint, render_template, request
import ckan.plugins.toolkit as tk

from ckanext.subakdc.oauth.OAuthClient import login, authorize

log = logging.getLogger(__name__)

# Create Blueprint for plugin
oauth = Blueprint("oauth", __name__)


def login_view():
    return login()


def authorize_view():
    log.debug("authorised")
    log.debug(tk.request)
    email, name = authorize()
    # return tk.redirect_to("home.index")
    return f"<p>{email}</p><p>{name}</p>"


oauth.add_url_rule(
    "/oauth/login",
    "login",
    login_view,
)

oauth.add_url_rule(
    "/oauth/authorize",
    "authorize",
    authorize_view,
)


def get_blueprints():
    return [oauth]
