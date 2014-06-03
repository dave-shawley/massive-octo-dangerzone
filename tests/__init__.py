from faker import Faker


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
