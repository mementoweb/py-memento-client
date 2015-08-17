The py-memento-client library provides Memento support, as specified in RFC 7089 (http://tools.ietf.org/html/rfc7089).

For more information about Memento, see http://www.mementoweb.org/about/

# QUICK START

Just type:
```
pip install memento_client
```
and you will have the latest stable release of this library.

# BUILD

This source distribution contains the following folders:

* memento_client - the memento_client module
* test - test code for memento_client
* LICENSE - the license for this source code
* README.md - this file
* README.txt - symbolic link to README.md
* setup.py - Python script for building this library

To build this distribution, just type:
```
python setup.py bdist
```
and it will create a dist folder containing a tar.gz containing this distribution.

To start fresh: 
```
python setup.py cleanall
```
will remove all folders (except .eggs) created during the build/test process.

To run automated tests: 
```
python setup.py test
```
Note that these rely upon live web resources, which may respond differently depending on network connectivity and location.

# USING THE LIBRARY

This simple use case gets a Memento from the default Memento TimeGate for "http://lanl.gov" on April 24, 2010 at 19:00:00.

```python
import datetime
from memento_client import MementoClient

dt = datetime.datetime(2010, 4, 24, 19, 0)

uri = "http://lanl.gov"

mc = MementoClient()

memento_uri = mc.get_memento_info(uri, dt).get("mementos").get("closest").get("uri")[0]
```

One can specify a specific TimeGate like so.

```python
import datetime
from memento_client import MementoClient

dt = datetime.datetime(2010, 4, 24, 19, 0)
uri = "http://lanl.gov"

timegate = "http://timetravel.mementoweb.org/webcite/timegate/"

mc = MementoClient(timegate_uri=timegate, check_native_timegate=False)

memento_uri = mc.get_memento_info(uri, dt).get("mementos").get("closest").get("uri")[0]
```
The get_memento_info method returns a dictionary much like the JSON format described by API documentation at http://timetravel.mementoweb.org/guide/api/#memento-json.

For example (as run in iPython):

```python
In [48]: mc = MementoClient()

In [49]: mc.get_memento_info("http://www.cnn.com", dt)
Out[49]:
{'mementos': {'closest': {'datetime': datetime.datetime(2001, 9, 11, 18, 15, 28),
   'http_status_code': 200,
   'uri': [u'http://webarchive.loc.gov/all/20010911181528/http://www2.cnn.com/']},
  'first': {'datetime': datetime.datetime(2000, 6, 20, 18, 2, 59),
   'uri': ['http://web.archive.org/web/20000620180259/http://cnn.com/']},
  'last': {'datetime': datetime.datetime(2015, 8, 7, 20, 0, 34),
   'uri': ['http://web.archive.org/web/20150807200034/http://www.cnn.com/']}},
 'original_uri': 'http://www.cnn.com',
 'timegate_uri': 'http://timetravel.mementoweb.org/timegate/http://www.cnn.com'}
```

As shown above, to get the closest memento to the datetime given, use .get("mementos").get("closest").get("uri")[0] in order to extract the first memento URI from the list.

Other information is also available from this data structure.  Using .get("mementos").get("first").get("uri")[0] returns the first URI-M known for the given URI-R.  This data structure also contains the "timegate_uri" refering to the URI-G that was used for datetime negotiation during this session.  So backtracking is possible, the "original_uri" key is available to extract the URI-R again.

If the TimeGate has no Memento to return (i.e. the archive has no Memento for that URI-R), then the data structure returned only contains the "original_uri" and "timegate_uri" keys, as show below (as run in iPython):

```python
In [46]: mc = MementoClient(timegate_uri="http://timetravel.example.org/testing/timegate")

In [47]: mc.get_memento_info("http://www.cnn.com", dt)Out[47]:
{'original_uri': 'http://www.cnn.com',
 'timegate_uri': 'http://timetravel.example.org/testing/timegatehttp://www.cnn.com'}
```
