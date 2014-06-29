import contextlib
import functools
import sqlite3

from familytree import storage

from . import Neo4jTestingMixin, SqliteLayerTestingMixin
from .. import ActArrangeAssertTestCase


class WhenCreatingStorageLayer(
        Neo4jTestingMixin, SqliteLayerTestingMixin, ActArrangeAssertTestCase):

    @classmethod
    def action(cls):
        cls.storage = storage.StorageLayer(cls.store_name)

    @functools.lru_cache()
    def get_column_names(self, table_name):
        with sqlite3.connect(self.storage.database_name) as connection:
            with contextlib.closing(connection.cursor()) as cursor:
                cursor.execute('SELECT * FROM {0} LIMIT 1'.format(table_name))
                cursor.fetchone()
                return [t[0] for t in cursor.description]

    def should_create_source_table(self):
        assert 'id' in self.get_column_names('source')
        assert 'type' in self.get_column_names('source')
        assert 'authority' in self.get_column_names('source')
        assert 'author' in self.get_column_names('source')
        assert 'title' in self.get_column_names('source')
        assert 'created' in self.get_column_names('source')

    def should_create_people_table(self):
        assert 'id' in self.get_column_names('people')
        assert 'first_name' in self.get_column_names('people')
        assert 'middle_name' in self.get_column_names('people')
        assert 'last_name' in self.get_column_names('people')
        assert 'gender' in self.get_column_names('people')


class WhenCreatingStorageLayerAndDatabaseFileExists(WhenCreatingStorageLayer):

    @classmethod
    def arrange(cls):
        super().arrange()
        db_name = '{0}.ser'.format(cls.store_name)
        with sqlite3.connect(db_name) as connection:
            connection.execute('CREATE TABLE foo (bar TEXT)')
            connection.commit()
