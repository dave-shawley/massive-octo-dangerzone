"""
Storage Interface.
------------------

- :class:`BaseUrlMixin` - add relative URL support to the
  :class:`requests.Session` class
- :class:`JsonSessionMixin` - implements common JSON-related
  behaviors over :class:`requests.Session`
- :class:`StorageLayer` - provides object, relationship, and fact
  persistence and retrieval
- :func:`generate_hash` - generates consistent identifies for
  immutable objects

This module is responsible for storing system objects, saving the
relationships between them, and retrieving them.  Objects are
stored in a relational database (currently using :mod:`sqlite3`)
and the relationships are tracked in a Neo4j graph database.  The
details are hidden within a :class:`StorageLayer` instance as long
as the user does not peek into any identifiers returned by this
layer.  The identifiers are always opaque strings and can be
compared safely for equality.  The user should not modify object
identifiers (e.g., manipulating case).

"""
import hashlib
import json
import pickle
import sqlite3
import urllib.parse

from requests import structures
import requests

from . import urls


class _SqliteLayer:

    """
    Stores objects in an sqlite database.

    .. attribute:: database_name

        The name of the database as it appears on disk.

    """

    def __init__(self, *args, database_name, **kwargs):
        """Initialze the layer and create the database.

        :keyword str database_name: name of the database as it
            appears on disk

        When the ``SqliteLayer`` instance is created, the persistence
        file is created and initialized via a call to
        :meth:`._create_database`

        .. note::

            Additional positional and keyword arguments are
            passed along to ``super().__init__()``.

        """
        self.database_name = database_name
        super().__init__(*args, **kwargs)
        self._create_database()

    def _create_database(self):
        """Create and initialize the database.

        This method creates the database file if it does not exist
        and ensures that the necessary tables exists.  It is called
        during initialization so there no reason to call this method
        unless you want to ensure that the structure exists at some
        other time.

        """
        with sqlite3.connect(self.database_name) as connection:
            try:
                connection.execute('''
                    CREATE TABLE source (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        authority TEXT NOT NULL,
                        author TEXT NOT NULL,
                        title TEXT NOT NULL,
                        created DATE NOT NULL
                    )
                ''')
            except sqlite3.OperationalError as error:
                if 'table source already exists' not in str(error):
                    raise

            try:
                connection.execute('''
                    CREATE TABLE people (
                        id TEXT PRIMARY KEY,
                        first_name TEXT DEFAULT NULL,
                        middle_name TEXT DEFAULT NULL,
                        last_name TEXT DEFAULT NULL,
                        gender CHAR(1) NOT NULL
                    )
                ''')
            except sqlite3.OperationalError as error:
                if 'table people already exists' not in str(error):
                    raise


class _Neo4jLayer:

    """
    Store relationships in a graph database.

    .. attribute:: neo4j_actions

       A dictionary that maps Neo4j actions to the URLs necessary
       to invoke them.

    """

    def __init__(self, *args, **kwargs):
        """Initialize the layer and ensure that labels exist.

        The :meth:`._create_neo_labels` method is called during
        initializing to ensure that the labels exist.

        .. note::

           The additional positional and keyword parameters are
           passed on to ``super().__init__()``.

        """
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.headers['Accept'] = 'application/json'
        self._neo_actions = None
        self._create_neo_labels()

    @property
    def neo_actions(self):
        """Memoized dictionary of Neo4j action -> URL.

        .. code-block:: json

            {
                "batch": "http://localhost:7474/db/data/batch",
                "constraints":
                  "http://localhost:7474/db/data/schema/constraint",
                "cypher": "http://localhost:7474/db/data/cypher",
                "extensions": {},
                "extensions_info": "http://localhost:7474/db/data/ext",
                "indexes": "http://localhost:7474/db/data/schema/index",
                "neo4j_version": "2.0.3",
                "node": "http://localhost:7474/db/data/node",
                "node_index": "http://localhost:7474/db/data/index/node",
                "node_labels": "http://localhost:7474/db/data/labels",
                "relationship_index":
                  "http://localhost:7474/db/data/index/relationship",
                "relationship_types":
                  "http://localhost:7474/db/data/relationship/types",
                "transaction": "http://localhost:7474/db/data/transaction"
            }

        """
        if self._neo_actions is None:
            response = self.session.get('http://localhost:7474/db/data')
            response.raise_for_status()
            self._neo_actions = response.json()
        return self._neo_actions

    def _create_neo_labels(self):
        """Ensure that the labels exist."""
        response = self.session.get(self.neo_actions['indexes'])
        labels = {info['label'] for info in response.json()}
        if 'Person' not in labels:
            self._create_label('Person', ['external_id'])

    def _create_label(self, label_name, property_keys):
        return self.session.post(
            urls.append(self.neo_actions['indexes'], label_name),
            data=json.dumps({'property_keys': property_keys}),
            headers={'content-type': 'application/json'},
        )


class StorageLayer(_Neo4jLayer, _SqliteLayer):

    """
    Stores objects, facts, and relationships between them.

    :param str store_name: name to save storage files as

    Creating a new :class:`StorageLayer` instance will create the
    persistence storage files if they do not exist.

    .. attribute:: database_name

       The name of the database as it appears on disk.

    """

    def __init__(self, store_name):
        super().__init__(database_name='{0}.ser'.format(store_name))


def _normalize(data):
    def normalize_datetime(value):
        return value.replace(microsecond=0)

    def normalize_string(value):
        return value.lower()

    def normalize_dict(value):
        return {k: _normalize(v) for k, v in value.items()}

    def normalize_iterable(value):
        return [_normalize(elm) for elm in value]

    hooks = [normalize_datetime, normalize_string, normalize_dict,
             normalize_iterable]
    for hook in hooks:
        try:
            return hook(data)
        except (AttributeError, TypeError):
            pass

    return data


def generate_hash(object_type, object_data):
    """Generate a consistent hash for an object.

    :param str object_type: the type of object being created
    :param dict object_data: the identifying data to hash

    :return: a SHA1 digest of the object

    This function hashes normalized versions of `object_type`
    and `object_data` and returns the SHA1 hex string.  The
    normalization process applied converts strings to lower
    case and truncates sub-second values from date/time values
    before hashing the contents.

    """
    pickled = pickle.dumps((object_type.lower(), _normalize(object_data)))
    return hashlib.sha1(pickled).hexdigest()


class JsonSessionMixin:

    """Mix in over :class:`requests.Session` to handle JSON bodies.

    This mix-in provides semi-automatic content handling for JSON
    requests and responses.  The :meth:`requests.Session.request`
    method is extended to:

    1. JSONify the ``data`` keyword argument unless the
       :mailheader:`Content-Type` header *says* not to
    2. Insert a :mailheader:`Content-Type` header if necessary
    3. Insert a :mailheader:`Accept` header if necessary

    The JSONification process is more involved than simply
    calling :func:`json.dumps` on the data.  Dates are handled
    explicitly by transforming them into lists of integer values
    ordered from largest to smallest (i.e., year to second).

    """

    @staticmethod
    def _normalize_date(obj):
        try:
            value = obj.replace(second=0, microsecond=0)
            return [value.year, value.month, value.day,
                    value.hour, value.minute, value.second]
        except (AttributeError, TypeError):
            pass

        try:
            return [obj.year, obj.month, obj.day]
        except AttributeError:
            pass

        return str(obj)

    def request(self, method, url, **kwargs):
        """Adjust the request for JSON handling.

        :keyword data: an optional body to send with the request
        :keyword headers: an optional set of HTTP headers to
            include with the request

        This method extends the ``request`` method and implements
        automatic behaviors for JSON requests.  All parameters
        are passed through to ``super().request()``.

        If ``data`` is specified, then it will be converted to JSON
        unless a :mailheader:`Content-Type` header indicates that the
        body is not JSON.  The presence of a body will also trigger
        the addition of the appropriate content type header if not
        not present.

        If an :mailheader:`Accept` header is not present, then
        one will be added that allows for ``application/json``
        responses.

        """
        headers = structures.CaseInsensitiveDict(data=kwargs.get('headers'))
        data = kwargs.get('data', None)
        if data is not None:
            content_type = headers.get('Content-Type')
            if content_type is not None:
                if ';' in content_type:
                    content_type, _ = content_type.split(';', 1)
                is_json = content_type.endswith('json')
            else:
                headers['Content-Type'] = 'application/json; charset=utf-8'
                is_json = True

            if is_json:
                kwargs['data'] = json.dumps(
                    data, default=self._normalize_date)

        if 'Accept' not in headers:
            headers['Accept'] = 'application/json'

        kwargs['headers'] = headers

        return super().request(method, url, **kwargs)


class BaseUrlMixin:

    """Mix in over :class:`requests.Session` for a URL prefix.

    .. attribute:: base_url

       The URL to use as the base when relative URLs are passed
       to :meth:`request`.  This attribute is set by specifying
       the ``base_url`` parameter to the initializer.

    This simple mix-in extends :meth:`requests.Session.request`
    so that it will perform a *URL join* operation between the
    requested URL and the :attr:`base_url` attribute before
    calling the base class ``request`` method.

    """

    def __init__(self, base_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url
        if not self.base_url.endswith('/'):
            self.base_url += '/'

    def request(self, method, url, *args, **kwargs):
        """Prefixes ``url`` with :attr:`base_url` if necessary."""
        return super().request(
            method,
            urllib.parse.urljoin(self.base_url, url),
            *args, **kwargs
        )


class NeoSession(BaseUrlMixin, JsonSessionMixin, requests.Session):

    """A ``requests.Session`` with Neo4j helpers.

    The `Neo4j REST API`_ is a JSON-based API that contains
    some hypermedia action links.  A ``NeoSession`` instance
    provides automatic translation of request data to JSON
    bodies using the :class:`.JsonSessionMixin`.  Just include
    a :class:`dict` instance as the ``data`` keyword parameter
    to any of the HTTP action methods.  The ``NeoSession`` will
    take care of JSONifying the ``dict`` and inserting the
    appropriate headers.

    The *Service Root* of the API is a point for discovering the
    available endpoints.  The service root response contains a
    hypermedia link map as well as some information about the
    server.  The API map is loaded on demand and made available
    via the :attr:`action_links` attribute.

    Since the Neo4j API is hypermedia driven, the :meth:`request`
    method will accept an action name in place of the ``url``
    parameter.  If ``url`` matches a key in :attr:`action_links`,
    then the URL for the endpoint is used instead.

    .. _Neo4j REST API: http://docs.neo4j.org/chunked/stable/rest-api.html

    """

    def __init__(self):
        super().__init__(base_url='http://localhost:7474/db/data')
        self._action_links = None

    @property
    def action_links(self):
        """
        :class:`dict` that maps hypermedia action to API endpoint

        This attribute can be used to discover the functionality
        available from the Neo server.  Keys from this attribute
        can be used as the ``url`` parameter to :meth:`request`
        as well.

        .. code-block:: json

            {
                "batch": "http://localhost:7474/db/data/batch",
                "constraints":
                    "http://localhost:7474/db/data/schema/constraint",
                "cypher": "http://localhost:7474/db/data/cypher",
                "extensions": {},
                "extensions_info": "http://localhost:7474/db/data/ext",
                "indexes": "http://localhost:7474/db/data/schema/index",
                "neo4j_version": "2.0.3",
                "node": "http://localhost:7474/db/data/node",
                "node_index": "http://localhost:7474/db/data/index/node",
                "node_labels": "http://localhost:7474/db/data/labels",
                "relationship_index":
                    "http://localhost:7474/db/data/index/relationship",
                "relationship_types":
                    "http://localhost:7474/db/data/relationship/types",
                "transaction": "http://localhost:7474/db/data/transaction"
            }

        """
        if self._action_links is None:
            response = self.get('')
            self._action_links = response.json()
        return self._action_links

    def request(self, method, url, *args, **kwargs):
        """Issue an HTTP request.

        :param str method: passed to ``super().request()``
        :param str url: see below
        :param args: passed to ``super().request()``
        :param kwargs: passed to ``super().request()``

        This method recognizes when a Neo4j action is passed
        as the `url` parameter.  If `url` is a key in
        :attr:`action_links`, then the action link replaces
        the URL before calling ``super().request()``.

        """
        if url in self.action_links:
            url = self.action_links[url]
        return super().request(method, url, *args, **kwargs)
