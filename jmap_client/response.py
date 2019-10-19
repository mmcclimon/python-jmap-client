import json


def from_http(http_res):
    data = http_res.json()
    items = data.get("methodResponses")
    return Response(items=items, http_response=http_res, wrapper_properties=data)


class Response:
    def __init__(self, **kwargs):
        self.items = kwargs["items"]
        self.http_response = kwargs["http_response"]
        self.wrapper_properties = kwargs["wrapper_properties"]
