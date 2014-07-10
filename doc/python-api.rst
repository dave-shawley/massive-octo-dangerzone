Python API
==========

Concepts
--------

A **Concept** in this application suite is a Python module or package that
contains all of the details surrounding a single element in the information
model.  A Concept differs from a Model (in the MVC paradigm) in that all of
the behavior associated with an IM element is contained in a single place.
This includes the management of the object, the routines that interact with
the persistent storage layer (e.g., :mod:`familytree.storage`), as well as
any external interfaces (e.g., HTTP endpoints, CLI entry points).  This is
a departure from many traditional approaches where the implementation for
any element of the information model is distributed across the entire
application.


Command Line Interface
----------------------

.. automodule:: familytree.cli.console
   :members:

.. automodule:: familytree.cli.validators
   :members:

Persistence Layer
-----------------

.. automodule:: familytree.storage
   :members:
   :inherited-members:
   :exclude-members: BaseUrlMixin, JsonSessionMixin
