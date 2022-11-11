import os
import codecs

def generate_verification_code():
    """
    Verification code is a randomly generated hexadecimal string
    """
    return codecs.encode(os.urandom(16), 'hex').decode('utf-8')
