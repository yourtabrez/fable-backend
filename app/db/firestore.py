from google.cloud import firestore

_db = None


def _get_db():
    global _db
    if _db is None:
        _db = firestore.Client()
    return _db


class _LazyDB:
    def collection(self, *args, **kwargs):
        return _get_db().collection(*args, **kwargs)


db = _LazyDB()