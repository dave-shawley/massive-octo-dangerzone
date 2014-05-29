import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

from familytree import __version__


def read_requirements_file(req_file):
    with open(req_file, 'r') as req_handle:
        return [l.strip() for l in req_handle if not l.startswith('#')]


class PyTestRunner(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True

    def run_tests(self):
        import pytest  # lazily
        sys.exit(pytest.main(self.test_args))


setup(
    name='familytree',
    version=__version__,
    author='Dave Shawley',
    description='Simple geneaology application',
    long_description='\n' + open('README.rst').read(),
    packages=['familytree'],
    zip_safe=False,
    setup_requires=[],
    install_requires=read_requirements_file('requirements.txt'),
    tests_require=read_requirements_file('test-requirements.txt'),
    cmdclass={'test': PyTestRunner},
    classifiers=[
    ],
)
