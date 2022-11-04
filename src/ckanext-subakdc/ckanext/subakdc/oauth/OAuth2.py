import logging
import os
import sys

import requests
from requests.exceptions import HTTPError
from flask import redirect, make_response
from sqlalchemy.exc import IntegrityError

import ckan.model as model
import ckan.plugins.toolkit as tk

from authlib.integrations.requests_client import OAuth2Session
from authlib.jose import JsonWebToken
from authlib.oidc.core import CodeIDToken


log = logging.getLogger(__name__)

# TODO read from CKAN_SITE_URL rather than hardcoded ngrok url
BASE_URL = "https://17ef-82-163-125-51.eu.ngrok.io"
# BASE_URL = os.environ.get("CKAN_SITE_URL")


GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_ACCESS_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_AUTHORIZE_TOKEN_URI = "https://accounts.google.com/o/oauth2/auth"
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

    def identify(self, token, username=None):
        # Get the public keys used to sign id_token JWT in token
        keys_resp = requests.get("https://www.googleapis.com/oauth2/v3/certs")
        keys = keys_resp.json()

        # Decode/validate the id_token
        jwt = JsonWebToken(["RS256"])
        claims = jwt.decode(token["id_token"], keys, claims_cls=CodeIDToken)
        claims.validate()
        
        log.debug(claims)

        user = self.get_user(claims["email"])
        log.debug(user)
        
        if user is None and username is not None:
            user = self.create_user(claims['email'], username)

        return user

    def get_user(self, email):
        # Find user by email address
        users = model.User.by_email(email)
        if len(users) > 0:
            return users[0]
        
        return None
    
    def create_user(self, email, username):
        try:
            user = model.User(email=email)

            user.name = username

            # Save user
            model.Session.add(user)
            model.Session.commit()
            model.Session.remove()
        except IntegrityError as e:
            return None
        
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

        response = make_response(tk.redirect_to("dashboard.index"))
        for key, value in headers:
            response.headers[key] = value

        return response
