import codecs
import logging
import os

import ckan.lib.helpers as h
from ckan.lib.mailer import MailerException
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

def generate_verification_code():
    """
    Verification code is a randomly generated hexadecimal string
    """
    return codecs.encode(os.urandom(16), 'hex').decode('utf-8')

def send_verification_email(user, code):
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
        
def send_sysadmin_notification_email(user):
    site_name = tk.config.get('ckan.site_title')
    sysadmin_name = os.environ.get('CKAN_SYSADMIN_NAME')
    sysadmin_email = os.environ.get('CKAN_SYSADMIN_EMAIL')
    body = tk.render('emails/sysadmin_new_user_notify.txt', {"site_name": site_name, "user_name": user.name, "user_email": user.email})
    try:
        tk.mail_recipient(sysadmin_name, sysadmin_email, 
                          subject=f"New user sign-up on {site_name}",
                          body=body)
    except:
        log.error(f"Could not send sysadmin new user notification email for user: {user.name}")