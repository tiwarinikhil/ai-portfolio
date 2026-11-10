"""A stand-in custom retriever, used to test --retriever module:factory."""


class _Always:
    def __init__(self, chunks):
        self.ids = [c.id for c in chunks]

    def search(self, query, k=5):
        return self.ids[:k]


def build(chunks):
    return _Always(chunks)
