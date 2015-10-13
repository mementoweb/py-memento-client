"""
A Memento Client library.

"""

import requests
from datetime import datetime
import sys
import logging
import os


# Python 2.7 and 3.X support are different for urlparse
if sys.version_info[0] == 3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

if os.environ.get('DEBUG_MEMENTO_CLIENT') == '1':
    logging.basicConfig(level=logging.DEBUG)

DEFAULT_TIMEGATE_BASE_URI = "http://timetravel.mementoweb.org/timegate/"
HTTP_DT_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"
MAX_REDIRECTS = 30


class MementoClientException(Exception):
    """
    The memento client Exception class.
    """

    def __init__(self, message, data):
        super(MementoClientException, self).__init__(message)
        self.data = data


class MementoClient(object):
    """
    A memento client.
    """

    def __init__(self,
                 timegate_uri=DEFAULT_TIMEGATE_BASE_URI,
                 check_native_timegate=True,
                 max_redirects=MAX_REDIRECTS):
        """
        A Memento Client that makes it straightforward to access the Web of the
         past as it is to access the current Web.
        Basic usage:
        >>> mc = MementoClient()
        >>> dt = mc.convert_to_datetime("Sun, 01 Apr 2010 12:00:00 GMT")
        >>> mc = mc.get_memento_info("http://www.bbc.com/", dt)
        >>> print(mc)
        {'mementos': {'closest': {
        'datetime': datetime.datetime(2010, 5, 23, 10, 19, 6),
        'http_status_code': 200,
        'uri': [u'http://web.archive.org/web/20100523101906/
        http://www.bbc.co.uk/']},
        'first': {'datetime': datetime.datetime(1998, 12, 2, 21, 26, 10),
        'uri': ['http://web.archive.bibalex.org/web/19981202212610/
        http://bbc.com/']},
        'last': {'datetime': datetime.datetime(2015, 8, 7, 21, 59, 59),
        'uri': ['http://wayback.archive-it.org/all/20150807215959/
        http://www.bbc.com/']}},
        'original_uri': 'http://www.bbc.com/',
        'timegate_uri': 'http://timetravel.mementoweb.org/timegate/
        http://www.bbc.com/'}
        The output conforms to the Memento API format explained here:
        http://timetravel.mementoweb.org/guide/api/#memento-json

        By default, MementoClient uses the Memento Aggregator:
        http://mementoweb.org/depot/
        It is also possible to use different TimeGate, simply initialize
        with a preferred timegate base uri.
        Toggle check_native_timegate to see if the original uri has its own
        timegate. The native timegate, if found will be used instead of the
        timegate_uri preferred. If no native timegate is found, the preferred
        timegate_uri will be used.

        :param timegate_uri: (str) A valid HTTP base uri for a timegate.
                            Must start with http(s):// and end with a /.
        :param max_redirects: (int) the maximum number of redirects allowed
                              for all HTTP requests to be made.
        :return: A MementoClient obj.
        """
        self.timegate_uri = timegate_uri
        self.check_native_timegate = check_native_timegate
        self.native_redirect_count = 0
        self.max_redirects = max_redirects

    def get_memento_info(self, request_uri, accept_datetime=None):
        """
        Given an original uri and an accept datetime, this method queries the
        preferred timegate and returns the closest memento uri, along with
        prev/next/first/last if available.

        The response format is explained here:
        http://timetravel.mementoweb.org/guide/api/#memento-json

        :param request_uri: (str) The input http uri.
        :param accept_datetime: (datetime) The datetime object of the accept
                                datetime. The current datetime is used if none
                                is provided.
        :return: (dict) A map of uri and datetime for the
                 closest/prev/next/first/last mementos.
        """

        if not accept_datetime:
            accept_datetime = datetime.now()

        logging.debug("getting URI-R {0} at accept-datetime {1}!!!".
                      format(request_uri, str(accept_datetime)))
        logging.debug("Starting with URI-G stem: " + self.timegate_uri)

        assert request_uri and accept_datetime
        # if not request_uri or not accept_datetime:
        #     raise MementoClientException(
        # "No uri or accept datetime was provided to retrieve mementos.", {})

        if not request_uri.startswith("http://") \
                and not request_uri.startswith("https://"):
            raise ValueError("Only HTTP URIs are supported, "
                             "URI %s unrecognized." % request_uri)

        if type(accept_datetime) != datetime:
            raise TypeError("Expecting accept_datetime to be of type "
                            "datetime.")

        http_acc_dt = self.convert_to_http_datetime(accept_datetime)

        # finding the actual original_uri in case the input uri is a memento
        original_uri = self.get_original_uri(request_uri)
        logging.debug("original uri: " + original_uri)

        native_tg = None
        if self.check_native_timegate:
            native_tg = self.get_native_timegate_uri(
                original_uri, accept_datetime=accept_datetime)
            logging.debug("Found native URI-G:  " + str(native_tg))

        timegate_uri = native_tg if native_tg \
            else self.timegate_uri + original_uri

        logging.debug("Using URI-G: " + timegate_uri)

        response = self.request_head(timegate_uri,
                                     accept_datetime=http_acc_dt,
                                     follow_redirects=True)

        logging.debug("request method:  " + str(response.request.method))
        logging.debug("request URI:  " + str(response.request.url))
        logging.debug("request headers: " + str(response.request.headers))
        logging.debug("response status code: " + str(response.status_code))
        logging.debug("response headers:  " + str(response.headers))

        uri_m = response.url
        dt_m = None
        link_header = None
        mem_status = response.status_code

        # getting the memento datetime from the memento response headers
        if self.is_memento(uri_m, response=response):
            dt_m = self.convert_to_datetime(
                response.headers.get("Memento-Datetime"))
            # link_header = response.headers.get("Link")

        # getting the next, prev, etc from the timegate reponse headers
        # so that these headers not locked in any one archive
        # when using the aggr.
        for res in response.history:
            if self.is_timegate(timegate_uri, response=res):
                logging.debug("found URI-M from timegate response:  " + uri_m)
                logging.debug("timegate uri: " + res.url)

                # sometimes we get relative URI-Ms, which have no scheme
                if not urlparse(uri_m).scheme:
                    uri_m = urlparse(timegate_uri).scheme + "://" \
                        + urlparse(timegate_uri).netloc + uri_m

                link_header = res.headers.get("link")
                logging.debug("link header:  " + str(link_header))

                if not link_header:
                    raise MementoClientException(
                        "The TimeGate (%s) did not return a Link header." %
                        timegate_uri,
                        {"timegate_uri": timegate_uri,
                         "original_uri": original_uri,
                         "request_uri": request_uri,
                         "memento_uri": uri_m})
                break

        memento_info = {}
        memento_info["original_uri"] = original_uri
        memento_info["timegate_uri"] = timegate_uri

        if not uri_m or not link_header:
            return memento_info
        memento_info.update(
            self.__prepare_memento_response(uri_m=uri_m, dt_m=dt_m,
                                            link_header=link_header,
                                            status_code=mem_status))
        return memento_info

    def get_native_timegate_uri(self, original_uri, accept_datetime):
        """
        Given an original URL and an accept datetime, check the original uri
        to see if the timegate uri is provided in the Link header.

        :param original_uri: (str) An HTTP uri of the original resource.
        :param accept_datetime: (datetime) The datetime object of the accept
                                datetime
        :return: (str) The timegate uri of the original resource, if provided,
                 else None.
        """

        try:
            org_response = self.request_head(
                original_uri, accept_datetime=self.convert_to_http_datetime(
                    accept_datetime))

            logging.debug("Request headers sent to search for URI-G:  " +
                          str(org_response.request.headers))

            def follow():
                """
                a recursive func to follow redirects.
                """
                logging.debug("Following to new URI of " +
                              org_response.headers.get("Location"))
                return self.get_native_timegate_uri(
                    org_response.headers.get('Location'), accept_datetime)

            if org_response.headers.get("Vary") and\
                    'accept-datetime' in org_response.headers.get('Vary').lower():
                logging.debug("Vary header with Accept-Datetime found for URI-R: "
                              + original_uri)
                return

            if 'Memento-Datetime' in org_response.headers:
                logging.debug("Memento-Datetime found in headers for URI-R: {0},"
                              " so assuming it is a URI-M.".
                              format(original_uri))
                return

            if 299 < org_response.status_code < 400 \
                    and self.native_redirect_count < self.max_redirects:
                logging.debug("Been redirected from URI-R: " + original_uri)
                self.native_redirect_count += 1
                return follow()

            if "Link" not in org_response.headers:
                logging.debug("No URI-G found for URI-R: " + original_uri)
                return

            logging.debug("Received raw Link header:  " +
                          str(org_response.headers.get("Link")))

            link_header = self.parse_link_header(org_response.headers.get("Link"))
            logging.debug("Received Link header:  " + str(link_header))
            tg = self.get_uri_dt_for_rel(link_header, ["timegate"])

            tg_uri = None

            if "timegate" in tg:
                tg_uri = tg["timegate"].get("uri")

            logging.debug("Search for native URI-G yielded:  " + str(tg_uri))

            return tg_uri

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError) as e:
            logging.warning("Could not connect to URI {},"
                            " returning no native URI-G".format(original_uri))
            return

    def get_original_uri(self, request_uri):
        """
        Returns the original uri of the given request uri. Checks for
        rel=original in the response headers of the request uri.
        Useful when the request uri is a memento, so that the original uri
        can be used to for the timegate, instead of the memento uri.
        :param request_uri: the requested http uri.
        :return: (str) the original uri
        """

        try:
            response = self.request_head(request_uri, accept_datetime=None,
                                         follow_redirects=True)
            if response.headers.get("Link"):
                link_header = response.headers.get("Link")
                links = self.parse_link_header(link_header)
                org = self.get_uri_dt_for_rel(links, ["original"])
                if org.get("original"):
                    logging.debug("Org URI from request uri headers: " + repr(org))
                    return org.get("original").get("uri")

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError) as e:
            logging.warning(
                "Could not connect to {},"
                " using it as original URI".format(request_uri))

        return request_uri

    @staticmethod
    def is_timegate(uri, accept_datetime=None, response=None):
        """
        Checks if the given uri is a valid timegate according to the RFC.
        :param uri: the http uri to check.
        :param accept_datetime: (str)[optional] the accept datetime string in
                                http date format.
        :param response: (request's response obj)[optional] the response
                            object of the uri.
        :return: (bool) True if a valid timegate, else False.
        """

        if not response:
            if not accept_datetime:
                accept_datetime = MementoClient.convert_to_http_datetime(
                    datetime.now())

            response = MementoClient.request_head(
                uri, accept_datetime=accept_datetime)

        if response.status_code != 302 and response.status_code != 200:
            raise MementoClientException("""
TimeGate did not respond with a 302 redirect or 200 OK HTTP status code
URI:  {0}
Accept-Datetime:  {1}
Status code received: {2}
        """.format(uri, accept_datetime, str(response.status_code)),
                                         {"status_code": response.status_code,
                                          "timegate_uri": uri,
                                          "accept_datetime": accept_datetime})

        links = MementoClient.parse_link_header(response.headers.get("Link"))
        original_uri = MementoClient.get_uri_dt_for_rel(links, ["original"])

        if response.headers.get("Vary") \
                and "accept-datetime" in response.headers.get("Vary").lower() \
                and original_uri and response.headers.get("Location"):
            return True

        return False

    @staticmethod
    def is_memento(uri, response=None):
        """
        Determines if the URI given is indeed a Memento.  The simple case is to
        look for a Memento-Datetime header in the request, but not all
        archives are Memento-compliant yet.

        :param uri: (str) an HTTP URI for testing
        :param response: (request's response obj)[optional] the response object
                            of the uri.
        :return: (bool) True if a Memento, False otherwise
        """

        if not response:
            response = requests.head(uri, allow_redirects=False)

        if 'Memento-Datetime' in response.headers:

            if 'Link' in response.headers:

                links = MementoClient.parse_link_header(response.headers.get("Link"))

                rels = MementoClient.get_uri_dt_for_rel(links, ["original"])

                if 'original' in rels:
                    logging.debug("Memento-Datetime found in headers for"
                                  " URI-R: {0}, so assuming it is a URI-M.".
                                  format(uri))

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
        :param rel_types: (list) a list of rel types for which the uris
                            should be found.
        :return: (dict) {rel: {"uri": "", "datetime": }}
        """
        if not links or not rel_types:
            return

        uris = {}
        for uri in links:
            for rel in rel_types:
                if rel in links.get(uri).get("rel"):
                    uris[rel] = {"uri": uri,
                                 "datetime": links.get(uri).get("datetime")}
        return uris

    @staticmethod
    def parse_link_header(link):
        """
        Parses the link header character by character.
        More robust than the parser provided by the requests module.

        :param link: (str) The HTTP link header as a string.
        :return: (dict) {"uri": {"rel": ["", ""], "datetime": [""]}...}
        """

        if not link:
            return
        state = 'start'
        data = list(link.strip())
        links = {}

        while data:
            if state == 'start':
                dat = data.pop(0)
                while dat.isspace():
                    dat = data.pop(0)

                if dat != "<":
                    raise ValueError("Parsing Link Header: Expected < in "
                                     "start, got %s" % dat)

                state = "uri"
            elif state == "uri":
                uri = []
                dat = data.pop(0)

                while dat != ";":
                    uri.append(dat)
                    dat = data.pop(0)

                uri = ''.join(uri)
                uri = uri[:-1]
                data.insert(0, ';')

                # Not an error to have the same URI multiple times (I think!)
                if uri not in links:
                    links[uri] = {}
                state = "paramstart"
            elif state == 'paramstart':
                dat = data.pop(0)

                while data and dat.isspace():
                    dat = data.pop(0)
                if dat == ";":
                    state = 'linkparam'
                elif dat == ',':
                    state = 'start'
                else:
                    raise ValueError("Parsing Link Header: Expected ;"
                                     " in paramstart, got %s" % dat)
            elif state == 'linkparam':
                dat = data.pop(0)
                while dat.isspace():
                    dat = data.pop(0)
                param_type = []
                while not dat.isspace() and dat != "=":
                    param_type.append(dat)
                    dat = data.pop(0)
                while dat.isspace():
                    dat = data.pop(0)
                if dat != "=":
                    raise ValueError("Parsing Link Header: Expected = in"
                                     " linkparam, got %s" % dat)
                state = 'linkvalue'
                pt = ''.join(param_type)

                if pt not in links[uri]:
                    links[uri][pt] = []
            elif state == 'linkvalue':
                dat = data.pop(0)
                while dat.isspace():
                    dat = data.pop(0)
                param_value = []
                if dat == '"':
                    pd = dat
                    dat = data.pop(0)
                    while dat != '"' and pd != '\\':
                        param_value.append(dat)
                        pd = dat
                        dat = data.pop(0)
                else:
                    while not dat.isspace() and dat not in (',', ';'):
                        param_value.append(dat)
                        if data:
                            dat = data.pop(0)
                        else:
                            break
                    if data:
                        data.insert(0, dat)
                state = 'paramstart'
                pv = ''.join(param_value)
                if pt == 'rel':
                    # rel types are case insensitive and space separated
                    links[uri][pt].extend([y.lower() for y in pv.split(' ')])
                else:
                    if pv not in links[uri][pt]:
                        links[uri][pt].append(pv)

        return links

    @staticmethod
    def request_head(uri, accept_datetime=None, follow_redirects=False):
        """
        Makes HEAD requests.
        :param uri: (str) the uri for the request.
        :param accept_datetime: (str) the accept-datetime in the http format.
        :param follow_redirects: (boolean) Toggle to follow redirects.
                                 False by default,
        so does not follow any redirects.
        :return: the response object.
        """
        headers = {}
        if accept_datetime:
            headers["Accept-Datetime"] = accept_datetime
        return requests.head(uri, headers=headers,
                             allow_redirects=follow_redirects)

    def __prepare_memento_response(self, uri_m=None, dt_m=None,
                                   link_header=None, status_code=None):
        """
        Prepares the response for the get_memento_info function.
        :param uri_m: (str) the memento uri
        :param dt_m: (datetime) the memento datetime
        :param links: (str) the link header from the memento/timegate response
        :param status_code: (int) the http status code of the memento.
        :return: (dict) a map of the mementos found.
        """

        logging.debug("Preparing memento response.")
        memento_info = {}
        memento_info["mementos"] = {}

        memento_info["mementos"]["closest"] = {}
        memento_info["mementos"]["closest"]["uri"] = [uri_m]
        memento_info["mementos"]["closest"]["http_status_code"] = status_code

        links = self.parse_link_header(link_header)
        mementos = self.get_uri_dt_for_rel(links,
                                           ["prev", "next", "first", "last"])
        if not dt_m and uri_m in links:
            if "datetime" in links.get(uri_m):
                dt_m = self.convert_to_datetime(links.get(uri_m).
                                                get("datetime")[0])
        memento_info["mementos"]["closest"]["datetime"] = dt_m

        for mem in mementos:
            memento_info["mementos"][mem] = {
                "uri": [mementos.get(mem).get("uri")],
                "datetime": self.convert_to_datetime(mementos.get(mem).
                                                     get("datetime")[0])
            }
        logging.debug("The full response: " + repr(memento_info))
        return memento_info
