import logging

from flask import Blueprint
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

# Create Blueprint for plugin
verification_blueprint = Blueprint("verification", __name__)

def verification_view(code=None):
    # If user not logged in, send to login first
    if not tk.g.user:
        return tk.redirect_to("user.login", came_from=tk.url_for("verification.email_verification", code=code))
    
    stored_code = tk.g.userobj.plugin_extras['verification']['code']
    if code != stored_code:
        h.flash_error(f"Your email address could not be verified. Please enure you use the link that was sent to your email address: {tk.g.userobj.email}")
        return tk.redirect_to("dashboard.index")
    
    user_update = tk.get_action('user_update')
    user_update({"ignore_auth": True}, {"id": tk.g.user, "email_verification_code": None})
    h.flash_success("Your email address was successfully verified")
    return tk.redirect_to("dashboard.index")

verification_blueprint.add_url_rule(
    "/auth/email-verification/<string:code>",
    "email_verification",
    verification_view,
)

def get_blueprints():
    return [verification_blueprint]
