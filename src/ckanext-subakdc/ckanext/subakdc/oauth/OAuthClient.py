import logging
import sys

import requests
from requests.exceptions import HTTPError
from flask import redirect

import ckan.plugins.toolkit as tk

from authlib.integrations.requests_client import OAuth2Session
from authlib.jose import JsonWebToken
from authlib.oidc.core import CodeIDToken


# authlog = logging.getLogger("authlib")
# authlog.addHandler(logging.StreamHandler(sys.stdout))
# authlog.setLevel(logging.DEBUG)

log = logging.getLogger(__name__)

# TODO regenerate these and move them to env vars
GOOGLE_CLIENT_ID = (
    "1053861686053-2v763h747gc3vrhllr6t1cgvijve5lid.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_ACCESS_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_AUTHORIZE_TOKEN_URI = "https://accounts.google.com/o/oauth2/auth"
# SCOPE = "https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile"
SCOPE = "openid email profile"

oauth_client = OAuth2Session(
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    scope=SCOPE,
    redirect_uri="https://dcd5-51-148-176-70.eu.ngrok.io/oauth/authorize",
)


def login():
    uri, state = oauth_client.create_authorization_url(GOOGLE_AUTHORIZE_TOKEN_URI)
    return redirect(uri)


def identify():
    pass


def authorize():
    authorization_response = (
        "https://dcd5-51-148-176-70.eu.ngrok.io" + tk.request.full_path
    )
    log.debug(authorization_response)
    try:
        token = oauth_client.fetch_token(
            GOOGLE_ACCESS_TOKEN_URI, authorization_response=authorization_response
        )
        log.debug(token)

        # Get the public keys used to sign id_token JWT in token
        keys_resp = requests.get("https://www.googleapis.com/oauth2/v3/certs")
        keys = keys_resp.json()

        # Decode/validate the id_token
        jwt = JsonWebToken(["RS256"])
        claims = jwt.decode(token["id_token"], keys, claims_cls=CodeIDToken)
        claims.validate()

        # Can now access info from oauth provider
        return claims["email"], claims["name"]

    except HTTPError as e:
        log.debug(e.response.text)


def logout():
    # Necessary?
    # session.pop('user', None)
    return tk.redirect("home")
