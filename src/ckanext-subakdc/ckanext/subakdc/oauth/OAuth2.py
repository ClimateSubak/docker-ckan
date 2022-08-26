import logging
import sys

import requests
from requests.exceptions import HTTPError
from flask import redirect, make_response

import ckan.model as model
import ckan.plugins.toolkit as tk

from authlib.integrations.requests_client import OAuth2Session
from authlib.jose import JsonWebToken
from authlib.oidc.core import CodeIDToken


log = logging.getLogger(__name__)

BASE_URL = "https://9bbb-51-148-176-70.eu.ngrok.io"
# TODO regenerate these and move them to env vars
GOOGLE_CLIENT_ID = (
    "1053861686053-2v763h747gc3vrhllr6t1cgvijve5lid.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_ACCESS_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_AUTHORIZE_TOKEN_URI = "https://accounts.google.com/o/oauth2/auth"
# SCOPE = "https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile"
SCOPE = "openid email profile"


class OAuth2:
    def make_client(self):
        return OAuth2Session(
            GOOGLE_CLIENT_ID,
            GOOGLE_CLIENT_SECRET,
            scope=SCOPE,
            redirect_uri=f"{BASE_URL}/oauth/authorize",
        )

    def challenge(self):
        client = self.make_client()
        uri, _ = client.create_authorization_url(GOOGLE_AUTHORIZE_TOKEN_URI)

        return redirect(uri)

    def get_token(self):
        client = self.make_client()

        authorization_response = f"{BASE_URL}{tk.request.full_path}"
        log.debug(authorization_response)

        try:
            token = client.fetch_token(
                GOOGLE_ACCESS_TOKEN_URI, authorization_response=authorization_response
            )
            log.debug(token)

        except HTTPError as e:
            log.debug(e.response.text)

        return token

    def identify(self, token):
        # Get the public keys used to sign id_token JWT in token
        keys_resp = requests.get("https://www.googleapis.com/oauth2/v3/certs")
        keys = keys_resp.json()

        # Decode/validate the id_token
        jwt = JsonWebToken(["RS256"])
        claims = jwt.decode(token["id_token"], keys, claims_cls=CodeIDToken)
        claims.validate()

        user = self.get_or_create_db_user(claims["email"])

        return user

    def get_or_create_db_user(self, email):

        # Find user by email address
        users = model.User.by_email(email)
        if len(users) > 0:
            return users[0]

        # If the user does not exist, we have to create it...
        user = model.User(email=email)

        # TODO Allow user to select username via form
        user.name = "testing"

        # Save user
        model.Session.add(user)
        model.Session.commit()
        model.Session.remove()

        return user

    def remember_user(self, user_name):
        """
        Remember the authenticated identity.
        """
        environ = tk.request.environ
        plugins = environ.get("repoze.who.plugins", {})
        rememberer = plugins.get("auth_tkt")

        identity = {"repoze.who.userid": user_name}
        headers = rememberer.remember(environ, identity)

        response = make_response(tk.redirect_to("home.index"))
        for key, value in headers:
            response.headers[key] = value

        return response
