"""
"""

__author__ = 'Harihar Shankar'


import requests
from datetime import datetime


DEFAULT_ARCHIVE_REGISTRY_URI = "http://labs.mementoweb.org/aggregator_config/archivelist.xml"
DEFAULT_TIMEGATE_BASE_URI = "http://timetravel.mementoweb.org/timegate/%s"
HTTP_DT_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"


class MementoClient(object):

    def __init__(self,
                 archive_registry_uri=DEFAULT_ARCHIVE_REGISTRY_URI,
                 timegate_uri=DEFAULT_TIMEGATE_BASE_URI,
                 check_native_timegate=True):
        """

        :param archive_registry_uri:
        :param timegate_uri:
        :param check_memento_compliance:
        :return:
        """
        self.archive_registry_uri = archive_registry_uri
        self.timegate_uri = timegate_uri
        self.check_native_timegate = check_native_timegate

    def get_memento_uri(self, org_uri, accept_datetime, **kwargs):
        """

        :param org_uri: the http uri of the resource
        :param accept_datetime: (str/date)
        :param timegate_uri:
        :return:
        """

        if not org_uri or not accept_datetime:
            # TODO: error handling
            return

        if not org_uri.startswith("http://") \
                and not org_uri.startswith("https://"):
            # TODO: create a relevant exception...
            raise Exception("Only HTTP URIs are supported, URI %s unrecognized." % org_uri)

        if type(accept_datetime) != datetime:
            raise KeyError("Expecting accept_datetime to be of type datetime.")

        http_acc_dt = self.convert_to_http_datetime(accept_datetime)

        native_tg = None
        if self.check_native_timegate:
            native_tg = self.get_native_timegate_uri(org_uri, accept_datetime=accept_datetime)

        timegate_uri = native_tg if native_tg else self.timegate_uri % org_uri
        print("tg: " + timegate_uri)

        response = self.head_request(timegate_uri, accept_datetime=http_acc_dt)

        #print response.headers
        link_header = response.headers.get("link")
        #print link_header
        if not link_header:
            # TODO: create a "memento exception"
            raise Exception("The TimeGate (%s) did not return a Link header." % timegate_uri)

        links = self.parse_link_header(link_header)
        #print links
        mementos = self.get_uri_dt_for_rel(links,
                                           ["prev",
                                            "next",
                                            "first",
                                            "last"])

        closest_memento = response.headers.get("Location")
        #print closest_memento
        memento_uris = {}
        memento_uris["closest"] = {}
        memento_uris["closest"]["uri"] = closest_memento
        memento_uris["closest"]["datetime"] = self.convert_to_datetime(links.get(closest_memento).get("datetime")[0])
        for mem in mementos:
            memento_uris[mem] = {
                "uri": mementos.get(mem).get("uri"),
                "datetime": self.convert_to_datetime(mementos.get(mem).get("datetime")[0])
            }

        return memento_uris

    def get_native_timegate_uri(self, org_uri, accept_datetime):
        """
        Given an original URL and an accept datetime,
        recursively search for the appropriate TimeGate URL.

        :param org_uri:
        :param accept_datetime:
        :return:
        """

        org_response = self.head_request(org_uri, accept_datetime=self.convert_to_http_datetime(accept_datetime))

        def follow():
            print "following.. " + org_response.headers.get("Location")
            return self.get_native_timegate_uri(org_response.headers.get('Location'), accept_datetime)

        if org_response.headers.get("Vary") and 'accept-datetime' in org_response.headers.get('Vary'):
            print "vary acc-dt found for " + org_uri
            return

        if 'Memento-Datetime' in org_response.headers:
            print "mem-dt found for " + org_uri
            return

        if 299 < org_response.status_code < 400:
            # TODO: implement check for redirect loop, max_redirects=50?
            print "redirect.. " + org_uri
            return follow()

        if "Link" not in org_response.headers:
            print "no tg found.. " + org_uri
            return

        link_header = self.parse_link_header(org_response.headers.get("Link"))
        tg_uri = self.get_uri_dt_for_rel(link_header, "timegate")
        if tg_uri:
            return tg_uri[0][0]

    @staticmethod
    def convert_to_datetime(dt):
        """

        :param dt:
        :return:
        """
        if not dt:
            return
        return datetime.strptime(dt, HTTP_DT_FORMAT)

    @staticmethod
    def convert_to_http_datetime(dt):
        """

        :param dt:
        :return:
        """
        if not dt:
            return
        return dt.strftime(HTTP_DT_FORMAT)

    @staticmethod
    def get_uri_dt_for_rel(links, rel_types):
        """

        :param links:
        :param rel_types:
        :return:
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

        :param link:
        :return:
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
    def head_request(uri, accept_datetime):
        return requests.head(uri, headers={"Accept-Datetime": accept_datetime}, allow_redirects=False)


if __name__ == "__main__":
    mc = MementoClient()
    dt = mc.convert_to_datetime("Sun, 01 Apr 2010 12:00:00 GMT")
    res = mc.get_memento_uri("http://www.google.com", dt)
