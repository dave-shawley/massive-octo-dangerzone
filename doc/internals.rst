Internals
=========
This section describes some of the internals of this application and its
source environment.

Storage Layer
-------------
The :class:`~familytree.storage.StorageLayer` class is responsible for
hiding many of the details surrounding the underlying storage of objects
and relationships.  The details are actually separated into separate base
classes for each of the backend concerns.

.. autoclass:: familytree.storage._SqliteLayer
   :members:
   :special-members: __init__
   :private-members:

.. autoclass:: familytree.storage._Neo4jLayer
   :members:
   :special-members: __init__
   :private-members:


Testing
-------
This application suite is tested using `py.test`_ and a number of useful
testing classes that I've come up with.

.. autoclass:: tests.ActArrangeAssertTestCase
   :members:

.. autoclass:: tests.PatchingMixin
   :members:

.. autoclass:: tests.RandomValueMixin
   :members:

.. autoclass:: tests.TemporaryFileMixin
   :members:

.. autoclass:: tests.InfectiousMixin
   :members:

.. autoclass:: tests.integration.Neo4jTestingMixin
   :members:

.. autoclass:: tests.integration.SqliteLayerTestingMixin
   :members:

.. _py.test: http://pytest.org/
