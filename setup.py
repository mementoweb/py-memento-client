
# much of this was shamelessly stolen from
# https://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

import memento_client

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.txt')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name="memento_client",
    version=memento_client.__version__,
    url='https://github.com/mementoweb/py-memento-client',
    license='LICENSE.txt',
    author=memento_client.__author__,
    tests_require=['pytest'],
    install_requires=[ 'requests', 'lxml' ],
    cmdclass={'test': PyTest},
    author_email=memento_client.__author_email__,
    description='Official Python library for using the Memento Protocol',
    long_description=long_description,
    packages=['memento_client'],
    keywords='memento http web archives',
    extras_require = {
        'testing': ['pytest'],
    }
)
