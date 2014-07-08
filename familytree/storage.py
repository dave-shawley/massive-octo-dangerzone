"""
Storage Interface.
------------------

- :class:`StorageLayer` - provides object, relationship, and fact
  persistence and retrieval

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
import json
import sqlite3

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
