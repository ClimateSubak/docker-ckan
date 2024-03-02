import logging
import os
import sys

import requests

from flask import redirect, make_response

from ckan.logic.schema import validator_args
import ckan.model as model
import ckan.plugins.toolkit as tk

from authlib.integrations.requests_client import OAuth2Session
from authlib.jose import JsonWebToken
from authlib.oidc.core import CodeIDToken


log = logging.getLogger(__name__)

# BASE_URL = "https://bac4-51-148-176-70.eu.ngrok.io" # For local testing, use ngrok
BASE_URL = os.environ.get("CKAN_SITE_URL")

class OAuth2:
    def make_client(self, provider):
        if provider == "microsoft":
            client_id = os.environ.get("MICROSOFT_OAUTH_CLIENT_ID")
            client_secret = os.environ.get("MICROSOFT_OAUTH_CLIENT_SECRET")
        else:
            client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
            client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        
        return OAuth2Session(
            client_id,
            client_secret,
            scope="openid email profile",
            redirect_uri=f"{BASE_URL}/oauth/authorize?provider={provider}",
        )

    def challenge(self, provider):
        client = self.make_client(provider)

        if provider == "microsoft":
            provider_auth_uri = "https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize"
        else:
            provider_auth_uri = "https://accounts.google.com/o/oauth2/auth"
            
        uri, _ = client.create_authorization_url(provider_auth_uri)

        return redirect(uri)

    def get_token(self, provider):
        client = self.make_client(provider)

        authorization_response = f"{BASE_URL}{tk.request.full_path}"
        # log.debug(authorization_response)
        
        if provider == "microsoft":
            access_token_uri = f"https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
        else:
            access_token_uri = "https://oauth2.googleapis.com/token"

        try:
            token = client.fetch_token(
                access_token_uri, authorization_response=authorization_response
            )
            # log.debug(token)
        except:
            return None

        return token
    
    def get_token_user_email(self, provider, token):
        # Decode/validate the id_token
        jwt = JsonWebToken(["RS256"])
        
        try:
            # Get the public keys used to sign id_token JWT in token
            if provider == "microsoft":
                keys_resp = requests.get("https://login.microsoftonline.com/common/discovery/v2.0/keys")
            else: # Google
                keys_resp = requests.get("https://www.googleapis.com/oauth2/v3/certs")
            
            keys = keys_resp.json()
            claims = jwt.decode(token["id_token"], keys, claims_cls=CodeIDToken)
            claims.validate()
            # log.debug(claims)
        except:
            return None

        return claims["email"]

    def get_user(self, email):
        # Find user by email address
        users = model.User.by_email(email)
        if len(users) > 0:
            return users[0]
        
        return None
    
    def create_user(self, email, username):
        user_create = tk.get_action("user_create")
        schema = custom_user_schema()
        
        # Disallow user creation        
        return None
        
        # try:
        #     user = user_create({"ignore_auth": True, "user": None, "schema": schema}, 
        #                        {"email": email, "name": username})
        # except Exception as e:
        #     # log.debug(e)
        #     return None
        
        # return user

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


@validator_args
def custom_user_schema(unicode_safe, name_validator, user_name_validator, 
                       email_is_unique, not_empty, email_validator):
    return {'name': [not_empty, name_validator, user_name_validator, unicode_safe],
            'email': [not_empty, email_validator, email_is_unique, unicode_safe]}
