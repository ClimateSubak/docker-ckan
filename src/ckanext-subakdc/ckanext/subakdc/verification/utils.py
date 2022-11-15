import os
import codecs

import ckan.lib.helpers as h
from ckan.lib.mailer import MailerException
import ckan.plugins.toolkit as tk

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