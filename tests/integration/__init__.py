import requests

from familytree import storage
from .. import InfectiousMixin


class Neo4jTestingMixin(InfectiousMixin):

    """
    Removes Neo4j elements created during testing.

    This mix-in patches the :class:`familytree.storage.StorageLayer`
    class so that the Neo4j manipulation methods inherited from
    :class:`familytree.storage._Neo4jLayer` record the actions that
    they have done.  Then, during annihilation, any modifications
    to the data set are removed.

    Usage:

    .. code-block:: python

       class MyTest(Neo4jTestingMixin, ActArrangeAssertTestCase):
           @classmethod
           def action(cls):
               cls.storage = StorageLayer(uuid.uuid4().hex)

           @classmethod
           def annihilate(cls):
               super().annihilate()
               os.unlink(cls.storage.database_name)

           def should_do_something(self):
               ...

    The goal of this class is to make the previous test possible
    without having to complicate it with details surrounding cleaning
    up the Neo4j layer when the test finishes.  In fact, the test code
    should not even care about Neo4j unless it is specifically testing
    the interaction with it.

    """

    @classmethod
    def arrange(cls):
        super().arrange()
        cls._session = requests.Session()
        cls._session.headers['Accept'] = 'application/json'

        cls._cleanups = []
        cls.infect_method(
            storage.StorageLayer, '_create_label', cls._record_result)

    @classmethod
    def _record_result(cls, method, result):
        if result.ok:  # pragma nocover
            if method == storage._Neo4jLayer._create_label:
                url = '/'.join((
                    result.request.url,
                    result.json()['property_keys'][0],
                ))
                cls._cleanups.append((cls._session.delete, (url, ), {}))
        return result

    @classmethod
    def annihilate(cls):
        super().annihilate()
        while cls._cleanups:
            action, args, kwargs = cls._cleanups.pop()
            action(*args, **kwargs)
