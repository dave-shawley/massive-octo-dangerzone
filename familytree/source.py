"""
Records why something exists in the information model.

A **Source** represents the reason or proof that another object
exists in the data model.  For example, if a person is created
based on information from a census record, then the census record
is the source.  Tracking _why_ we believe that something exists is
almost as important as the what.

- :func:`create_source`: creates a new :class:`Source` instance and
  persists it to the data store.
- :class:`Source`: the focal point of the concept.

"""
import datetime
import hashlib
import uuid


def create_source(title, source_type):
    return Source(title, source_type)


class Source:

    def __init__(self, title, source_type):
        super().__init__()
        self.title = title
        self.source_type = source_type
        now = datetime.date.today().isoformat()
        self.id = hashlib.sha1(b':'.join([
            b'source',
            self.title.encode('utf-8'),
            self.source_type.encode('utf-8'),
            now.encode('utf-8'),
        ])).hexdigest()
