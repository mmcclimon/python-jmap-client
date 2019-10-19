import json
import requests

import jmap_client as jc
import jmap_client.response
import jmap_client.result
from jmap_client.exceptions import ConfigurationError


class JMAPClient:
    def __init__(self, api_uri, **kwargs):
        self.api_uri = api_uri
        self.authentication_uri = kwargs.get("authentication_uri")
        self.download_uri = kwargs.get("download_uri")
        self.upload_uri = kwargs.get("upload_uri")

        self.default_using = kwargs.get("default_using")
        self.default_arguments = kwargs.get("default_arguments", {})

        self.ua = requests.Session()
        self.ua.headers = {"Content-Type": "application/json"}

        # if we have a username and password, we'll use that to do basic auth
        username = kwargs.get("username")
        password = kwargs.get("password")

        if username and password:
            self.ua.auth = (username, password)

        # filled in later
        self.accounts = None
        self.primary_accounts = None

    def update_session(self, auth_uri=None):
        auth_uri = auth_uri or self.authentication_uri

        if not auth_uri:
            raise ConfigurationError("tried to update client session with no auth_uri")

        auth_res = self.ua.get(auth_uri)
        if auth_res.status_code != 200:
            return jc.result.Failure(
                auth_res, ident="failed to retrieve client session"
            )

        session = auth_res.json()
        auth = jc.result.Auth(auth_res, session=session)

        self.configure_from_session(session)

        return auth

    def configure_from_session(self, session):
        # XXX JMAP::Tester does a bunch of other stuff here, largely I think
        # because it was written when authentication was still part of the
        # official spec. I will forgo most of that here.
        for kind in ["api", "authentication", "download", "upload"]:
            val = session.get(kind + "Url")
            if val:
                setattr(self, kind + "_uri", val)

        self.accounts = session["accounts"]
        self.primary_accounts = session["primaryAccounts"]

    def request(self, input_req):
        if not self.api_uri:
            raise ConfigurationError("cannot request() without an api_uri")

        # we can take either an array of jmap triples, or a full request
        request = input_req
        if isinstance(input_req, list):
            request = {"methodCalls": input_req}

        default_args = self.default_arguments.copy()
        seen = set()
        cid_count = 1
        suffixed = []

        for call in request["methodCalls"]:
            copy = call.copy()

            # client ids are optional
            if len(copy) == 2:
                copy.append(None)

            if copy[2]:
                seen.add(copy[2])
            else:
                next_cid = "c{}".format(cid_count)
                while next_cid in seen:
                    cid_count += 1
                    next_cid = "c{}".format(cid_count)
                copy[2] = next_cid
                seen.add(next_cid)

            arg = {**self.default_arguments, **copy[1]}

            # JMAP::Tester has a means to delete default arguments here, which
            # I am omitting at the moment.

            copy[1] = arg
            suffixed.append(copy)

        request["methodCalls"] = suffixed

        if self.default_using and not request.get("using"):
            request["using"] = self.default_using

        # TODO: logging
        http_res = self.ua.post(self.api_uri, data=json.dumps(request))

        if not http_res.ok:
            return jc.result.Failure(http_res)

        # result object
        return jc.response.from_http(http_res)
