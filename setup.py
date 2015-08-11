
# much of this was shamelessly stolen from
# https://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/
from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys
import glob
import shutil

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
        shutil.rmtree('.eggs', onerror = BetterClean.handle_remove_errors)


setup(
    name="memento_client",
    version="0.5.1.dev2",
    url='https://github.com/mementoweb/py-memento-client',
    license='LICENSE.txt',
    author="Harihar Shankar, Shawn M. Jones, Herbert Van de Sompel",
    author_email="prototeam@googlegroups.com",
    tests_require=['pytest'],
    install_requires=[ 'requests>=2.7.0', 'lxml>=3.4.4' ],
    cmdclass={'test': PyTest, 'clean': BetterClean},
    download_url="https://github.com/mementoweb/py-memento-client",
    description='Official Python library for using the Memento Protocol',
    long_description=long_description,
    packages=['memento_client'],
    keywords='memento http web archives',
    extras_require = {
        'testing': ['pytest'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',

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
