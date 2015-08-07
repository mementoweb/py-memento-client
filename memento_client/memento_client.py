"""
"""

__author__ = 'Harihar Shankar'


import requests
from datetime import datetime


DEFAULT_ARCHIVE_REGISTRY_URI = "http://labs.mementoweb.org/aggregator_config/archivelist.xml"
DEFAULT_TIMEGATE_BASE_URI = "http://timetravel.mementoweb.org/timegate/"
HTTP_DT_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"


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

    def get_archive_list(self, archive_registry_uri=DEFAULT_ARCHIVE_REGISTRY_URI):
        """
        This provides a list of archives and their corresponding timegates,
        so that one of them can be chosen as the preferred timegate.
        Retrieves a list of archives from the registry xml file, and provides the
        archive list along with their timegate uris.
        Use self.timegate_uri = "new timegate uri" to override the default timegate preference.

        :param archive_registry: (str) A valid base uri for the registry xml file.
        :return: (dict) A map of the archive id and their corresponding full name, timegate of the archive.
        """

        response = requests.get(archive_registry_uri)
        reg_data = response.content
        # parse xml
        archive_list = {"ia": {"name": "Internet Archive", "timegate_uri": "http://", "memento_status": "yes"}}

        return archive_list

    def get_memento_uri(self, original_uri, accept_datetime):
        """
        Given an original uri and an accept datetime, this method queries the
        preferred timegate and returns the closest memento uri, along with
        prev/next/first/last if available.

        :param original_uri: (str) The http uri of the original resource.
        :param accept_datetime: (datetime) The datetime object of the accept datetime.
        :return: (dict) A map of uri and datetime for the closest/prev/next/first/last mementos.
        """

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

        timegate_uri = native_tg if native_tg else self.timegate_uri + original_uri
        print("tg: " + timegate_uri)

        response = self.head_request(timegate_uri, accept_datetime=http_acc_dt, follow_redirects=True)

        #print response.headers
        link_header = response.headers.get("link")
        print link_header
        if not link_header:
            # TODO: create a "memento exception"
            raise Exception("The TimeGate (%s) did not return a Link header." % timegate_uri)

        links = self.parse_link_header(link_header)
        print
        print links
        mementos = self.get_uri_dt_for_rel(links, ["prev", "next", "first", "last"])

        closest_memento = response.url
        print closest_memento
        memento_uris = {}
        memento_uris["closest"] = {}
        memento_uris["closest"]["uri"] = closest_memento
        memento_uris["closest"]["datetime"] = self.convert_to_datetime(response.headers.get("Memento-Datetime"))
        for mem in mementos:
            memento_uris[mem] = {
                "uri": mementos.get(mem).get("uri"),
                "datetime": self.convert_to_datetime(mementos.get(mem).get("datetime")[0])
            }

        return memento_uris

    def get_native_timegate_uri(self, original_uri, accept_datetime):
        """
        Given an original URL and an accept datetime, check the original uri
        to see if the timegate uri is provided in the Link header.

        :param original_uri: (str) An HTTP uri of the original resource.
        :param accept_datetime: (datetime) The datetime object of the accept datetime
        :return: (str) The timegate uri of the original resource, if provided, else None.
        """

        org_response = self.head_request(original_uri, accept_datetime=self.convert_to_http_datetime(accept_datetime))

        def follow():
            print "following.. " + org_response.headers.get("Location")
            return self.get_native_timegate_uri(org_response.headers.get('Location'), accept_datetime)

        if org_response.headers.get("Vary") and 'accept-datetime' in org_response.headers.get('Vary'):
            print "vary acc-dt found for " + original_uri
            return

        if 'Memento-Datetime' in org_response.headers:
            print "mem-dt found for " + original_uri
            return

        if 299 < org_response.status_code < 400:
            # TODO: implement check for redirect loop, max_redirects=50?
            print "redirect.. " + original_uri
            return follow()

        if "Link" not in org_response.headers:
            print "no tg found.. " + original_uri
            return

        link_header = self.parse_link_header(org_response.headers.get("Link"))
        print(link_header)
        tg = self.get_uri_dt_for_rel(link_header, ["timegate"])
        return tg["timegate"].get("uri")

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
    res = mc.get_memento_uri("http://www.mementoweb.org/about/", dt)
