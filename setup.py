
# much of this was shamelessly stolen from
# https://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/
from setuptools import setup, Command
from setuptools.command.test import test as TestCommand
import os
import sys
import glob
import shutil

here = os.path.abspath(os.path.dirname(__file__))

class PyTest(TestCommand):

    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        import multiprocessing
        procs = multiprocessing.cpu_count()

        if procs > 1:
            if type(self.pytest_args) == list:
                self.pytest_args.append("-n " + str(procs))
            elif type(self.pytest_args) == str:
                self.pytest_args += " -n " + str(procs)

        errcode = pytest.main(self.pytest_args)
        sys.exit(errcode)


class BetterClean(Command):
    """Custom clean command to remove other stuff from project root."""
    user_options=[]
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def handle_remove_errors(*args):
        print("Issue removing '" + args[1] + "' (probably does not exist), skipping...")

    def run(self):
        egg_info = glob.glob('*.egg-info')

        for entry in egg_info:
            print("removing " + entry)
            shutil.rmtree(entry)

        shutil.rmtree('build', onerror = BetterClean.handle_remove_errors)
        shutil.rmtree('dist', onerror = BetterClean.handle_remove_errors)

setup(
    name="memento_client",
    version="0.5.3",
    url='https://github.com/mementoweb/py-memento-client',
    license='LICENSE.txt',
    author="Harihar Shankar, Shawn M. Jones, Herbert Van de Sompel",
    author_email="prototeam@googlegroups.com",
    install_requires=['requests>=2.7.0'],
    tests_require=['pytest-xdist', 'pytest'],
    cmdclass={
        'test': PyTest,
        'cleanall': BetterClean
        },
    download_url="https://github.com/mementoweb/py-memento-client",
    description='Official Python library for using the Memento Protocol',
    long_description="""
The memento_client library provides Memento support, as specified in RFC 7089 (http://tools.ietf.org/html/rfc7089)

For more information about Memento, see http://www.mementoweb.org/about/.

This library allows one to find information about archived web pages using the Memento protocol.  It is the goal of this library to make the Memento protocol as accessible as possible to Python developers.
""",
    packages=['memento_client'],
    keywords='memento http web archives',
    extras_require = {
        'testing': ['pytest'],
        "utils": ["lxml"]
    },
    classifiers=[

        'Intended Audience :: Developers',

        'License :: OSI Approved :: BSD License',

        'Operating System :: OS Independent',

        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',

        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4'
    ]
)
