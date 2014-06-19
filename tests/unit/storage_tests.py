import sqlite3
import uuid

from requests import exceptions

from familytree import storage
from .. import (
    ActArrangeAssertTestCase,
    PatchingMixin,
    RandomValueMixin,
    TemporaryFileMixin,
)


class CreateStorageTestCase(
        PatchingMixin, TemporaryFileMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super(CreateStorageTestCase, cls).arrange()

        session = cls.create_patch(
            'familytree.storage.requests.session').return_value
        session.get.return_value = '{"indexes":"http://example.com"}'

        sqlconnect = cls.create_patch('familytree.storage.sqlite3.connect')
        cls.sqlconn = sqlconnect.return_value.__enter__.return_value
        cls.sqlconn.execute.side_effect = cls._execute_sql_hook
        cls.store_name = cls.create_temporary_file(create_file=False)

    @classmethod
    def action(cls):
        cls.storage = storage.StorageLayer(cls.store_name)

    @classmethod
    def _execute_sql_hook(cls, sql, _=None):
        pass

    @staticmethod
    def _raise_table_exists(table_name):
        raise sqlite3.OperationalError(
            'table {0} already exists'.format(table_name))

    def sql_was_run(self, sql_fragment):
        for args, kwargs in self.sqlconn.execute.call_args_list:
            if sql_fragment.lower() in args[0].lower():
                return True
        return False

    def assert_sql_was_run(self, sql_fragment):
        assert self.sql_was_run(sql_fragment)


class WhenCreatingDatabaseAndSourceTableExists(CreateStorageTestCase):

    @classmethod
    def _execute_sql_hook(cls, sql, _=None):
        if 'create table source' in sql.lower():
            cls._raise_table_exists('source')

    def should_not_raise_exception(self):
        assert self.raised_exception is None

    def should_attempt_to_create_source_table(self):
        self.assert_sql_was_run('create table source')

    def should_attempt_to_create_people_table(self):
        self.assert_sql_was_run('create table people')


class WhenCreatingDatabaseAndPeopleTableExists(CreateStorageTestCase):

    @classmethod
    def _execute_sql_hook(cls, sql, _=None):
        if 'create table people' in sql.lower():
            cls._raise_table_exists('people')

    def should_not_raise_exception(self):
        assert self.raised_exception is None

    def should_attempt_to_create_source_table(self):
        self.assert_sql_was_run('create table source')

    def should_attempt_to_create_people_table(self):
        self.assert_sql_was_run('create table people')


class WhenCreatingDatabaseAndSourceTableCreationFails(CreateStorageTestCase):

    @classmethod
    def _execute_sql_hook(cls, sql, _=None):
        if 'create table source' in sql.lower():
            raise sqlite3.OperationalError('something bad happened')

    def should_raise_exception(self):
        assert self.raised_exception is not None

    def should_attempt_to_create_source_table(self):
        self.assert_sql_was_run('create table source')

    def should_not_attempt_to_create_people_table(self):
        assert not self.sql_was_run('create table people')


class WhenCreatingDatabaseAndPeopleTableCreationFails(CreateStorageTestCase):

    @classmethod
    def _execute_sql_hook(cls, sql, _=None):
        if 'create table people' in sql.lower():
            raise sqlite3.OperationalError('something bad happened')

    def should_raise_exception(self):
        assert self.raised_exception is not None

    def should_attempt_to_create_source_table(self):
        self.assert_sql_was_run('create table source')

    def should_attempt_to_create_people_table(self):
        assert self.sql_was_run('create table people')


class WhenRetrievingNeoActionsAndGetFails(
        PatchingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()

        cls.create_patch('familytree.storage.sqlite3.connect')
        cls.create_patch('familytree.storage.StorageLayer._create_neo_labels')
        requests = cls.create_patch('familytree.storage.requests')
        cls.session = requests.Session.return_value
        response = cls.session.get.return_value
        response.raise_for_status.side_effect = exceptions.HTTPError

        cls.storage = storage.StorageLayer('unused')

    @classmethod
    def action(cls):
        cls.actions = cls.storage.neo_actions

    def should_retrieve_actions_from_neo_root(self):
        self.session.get.assert_called_once_with(
            'http://localhost:7474/db/data')

    def should_propagate_exception(self):
        assert isinstance(self.raised_exception, exceptions.HTTPError)
