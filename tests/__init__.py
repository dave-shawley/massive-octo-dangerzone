from unittest import mock
import logging

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

    @property
    def random_string(self):
        """A new random string."""
        self.last_random = self._factory.pystr()
        return self.last_random

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

    .. _Act, Arrange, Assert: http://www.arrangeactassert.com/why-and-what-is-arrange-act-assert/
    .. _Single Assert Principle: http://www.artima.com/weblogs/viewpost.jsp?thread=35578

    """

    raised_exception = None
    """Captures any exception raised by ``action``."""

    @classmethod
    def setup_class(cls):
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
            cls.arrange()
            try:
                cls.action()
            except AssertionError:
                raise
            except Exception as raised:
                _logger.debug('exception caught', exc_info=True)
                cls.raised_exception = raised
        except Exception:
            _logger.exception('arrange step failed')

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
    def action(cls):
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
