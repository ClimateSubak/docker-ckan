import logging

from flask import Blueprint, render_template
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

# Create Blueprint for plugin
verification_blueprint = Blueprint("verification", __name__)

def verification_view():
    code = tk.request.args.get("code")
    if code is None:
        pass
    
    h.flash_success("Your email address was successfully verified")
    return tk.redirect_to("dashboard.index")

verification_blueprint.add_url_rule(
    "/auth/email-verification",
    "email_verification",
    verification_view,
)

def get_blueprints():
    return [verification_blueprint]
