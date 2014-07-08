import datetime
import hashlib

from familytree import source

from .. import ActArrangeAssertTestCase, RandomValueMixin


class WhenCreatingSimpleSource(RandomValueMixin, ActArrangeAssertTestCase):

    @classmethod
    def action(cls):
        cls.source = source.create_source(
            cls.get_generated_string('title'),
            cls.get_generated_string('type'),
        )

    def should_create_deterministic_id_hash(self):
        parts = [
            b'source',
            self.get_generated_string('title').encode('utf-8'),
            self.get_generated_string('type').encode('utf-8'),
            datetime.date.today().isoformat().encode('utf-8'),
        ]
        assert self.source.id == hashlib.sha1(b':'.join(parts)).hexdigest()
