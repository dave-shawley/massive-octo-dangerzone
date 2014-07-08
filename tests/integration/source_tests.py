from familytree import source

from .. import ActArrangeAssertTestCase, RandomValueMixin


class WhenCreatingSource(RandomValueMixin, ActArrangeAssertTestCase):

    @classmethod
    def action(cls):
        cls.result = source.create_source(
            cls.get_generated_string('title'),
            cls.get_generated_string('type'),
        )

    def should_assign_unique_identifier(self):
        assert self.result.id is not None

    def should_store_title(self):
        assert self.result.title == self.get_generated_string('title')

    def should_store_type(self):
        assert self.result.source_type == self.get_generated_string('type')
