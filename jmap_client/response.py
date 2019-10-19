import json
from warnings import warn

from jmap_client.exceptions import SentenceError


def from_http(http_res):
    data = http_res.json()
    items = data.get("methodResponses")
    return Response(items=items, http_response=http_res, wrapper_properties=data)


class Response:
    def __init__(self, **kwargs):
        self.items = kwargs["items"]
        self.http_response = kwargs["http_response"]
        self.wrapper_properties = kwargs["wrapper_properties"]

        # JMAP::Tester uses a role to do this, but that's weird in python, so
        # I am going to collapse this hierarchy.
        self._index_setup()

    def _index_setup(self):
        cids = map(lambda item: item[2], self.items)

        prev_cid = None
        cid_indices = {}

        for i, cid in enumerate(cids):
            if not cid:
                warn(
                    "undefined client_id in position {}".format(i),
                    category=RuntimeWarning,
                )
                continue

            this_cid = cid_indices.setdefault(cid, [])
            this_cid.append(i)
            prev_cid = cid

        setattr(self, "_cid_indices", cid_indices)

    def is_success(self):
        return True

    def sentence_for_item(self, item):
        return Sentence(name=item[0], arguments=item[1], client_id=item[2])

    def sentence(self, n):
        try:
            item = self.items[n]
            return self.sentence_for_item(item)
        except IndexError:
            raise SentenceError("no sentence for index {}".format(n))

    def sentences(self):
        return list(map(lambda item: self.sentence_for_item(item), self.items))

    def single_sentence(self, name=None):
        if len(self.items) != 1:
            raise SentenceError(
                "called .single_sentence() on a response with more than one sentence"
            )

        sentence = self.sentence_for_item(self.items[0])
        if name and name != sentence.name:
            raise SentenceError("found no sentence named {}".format(name))

        return sentence

    def sentence_named(self, name):
        sentences = list(filter(lambda s: s.name == name, self.sentences()))
        if not sentences:
            raise SentenceError("found no sentence named {}".format(name))

        if len(sentences) > 1:
            raise SentenceError("found more than sentence named {}".format(name))

        return sentences[0]

    def as_triples(self):
        return list(map(lambda s: s.as_triple(), self.sentences()))

    def as_pairs(self):
        return list(map(lambda s: s.as_pair(), self.sentences()))


class Sentence:
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.arguments = kwargs["arguments"]
        self.client_id = kwargs["client_id"]

    def as_triple(self):
        return [self.name, self.arguments, self.client_id]

    def as_pair(self):
        return [self.name, self.arguments]
