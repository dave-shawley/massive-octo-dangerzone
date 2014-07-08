import functools
from unittest import mock
import logging
import os
import shutil
import tempfile
import uuid

from faker import Faker


_logger = logging.getLogger('tests')


class RandomValueMixin:

    """
    Mix-in that adds random data properties.

    This mix-in generates random values of specific types. The
    normal use case is similar to :data:`unittest.mock.sentinel`
    except that this class generates random *typed* values.

    """

    _factory = Faker()

    last_random = None
    """The last random value generated."""

    _named_values = {}

    @classmethod
    def get_generated_string(cls, value_name=None):
        """Get a named randomly generated string.

        :param str value_name: optional name to assign to the
            generated value

        If `value_name` is specified, then future calls to this
        method with the same name will result in the same value
        being returned.  This is useful if you need to generate
        several random strings and refer to their values later.

        """
        random_value = cls._factory.pystr()
        if value_name is not None:
            random_value = cls._named_values.setdefault(
                value_name, random_value)
        cls.last_random = random_value
        return cls.last_random

    @property
    def random_string(self):
        """A new random string."""
        return self.get_generated_string()

    @property
    def random_int(self):
        """A new random integer."""
        self.last_random = self._factory.pyint()
        return self.last_random


class ActArrangeAssertTestCase:

    """
    Base class for testing a single action.

    This class implements the `Act, Arrange, Assert`_ pattern
    that emerged somewhere around 2003.  The idea is simple:
    test implementations should do whatever setup is necessary,
    perform a *single action, precisely once*, and then execute
    logical assertions that constrain the action.

    The :class:`unittest.TestCase` class in the standard library
    implements  a variant of this using :meth:`~unittest.TestCase.setUp`,
    :meth:`~unittest.TestCase.tearDown`, and individual assertion
    methods.  What it lacks is the singular execution as well as
    guaranteed cleanup.  We can abuse the class-level set up and
    teardown methods to ensure that the action under question is
    performed precisely once as well as guaranteeing cleanup.

    While the `Act, Arrange, Assert`_ pattern makes tests much more
    readable, it doesn't necessarily make them easier to use as a
    tool.  The next pattern that is incorporated is the `Single Assert
    Principle`_ which emerged around 2004.  The idea is to make test
    failures very easy to diagnose by ensuring that each test
    case tests a *single logical assertion*.  This isn't strictly
    enforced but it is strongly encouraged.  Each test method should
    include a single logical assertion.  Since the action is executed
    once during the *act* phase, the expense of executing the setup and
    teardown for every test case has been removed.  So, you can include
    lots of test methods that are well-named and contain a single
    logical assertion.

    .. _Act, Arrange, Assert: http://www.arrangeactassert.com/
       why-and-what-is-arrange-act-assert/
    .. _Single Assert Principle: http://www.artima.com/weblogs/
       viewpost.jsp?thread=35578

    """

    raised_exception = None
    """Captures any exception raised by ``action``."""

    expected_exceptions = ()
    """Tuple of expected exception types."""

    @classmethod
    def setup_class(cls):  # pragma nocover
        """The heart of this testing pattern.

        The trick to having actions executed exactly once is to do
        them in a method that is only invoked once for the class
        such as ``setup_class``.  This is where the other classmethods
        are run from and the order between them is enforced.  Concrete
        test classes SHOULD NOT override or extend this method.  The
        :meth:`.arrange` and :meth:`.annihilate` methods should be
        extended instead.

        """
        # noinspection PyBroadException
        try:
            try:
                cls.arrange()
            except Exception:
                _logger.exception('Arrange step failed')
                raise

            try:
                cls.action()
            except AssertionError:
                raise
            except cls.expected_exceptions as raised:
                cls.raised_exception = raised
        except:
            # teardown_class will not be called in this case so we
            # need to perform the cleanup manually.
            _logger.exception('Unexpected exception')
            cls.annihilate()
            raise

    @classmethod
    def teardown_class(cls):
        cls.annihilate()

    @classmethod
    def arrange(cls):
        """Arrange the testing environment.

        Concrete test classes SHOULD extend this method to perform
        any actions that need to happen before the action under test
        is invoked.  If this method raises an exception, then the
        :meth:`.action` method will not be invoked.

        """
        pass

    @classmethod
    def annihilate(cls):
        """Clean up after the test and all assertions have run.

        Concrete test classes SHOULD extend this method to perform
        any clean up actions that are necessary.  This method is run
        from :meth:`.teardown_class` so it is run after all other
        methods have run.  The :meth:`.setup_class` method guarantees
        that this method will always run.

        """
        pass

    @classmethod
    def action(cls):  # pragma nocover
        """Perform the action under test.

        Concrete test class MUST implement this method.  It should
        before only the action under test.

        """
        raise NotImplementedError


class PatchingMixin:

    """
    Add the ability to create targeted patches.

    This mix-in adds a single new class method, :meth:`.create_patch`,
    which patches some portion of the system using
    :func:`unittest.mock.patch`.  The raison d'être for this mixin
    is to ensure that patches are active from the time that
    :meth:`.create_patch` returns until the test case has completed.
    When using ``patch`` directly, the lifetime of the patch is
    controlled by using the return value as either a decorator or a
    context manager.

    """

    @classmethod
    def setup_class(cls):
        cls.__patchers = []
        super().setup_class()

    @classmethod
    def teardown_class(cls):
        super().teardown_class()
        for patch in cls.__patchers:
            patch.stop()

    @classmethod
    def create_patch(cls, target, *args, **kwargs):
        """Patch ``target`` and return the generated mock.

        This method creates a new patch by calling :func:`unittest.mock.patch`
        with the parameters, installs the patch, and returns the
        active :class:`~unittest.mock.Mock` instance.  The
        :meth:`teardown_class` method is extended to stop any
        patches that are generated by this method.

        """
        patcher = mock.patch(target, *args, **kwargs)
        cls.__patchers.append(patcher)
        return patcher.start()


class TemporaryFileMixin:  # pragma nocover

    """
    Add the ability to safely create temporary files.

    This mix-in provides the :meth:`.create_temporary_file` method
    which does precisely what it sounds like it should do.  It
    creates temporary files that are removed when the test finishes.

    """

    @classmethod
    def setup_class(cls):
        cls.__temporary_directory = None
        super().setup_class()

    @classmethod
    def teardown_class(cls):
        super(TemporaryFileMixin, cls).teardown_class()
        if cls.__temporary_directory is not None:
            shutil.rmtree(cls.__temporary_directory)

    @classmethod
    def create_temporary_file(cls, prefix='tmp', suffix='', create_file=True):
        """Create a new temporary file.

        :param prefix: passed to :func:`tempfile.mkstemp`
        :param suffix: passed to :func:`tempfile.mkstemp`
        :param create_file: set this to :data:`False` if you only
            need a unique file name
        :return: the name of a unique file that will be removed
            when :meth:`.teardown_class` is called

        """
        if cls.__temporary_directory is None:
            cls.__temporary_directory = tempfile.mkdtemp()
        if create_file:
            return tempfile.mkstemp(
                prefix=prefix, suffix=suffix, dir=cls.__temporary_directory)
        file_name = '{0}{1}{2}'.format(prefix, uuid.uuid4().hex, suffix)
        return os.path.join(cls.__temporary_directory, file_name)


class InfectiousMixin:

    """
    Observe method calls to an object/class.

    Mix in this class over :class:`.ActArrangeAssertTestCase` if
    you need to observe method calls to an object.  This functionality
    is implemented by overwriting the method of the target object with
    a simple wrapper that calls a hook and returns the result.  For
    example, this can be used to keep track of method calls and their
    results so that you can undo the action later.

    .. code-block:: python

        class WhenDoingTheWhoopy(
                InfectiousMixin, ActArrangeAssertTestCase):

            @classmethod
            def arrange(cls):
                super().arrange()
                cls.infect_method(
                    module.SomeClass, 'interesting', cls.spy)

            @classmethod
            def spy(cls, target, response):
                print(target, 'returned', response)
                return response

    """

    @classmethod
    def arrange(cls):
        super().arrange()
        cls._infected = []

    @classmethod
    def annihilate(cls):
        super().annihilate()
        for target_class, method_name, old_method in cls._infected:
            setattr(target_class, method_name, old_method)
        del cls._infected[:]

    @classmethod
    def infect_method(cls, target_class, method_name, hook):
        existing = getattr(target_class, method_name)
        assert existing is not None

        @functools.wraps(existing)
        def wrapped(*args, **kwargs):
            result = existing(*args, **kwargs)
            return hook(existing, result)

        setattr(target_class, method_name, wrapped)
        cls._infected.append((target_class, method_name, existing))
