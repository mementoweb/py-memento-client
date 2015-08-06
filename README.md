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
make
```
and it will create a dist folder containing a tar.gz, tar.bz2, and zip file containing this distribution.

To start fresh
```
make clean
```
will remove the build and dist folders.
