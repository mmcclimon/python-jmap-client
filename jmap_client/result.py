# TODO: flesh this out

from abc import ABC, abstractmethod


class Result(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def is_success(self):
        pass

    def response_payload(self):
        if getattr(self, "http_response"):
            return self.http_response.raw

        return ""


class Failure(Result):
    def __init__(self, http_res, **kwargs):
        self.http_response = http_res
        self.ident = kwargs.get("ident")

    def is_success(self):
        return False


class Auth(Result):
    def __init__(self, http_res, session):
        self.http_response = http_res
        self.session = session

    def is_success(self):
        return True
