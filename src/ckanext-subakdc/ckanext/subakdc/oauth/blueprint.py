import logging

from flask import Blueprint, render_template, request
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk

from ckanext.subakdc.oauth.OAuth2 import OAuth2

log = logging.getLogger(__name__)

oauth = OAuth2()

# Create Blueprint for plugin
oauth_blueprint = Blueprint("oauth", __name__)


def login_view():
    provider = request.args.get("provider", "google")
    return oauth.challenge(provider)

def authorize_view():
    provider = request.args.get("provider", "google")
    
    token = oauth.get_token(provider)
    if token is None:
        return abort_login()
    
    email = oauth.get_token_user_email(provider, token)
    if email is None:
        return abort_login()
    
    user = oauth.get_user(email)
    if user is None:
        return choose_username_view(provider=provider, auth_token=token['id_token'])
    
    response = oauth.remember_user(user.name)
    return response

def choose_username_view(provider, auth_token=None, data=None, error_summary=None):
    data = data or {}
    error_summary = error_summary or {}
    vars = {"data": data, "provider": provider, "auth_token": auth_token, "error_summary": error_summary}
    
    return render_template("user/choose_username.html", **vars)

def submit_username_view():
    username = request.form.get('username')
    provider = request.form.get('provider')
    token = request.form.get('auth_token')
    error_summary = None
    
    if not token:
        error_summary = {"auth_token": "Something went wrong, please contact the data catalogue administrator"}
    elif not username:
        error_summary = {"username": "Your username must not be empty"}
    else:
        email = oauth.get_token_user_email(provider, {"id_token": token})
        if email is None:
            return abort_login()
        
        user = oauth.create_user(email, username)
        if user is None:
            error_summary = {"username": "That username already exists, please choose a different username"}
    
    if error_summary:
        data = {"username": username}
        return choose_username_view(provider=provider, auth_token=token, data=data, error_summary=error_summary)
    
    response = oauth.remember_user(user["name"])
    return response

def abort_login():
    h.flash_error("Sorry, we could not log you in using your chosen login provider.")
    return tk.redirect_to('user.login')

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

oauth_blueprint.add_url_rule(
    "/oauth/choose-username",
    "choose_username",
    choose_username_view,
)

oauth_blueprint.add_url_rule(
    "/oauth/submit-username",
    "submit_username",
    submit_username_view,
    methods=["POST"]
)


def get_blueprints():
    return [oauth_blueprint]
