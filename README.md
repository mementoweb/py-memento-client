The py-memento-client library provides Memento support, as specified in RFC 7089.

For more information about Memento, go to http://www.mementoweb.org

This source distribution contains the following folders:

* py-memento-client - the main py-memento-client code
* test - test code for py-memento-client
* MANIFEST.in - manifest of this distribution, in format described by https://docs.python.org/2/distutils/sourcedist.html
* LICENSE.txt - the license for this source code
* README.md - this file
* setup.py - Python script providing information for distutils

To build this distribution, just type:
```
python setup.py dist
```
and it will create a dist folder containing a tar.gz containing this distribution.

To start fresh
```
python setup.py clean
```
will remove the contents of the build and dist folders.
