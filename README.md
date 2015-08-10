The py-memento-client library provides Memento support, as specified in RFC 7089.

For more information about Memento, go to http://www.mementoweb.org

This source distribution contains the following folders:

* py-memento-client - the main py-memento-client code
* test - test code for py-memento-client
* MANIFEST.in - manifest of this distribution, in format described by https://docs.python.org/2/distutils/sourcedist.html
* LICENSE.txt - the license for this source code
* README.md - this file
* setup.py - Python script providing information for distutils

# BUILD

To build this distribution, just type:
```
python setup.py dist
```
and it will create a dist folder containing a tar.gz containing this distribution.

To start fresh: 
```
python setup.py clean
```
will remove the contents of the build and dist folders.

To run automated tests: 
```
python setup.py test
```
Note that these rely upon live web resources, which should not change.

# USING THE LIBRARY

This simple use case gets a Memento from the default Memento TimeGate for "http://lanl.gov" on April 24, 2010 at 19:00:00.

```python
import datetime
import memento_client

dt = datetime.datetime(2010, 4, 24, 19, 0)

uri = "http://lanl.gov"

mc = MementoClient()

memento_uri = mc.get_memento_info(uri, dt).get("mementos").get("closest").get("uri")[0]
```

One can specify a specific TimeGate like so.

```python
import datetime
import memento_client

dt = datetime.datetime(2010, 4, 24, 19, 0)
uri = "http://lanl.gov"

timegate = "http://timetravel.mementoweb.org/webcite/timegate/"

mc = MementoClient(timegate_uri=timegate, check_native_timegate=False)

memento_uri = mc.get_memento_info(uri, dt).get("mementos").get("closest").get("uri")[0]
```
