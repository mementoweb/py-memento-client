"""
"""

from datetime import datetime

import requests
from datetime import datetime
import StringIO
from lxml import etree
import sys
import logging
import os
import re

# Python 2.7 and 3.X support are different for urlparse
if sys.version_info[0] == 3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

if os.environ.get('DEBUG_MEMENTO_CLIENT') == '1':
    logging.basicConfig(level=logging.DEBUG)

DEFAULT_ARCHIVE_REGISTRY_URI = "http://labs.mementoweb.org/aggregator_config/archivelist.xml"
DEFAULT_TIMEGATE_BASE_URI = "http://timetravel.mementoweb.org/timegate/"
HTTP_DT_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"

# non-compliant archive URI-M patterns
WEBCITE_PAT = re.compile("http[s]*://www.webcitation.org/[0-9A-Za-z]*")
WIKIPEDIA_PAT = re.compile("http[s]*://.*.wikipedia.org/w/index.php?.*oldid=[0-9]*")
WIKIA_PAT = re.compile("http[s]*://.*.wikia.com/wiki/.*oldid=[0-9]*")

class MementoClientException(Exception):

    def __init__(self, message, status_code, uri_r, uri_g, accept_datetime):
        super(MementoClientException, self).__init__(message)

        self.status_code = status_code
        self.uri_r = uri_r
        self.uri_g = uri_g
        self.accept_datetime = accept_datetime

class MementoClient(object):

    def __init__(self,
                 timegate_uri=DEFAULT_TIMEGATE_BASE_URI,
                 check_native_timegate=True):
        """
        Initialize with a preferred timegate base uri, thr default is the
        memento aggregator at http://timetravel.mementoweb.org/timegate/.
        Toggle check_native_timegate to see if the original uri has its own
        timegate. The native timegate, if found will be used instead of the
        timegate_uri preferred. If no native timegate is found, the preferred
        timegate_uri will be used.

        :param timegate_uri: (str) A valid HTTP base uri for a timegate. Must start with http(s):// and end with a /.
        :param check_memento_compliance: (boolean).
        :return: A MementoClient obj.
        """
        self.timegate_uri = timegate_uri
        self.check_native_timegate = check_native_timegate

    @staticmethod
    def get_archive_list(archive_registry_uri=DEFAULT_ARCHIVE_REGISTRY_URI):
        """
        This provides a list of archives and their corresponding timegates,
        so that one of them can be chosen as the preferred timegate.
        Retrieves a list of archives from the registry xml file, and provides the
        archive list along with their timegate uris.
        Use self.timegate_uri = "new timegate uri" to override the default timegate preference.

        :param archive_registry: (str) A valid base uri for the registry xml file.
        :return: (dict) A map of the archive id and their corresponding full name, timegate of the archive.
        """

        archive_list = {}
        response = requests.get(archive_registry_uri)
        # parse xml
        try:
            data = etree.parse(StringIO.StringIO(response.content))
        except:
            return archive_list

        for link in data.xpath("./link"):
            id = link.attrib["id"]
            name = link.attrib["longname"]
            timegate_uri = link.find("timegate").attrib["uri"]
            memento_status = link.find("archive").attrib["memento-status"]
            mem_status = False
            if memento_status == "yes":
                mem_status = True

            archive_list[id] = {"name": name,
                                "timegate_uri": timegate_uri,
                                "memento_status": mem_status,
                                }

        return archive_list

    def get_memento_info(self, original_uri, accept_datetime):
        """
        Given an original uri and an accept datetime, this method queries the
        preferred timegate and returns the closest memento uri, along with
        prev/next/first/last if available.

        :param original_uri: (str) The http uri of the original resource.
        :param accept_datetime: (datetime) The datetime object of the accept datetime.
        :return: (dict) A map of uri and datetime for the closest/prev/next/first/last mementos.
        """

        logging.debug("getting URI-R {0} at accept-datetime {1}!!!".format(original_uri, str(accept_datetime)))
        logging.debug("Starting with URI-G stem: " + self.timegate_uri)

        if not original_uri or not accept_datetime:
            # TODO: error handling
            return

        if not original_uri.startswith("http://") \
                and not original_uri.startswith("https://"):
            # TODO: create a relevant exception...
            raise Exception("Only HTTP URIs are supported, URI %s unrecognized." % original_uri)

        if type(accept_datetime) != datetime:
            raise KeyError("Expecting accept_datetime to be of type datetime.")

        http_acc_dt = self.convert_to_http_datetime(accept_datetime)

        native_tg = None
        if self.check_native_timegate:
            native_tg = self.get_native_timegate_uri(original_uri, accept_datetime=accept_datetime)
            logging.debug("Found native URI-G:  " + str(native_tg))

        timegate_uri = native_tg if native_tg else self.timegate_uri + original_uri

        logging.debug("Using URI-G: " + timegate_uri)

        response = self.head_request(timegate_uri, accept_datetime=http_acc_dt, follow_redirects=False)

        logging.debug("request method:  " + str(response.request.method))
        logging.debug("request URI:  " + str(response.request.url))
        logging.debug("request headers: " + str(response.request.headers))
        logging.debug("response status code: " + str(response.status_code))
        logging.debug("response headers:  " + str(response.headers))


        if (response.status_code != 302 and response.status_code != 200 ):
            raise MementoClientException("""
TimeGate did not respond with a 302 redirect or 200 OK HTTP status code
URI-R:  {0}
URI-G stem:  {1}
URI-G:  {2}
Accept-Datetime:  {3}
Status code received: {4}
""".format(original_uri, self.timegate_uri, timegate_uri, str(http_acc_dt), response.status_code),
    response.status_code, original_uri, timegate_uri, accept_datetime)

        uri_m = response.headers.get("location")

        logging.debug("received URI-M:  " + uri_m)

        # sometimes we get relative URI-Ms, which have no scheme
        if not urlparse(uri_m).scheme:
            uri_m = urlparse(timegate_uri).scheme + "://" + urlparse(timegate_uri).netloc + uri_m

        logging.debug("location:  " + response.headers.get("location"))
        logging.debug("using URI-M:  " + uri_m)

        memento_info = {}
        memento_info["closest"] = {}
        memento_info["closest"]["uri"] = uri_m

        link_header = response.headers.get("link")

        logging.debug("link header:  " + str(link_header))

        if not link_header:
            # TODO: create a "memento exception"
            raise Exception("The TimeGate (%s) did not return a Link header." % timegate_uri)

        links = self.parse_link_header(link_header)
        logging.debug("link header:  " + str(links))

        mementos = self.get_uri_dt_for_rel(links, ["prev", "next", "first", "last"])

        memento_uris = {}

        for mem in mementos:
            memento_uris[mem] = {
                "uri": mementos.get(mem).get("uri"),
                "datetime": self.convert_to_datetime(mementos.get(mem).get("datetime")[0])
            }

        return memento_info

    def get_native_timegate_uri(self, original_uri, accept_datetime):
        """
        Given an original URL and an accept datetime, check the original uri
        to see if the timegate uri is provided in the Link header.

        :param original_uri: (str) An HTTP uri of the original resource.
        :param accept_datetime: (datetime) The datetime object of the accept datetime
        :return: (str) The timegate uri of the original resource, if provided, else None.
        """

        org_response = self.head_request(original_uri, accept_datetime=self.convert_to_http_datetime(accept_datetime))

        logging.debug("Request headers sent to search for URI-G:  " + str(org_response.request.headers))

        def follow():
            logging.debug("Following to new URI of " + org_response.headers.get("Location"))
            return self.get_native_timegate_uri(org_response.headers.get('Location'), accept_datetime)

        if org_response.headers.get("Vary") and 'accept-datetime' in org_response.headers.get('Vary'):
            logging.debug("Vary header with Accept-Datetime found for URI-R: " + original_uri)
            return

        if 'Memento-Datetime' in org_response.headers:
            logging.debug("Memento-Datetime found in headers for URI-R: {0}, so assuming it is a URI-M.".format(original_uri))
            return

        if 299 < org_response.status_code < 400:
            # TODO: implement check for redirect loop, max_redirects=50?
            logging.debug("Been redirected from URI-R: " + original_uri)
            return follow()

        if "Link" not in org_response.headers:
            logging.debug("No URI-G found for URI-R: " + original_uri)
            return

        logging.debug("Received raw Link header:  " + str(org_response.headers.get("Link")))

        link_header = self.parse_link_header(org_response.headers.get("Link"))
        logging.debug("Received Link header:  " + str(link_header))
        tg = self.get_uri_dt_for_rel(link_header, ["timegate"])

        tg_uri = None

        if "timegate" in tg:
            tg_uri = tg["timegate"].get("uri")

        logging.debug("Search for native URI-G yielded:  " + str(tg_uri))

        return tg_uri

    def determine_if_memento(self, uri):
        """
        Determines if the URI given is indeed a Memento.  The simple case is to
        look for a Memento-Datetime header in the request, but not all
        archives are Memento-compliant yet.

        :param uri: (str) an HTTP URI for testing
        :return: (bool) True if a Memento, False otherwise
        """

        response = requests.head(uri, allow_redirects=False)

        if 'Memento-Datetime' in response.headers:

            if 'Link' in response.headers:

                logging.debug(
                    "Memento-Datetime found in headers for URI-R: {0}, so assuming it is a URI-M.".format(uri))
            return True

        # now the ugly kludges for sites that are not Memento-compliant

        webcite_results = WEBCITE_PAT.findall(uri)

        if len(webcite_results) > 0:
            if webcite_results[0] == uri:
                """
                    Everything from webcitation should be a URI-M.

                    There are some exceptions, but we do not know how to determine it.
                """
                return True

        wikipedia_results = WIKIPEDIA_PAT.findall(uri)
       
        if len(wikipedia_results) > 0:
            if wikipedia_results[0] == uri:
                """
                    Wikipedia oldid pages are URI-Ms in their own right.

                    Once they install the Memento extension, we should remove this code.
                """
                return True

        wikia_results = WIKIA_PAT.findall(uri)

        if len(wikia_results) > 0:
            if wikia_results[0] == uri:
                """
                    Just like Wikipedia, Wikia is a MediaWiki installation(s).

                    Once they install the Memento extension, we should remove this code.
                """
                return True

        return False

    @staticmethod
    def convert_to_datetime(dt):
        """
        Converts a date string in the HTTP date format to a datetime obj.
        eg: "Sun, 01 Apr 2010 12:00:00 GMT" -> datetime()
        :param dt: (str) The date string in HTTP date format.
        :return: (datetime) The datetime object of the string.
        """
        if not dt:
            return
        return datetime.strptime(dt, HTTP_DT_FORMAT)

    @staticmethod
    def convert_to_http_datetime(dt):
        """
        Converts a datetime object to a date string in HTTP format.
        eg: datetime() -> "Sun, 01 Apr 2010 12:00:00 GMT"
        :param dt: (datetime) A datetime object.
        :return: (str) The date in HTTP format.
        """
        if not dt:
            return
        return dt.strftime(HTTP_DT_FORMAT)

    @staticmethod
    def get_uri_dt_for_rel(links, rel_types):
        """
        Returns the uri and the datetime (if available) for a rel type from the
        parsed link header object.
        :param links: (dict) the output of parse_link_header.
        :param rel_types: (list) a list of rel types for which the uris should be found.
        :return: (dict) {rel: {"uri": "", "datetime": }}
        """
        uris = {}
        for uri in links:
            for rel in rel_types:
                if rel in links.get(uri).get("rel"):
                    uris[rel] = {"uri": uri, "datetime": links.get(uri).get("datetime")}
        return uris

    @staticmethod
    def parse_link_header(link):
        """
        Parses the link header character by character.
        More robust than the parser provided by the requests module.

        :param link: (str) The HTTP link header as a string.
        :return: (dict) {"uri": {"rel": ["", ""], "datetime": [""]}...}
        """

        state = 'start'
        #header = link.strip()
        #data = [d for d in header]
        data = list(link.strip())
        links = {}
        d_count = 0

        while data:
            if state == 'start':
                d = data.pop(0)
                d_count += 1
                while d.isspace():
                    d = data.pop(0)
                    d_count += 1

                if d != "<":
                    raise ValueError("Parsing Link Header: Expected < in start, got %s" % d)

                state = "uri"
            elif state == "uri":
                uri = []
                d = data.pop(0)
                d_count += 1

                while d != ";":
                    uri.append(d)
                    d = data.pop(0)

                uri = ''.join(uri)
                uri = uri[:-1]
                data.insert(0, ';')

                # Not an error to have the same URI multiple times (I think!)
                if uri not in links:
                    links[uri] = {}
                state = "paramstart"
            elif state == 'paramstart':
                d = data.pop(0)
                d_count += 1

                while data and d.isspace():
                    d = data.pop(0)
                    d_count += 1
                if d == ";":
                    state = 'linkparam'
                elif d == ',':
                    state = 'start'
                else:
                    raise ValueError("Parsing Link Header: Expected ; in paramstart, got %s" % d)
            elif state == 'linkparam':
                d = data.pop(0)
                d_count += 1
                while d.isspace():
                    d = data.pop(0)
                    d_count += 1
                paramType = []
                while not d.isspace() and d != "=":
                    paramType.append(d)
                    d = data.pop(0)
                    d_count += 1
                while d.isspace():
                    d = data.pop(0)
                    d_count += 1
                if d != "=":
                    raise ValueError("Parsing Link Header: Expected = in linkparam, got %s" % d)
                state = 'linkvalue'
                pt = ''.join(paramType)

                if pt not in links[uri]:
                    links[uri][pt] = []
            elif state == 'linkvalue':
                d = data.pop(0)
                d_count += 1
                while d.isspace():
                    d = data.pop(0)
                    d_count += 1
                paramValue = []
                if d == '"':
                    pd = d
                    d = data.pop(0)
                    d_count += 1
                    while d != '"' and pd != '\\':
                        paramValue.append(d)
                        pd = d
                        d = data.pop(0)
                        d_count += 1
                else:
                    while not d.isspace() and d not in (',', ';'):
                        paramValue.append(d)
                        if data:
                            d = data.pop(0)
                            d_count += 1
                        else:
                            break
                    if data:
                        data.insert(0, d)
                state = 'paramstart'
                pv = ''.join(paramValue)
                if pt == 'rel':
                    # rel types are case insensitive and space separated
                    links[uri][pt].extend([y.lower() for y in pv.split(' ')])
                else:
                    if pv not in links[uri][pt]:
                        links[uri][pt].append(pv)

        return links

    @staticmethod
    def head_request(uri, accept_datetime, follow_redirects=False):
        """
        Makes HEAD requests.
        :param uri: (str) the uri for the request.
        :param accept_datetime: (str) the accept-datetime in the http format.
        :param follow_redirects: (boolean) Toggle to follow redirects. False by default,
        so does not follow any redirects.
        :return: the response object.
        """
        return requests.head(uri, headers={"Accept-Datetime": accept_datetime}, allow_redirects=follow_redirects)


if __name__ == "__main__":
    mc = MementoClient()
    dt = mc.convert_to_datetime("Sun, 01 Apr 2010 12:00:00 GMT")
    res = mc.get_memento_uri("http://dbpedia.org/page/Berlin", dt)
