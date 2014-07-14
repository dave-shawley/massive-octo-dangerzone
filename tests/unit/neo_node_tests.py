from unittest import mock

from familytree import storage
from .. import ActArrangeAssertTestCase


class WhenFetchingActionLinks(ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.node = storage.NeoNode({
            mock.sentinel.action: mock.sentinel.link,
            'data': {},
        })

    @classmethod
    def action(cls):
        cls.links = cls.node.action_links

    def should_return_node_data_without_properties(self):
        assert self.links == {mock.sentinel.action: mock.sentinel.link}


class WhenFetchingActionLinksAgain(WhenFetchingActionLinks):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.first_links = cls.node.action_links

    def should_return_same_instance_twice(self):
        assert self.links is self.first_links
