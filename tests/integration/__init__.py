import requests


class NeoTestingMixin:

    """Removes Neo4j elements created during testing.

    This mix-in monitors a :class:`requests.Session` instance
    and records actions that need to be undone (e.g., creating
    a new node, etc.).  Then, during annihilation, the recorded
    actions are undone.

    Usage:

    .. code-block:: python

       class MyTest(NeoTestingMixin, ActArrangeAssertTestCase):

           @classmethod
           def arrange(cls):
               super().arrange()
               cls.storage = StorageLayer(uuid.uuid4().hex)
               cls.monitor_session(cls.storage._session)

           @classmethod
           def action(cls):
               cls.whatever = cls.storage.create_something()

           def should_do_something(self):
               ...

    If the ``create_something`` method issues an :http:method:`POST`
    or :http:method:`PUT` request, then the resulting object will
    be :http:method:`DELETE`\ d when the test is complete.  Recognizing
    a response that came from an object creation is not as easy as it
    should be, nor is it fullproof.

    The goal of this class is to make the previous test possible
    without having to complicate it with details surrounding cleaning
    up the Neo4j layer when the test finishes.  In fact, the test code
    should not even care about Neo4j unless it is specifically testing
    the interaction with it.

    """

    @classmethod
    def arrange(cls):
        super().arrange()
        cls._nodes_to_remove = []
        cls._actions = None

    @classmethod
    def annihilate(cls):
        super().annihilate()
        processed = set()
        for url in reversed(cls._nodes_to_remove):
            if url not in processed:
                requests.delete(url)
                processed.add(url)
        del cls._nodes_to_remove[:]

    @classmethod
    def monitor_session(cls, session):
        """Insert a response hook to monitor `session`.

        :param requests.Session session: the session to monitor.

        """
        session.hooks['response'].append(cls._process_neo_response)

    @classmethod
    def _process_neo_response(cls, response, **kwargs):
        if response.ok and response.text:
            if response.request.method in ('POST', 'PUT'):
                body = response.json()
                if body.get('self'):
                    cls._nodes_to_remove.append(body['self'])
                elif {'label', 'property_keys'}.issubset(body.keys()):
                    # if only POST /.../index returned a self link!
                    cls._nodes_to_remove.append(
                        'http://localhost:7474/db/data'
                        '/schema/index/{0}/{1}'.format(
                            body['label'],
                            body['property_keys'][0],
                        )
                    )

    @property
    def action_links(self):
        if self._actions is None:
            response = requests.get('http://localhost:7474/db/data')
            response.raise_for_status()
            self._actions = response.json()
        return self._actions

    def neo_get(self, action):
        """Retrieve named Neo4j action."""
        response = requests.get(self.action_links[action])
        response.raise_for_status()
        return response.json()
