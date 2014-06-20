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
import sqlite3


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
        self._create_database()

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
