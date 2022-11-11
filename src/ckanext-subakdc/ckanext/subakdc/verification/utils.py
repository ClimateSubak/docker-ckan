import os
import hashlib
import datetime

import ckan.plugins.toolkit as tk

def generate_verification_code(username):
    """
    Verification code is concatenation of username, secret and current datetime,
    and return as an MD5 encoded hexadecimal string
    """
    secret = os.environ["EMAIL_VERIFICATION_SECRET"]
    
    str_input = f"{username}.{secret}.{datetime.datetime.now()}"
    return hashlib.md5(str_input.encode()).hexdigest()

# TODO
# def check_verification_code(code):
#     return code == tk.current_user.code
