import json
import requests


class JMAPTester:
    def __init__(self, api_uri, **kwargs):
        self.api_uri = api_uri
        self.authentication_uri = kwargs.get("authentication_uri")
        self.download_uri = kwargs.get("download_uri")
        self.upload_uri = kwargs.get("upload_uri")

        self.default_using = kwargs.get("default_using")
        self.default_arguments = kwargs.get("default_arguments")

        self.ua = requests.Session()

        # if we have a username and password, we'll use that to do basic auth
        username = kwargs.get("username")
        password = kwargs.get("password")

        if username and password:
            self.ua.auth = (username, password)

        # filled in later
        self.accounts = None
        self.primary_accounts = None

    def update_client_session(self, auth_uri=None):
        auth_uri = auth_uri or self.authentication_uri

        # XXX better exceptions
        if not auth_uri:
            raise RuntimeError("tried to update client session with no auth_uri")

        auth_res = self.ua.get(auth_uri)
        if auth_res.status_code != 200:
            raise RuntimeError("auth failed")

        self.configure_from_client_session(auth_res.json())

    def configure_from_client_session(self, session):
        # XXX JMAP::Tester does a bunch of other stuff here, largely I think
        # because it was written when authentication was still part of the
        # official spec. I will forgo most of that here.
        for kind in ["api", "authentication", "download", "upload"]:
            val = session.get(kind + "Url")
            if val:
                setattr(self, kind + "_uri", val)

        self.accounts = session["accounts"]
        self.primary_accounts = session["primaryAccounts"]
