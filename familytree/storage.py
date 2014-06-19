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


class StorageLayer:

    """
    Stores objects, facts, and relationships between them.

    :param str store_name: name to save storage files as

    Creating a new :class:`StorageLayer` instance will create the
    persistence storage files if they do not exist.

    .. attribute:: db_name

       The name of the database as it appears on disk.

    """

    def __init__(self, store_name):
        self.db_name = '{0}.ser'.format(store_name)
        self.session = requests.Session()
        self.session.headers['Accept'] = 'application/json'
        self._neo_actions = None

        self._create_database()
        self._create_neo_labels()

    @property
    def neo_actions(self):
        """Memoized dictionary of Neo4j action -> URL."""
        if self._neo_actions is None:
            response = self.session.get('http://localhost:7474/db/data')
            response.raise_for_status()
            self._neo_actions = response.json()
        return self._neo_actions

    def _create_database(self):
        with sqlite3.connect(self.db_name) as connection:
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

    def _create_neo_labels(self):
        response = self.session.get(self.neo_actions['indexes'])
        labels = {info['label'] for info in response.json()}
        if 'Person' not in labels:
            self.session.post(
                urls.append(self.neo_actions['indexes'], 'Person'),
                data=json.dumps({'property_keys': ['external_id']}),
                headers={'content-type': 'application/json'},
            )
