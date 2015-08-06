"""
"""

__author__ = 'Harihar Shankar'


import requests
from datetime import datetime


DEFAULT_ARCHIVE_REGISTRY_URI = "http://labs.mementoweb.org/aggregator_config/archivelist.xml"
DEFAULT_TIMEGATE_BASE_URI = "http://timetravel.mementoweb.org/timegate/"


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

    def get_memento_uri(self, org_uri, accept_datetime):
        """

        :param org_uri: the http uri of the resource
        :param accept_datetime: (str/date)
        :param timegate_uri:
        :return:
        """

        if not org_uri or not accept_datetime:
            # TODO: error handling
            return

        if type(accept_datetime) != datetime:
            raise KeyError("Expecting accept_datetime to be of type datetime")


        #timegate_uri = self.timegate_uri
        native_tg = None
        if self.check_native_timegate:
            native_tg = self.get_native_timegate_uri(org_uri, accept_datetime=accept_datetime)

        timegate_uri = native_tg if native_tg else self.timegate_uri

        response = self.__head_request(timegate_uri, accept_datetime=accept_datetime)
        # do head on timegate link
        # return memento uri from link header
        # {"first": "",
        # "prev": "",
        # "next": "",
        # "closest": {"dt": datetime obj, "uri": "http://"},
        # "}

    def get_native_timegate_uri(self, org_uri, accept_datetime):
        """
        Given an original URL and a target datetime,
        recursively search for the appropriate Memento URL.

        :param org_uri:
        :param accept_datetime:
        :return:
        """

        #is_timegate = False
        org_response = self.__head_request(org_uri, accept_datetime=accept_datetime)
        # START
        # HEAD URI-Q with Accept-Datetime value
        # Go to TEST-0

        # FOLLOW
        # URI-Q = Location (value of HTTP header)
        # Go to START
        def follow():
            print "following.. " + org_response.headers.get("Location")
            return self.get_native_timegate_uri(org_response.headers.get('Location'), accept_datetime)

        # TEST-0
        # IF the response from URI-Q contains "Vary: accept-datetime"
        #    SET TG-FLAG=TRUE
        #    SET URI-R=URI-Q
        # Go to TEST-1
        if org_response.headers.get("Vary") and 'accept-datetime' in org_response.headers.get('Vary'):
            print "vary acc-dt found for " + org_uri
            return org_uri
            #is_timegate=True
            #original_url = org_uri

        # TEST-1
        # Is URI-Q a Memento?
        #         YES =>
        #                 TG-FLAG=FALSE
        #                 SET URI-R=blank
        #                 Is the response from URI-Q a 3XX?
        #                        YES => Go to FOLLOW
        #                        NO   => STOP SUCCESS
        #         NO => Go to TEST-2
        if 'Memento-Datetime' in org_response.headers:
            print "mem-dt found for " + org_uri
            return org_uri
            #is_timegate = False
            #original_url = None
            #if response.response_code.startswith('3'):
            #return follow()
            #else:
            #return org_uri

        # TEST-2 (the poor man's version)
        # Is the response from URI-Q a 3XX?
        #         YES => Go to FOLLOW
        #         NO   => Go to TEST-3
        #if response.response_code.startswith('3'):
        #    return follow()

        # TEST-2 (the rich man's version)
        # Is the response from URI-Q a 3XX?
        #         YES =>
        #                 Is TG-FLAG=TRUE?
        #                         YES => Go to FOLLOW
        #                         NO   => CASE O1 302 O2. How does the
        #                user agent handle this?
        #         NO => Go to TEST-3
        if 299 < org_response.status_code < 400:
            # TODO: implement check for redirect loop, max_redirects=50?
            print "redirect.. " + org_uri
            return follow()

        # TEST-3
        # Is TG-FLAG=TRUE AND Is the response from URI-Q a 4XX or 5XX?
        #         YES => CASE TimeGate or Memento error. How does the user
        # agent handle this?
        #         NO   => Go to TEST-4
        #if is_timegate and (response.response_code.startswith('4') or
        #                        response.response_code.startswith('5')):
        # TimeGate or Memento error
        #raise HttpError()

        # TEST-4
        # Does the response from URI-Q have a "timegate" link pointing at URI-G?
        #    SET TG-FLAG=TRUE
        #    SET URI-R=URI-Q
        #    YES => SET URI-Q=URI-G
        #    NO   => SET URI-Q=URI of the user agent's preferred TimeGate
        #    Go to START

        if "Link" not in org_response.headers:
            print "no tg found.. " + org_uri
            return org_uri

        link_header = self.parse_link_header(org_response.headers.get("Link"))
        return self.get_uri_for_rel(link_header, "timegate")

    @staticmethod
    def get_uri_for_rel(links, rel):
        for uri in links:
            if rel in links.get(uri).get("rel"):
                return uri

    @staticmethod
    def parse_link_header(link):

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


    def __head_request(self, uri, accept_datetime):
        return requests.head(uri, headers={"Accept-Datetime": accept_datetime}, allow_redirects=False)