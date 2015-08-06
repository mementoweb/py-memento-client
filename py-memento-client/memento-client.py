"""
"""

__author__ = 'Harihar Shankar'

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

        :param org_uri:
        :param accept_datetime:
        :param timegate_uri:
        :return:
        """

        if not org_uri or not accept_datetime:
            # TODO: error handling
            return

        timegate_uri = self.timegate_uri
        if self.check_native_timegate:
            timegate_uri = self.get_native_timegate_uri(org_uri, accept_datetime)

        # do head on timegate link
        # return memento uri from link header
        # {"first": "",
        # "prev": "",
        # "next": "",
        # "}

    def get_native_timegate_uri(self, org_uri, accept_datetime):
        """
        Given an original URL and a target datetime,
        recursively search for the appropriate Memento URL.

        :param org_uri:
        :param accept_datetime:
        :return:
        """

        is_timegate = False

        # START
        # HEAD URI-Q with Accept-Datetime value
        # Go to TEST-0
        response = get_headers(org_uri,
            headers={'Accept-Datetime':accept_datetime})

        # FOLLOW
        # URI-Q = Location (value of HTTP header)
        # Go to START
        def follow():
            return get_memento_url(response.headers['Location'], accept_datetime)

        # TEST-0
        # IF the response from URI-Q contains "Vary: accept-datetime"
        #    SET TG-FLAG=TRUE
        #    SET URI-R=URI-Q
        # Go to TEST-1
        if 'accept-datetime' in response.headers['Vary']:
        is_timegate=True
        original_url = org_uri

        # TEST-1
        # Is URI-Q a Memento?
        #         YES =>
        #                 TG-FLAG=FALSE
        #                 SET URI-R=blank
        #                 Is the response from URI-Q a 3XX?
        #                        YES => Go to FOLLOW
        #                        NO   => STOP SUCCESS
        #         NO => Go to TEST-2
        if 'Memento-Datetime' in response.headers:
        is_timegate = False
        original_url = None
        if response.response_code.startswith('3'):
            return follow()
        else:
            return org_uri

        # TEST-2 (the poor man's version)
        # Is the response from URI-Q a 3XX?
        #         YES => Go to FOLLOW
        #         NO   => Go to TEST-3
        if response.response_code.startswith('3'):
            return follow()

        # TEST-2 (the rich man's version)
        # Is the response from URI-Q a 3XX?
        #         YES =>
        #                 Is TG-FLAG=TRUE?
        #                         YES => Go to FOLLOW
        #                         NO   => CASE O1 302 O2. How does the
        #                user agent handle this?
        #         NO => Go to TEST-3
        if response.response_code.startswith('3'):
        if is_timegate:
            return follow()
        else:
            raise NotImplementedError()

        # TEST-3
        # Is TG-FLAG=TRUE AND Is the response from URI-Q a 4XX or 5XX?
        #         YES => CASE TimeGate or Memento error. How does the user
                agent handle this?
        #         NO   => Go to TEST-4
        if is_timegate and (response.response_code.startswith('4') or
            response.response_code.startswith('5')):
        # TimeGate or Memento error
        raise HttpError()

        # TEST-4
        # Does the response from URI-Q have a "timegate" link pointing at URI-G?
        #    SET TG-FLAG=TRUE
        #    SET URI-R=URI-Q
        #    YES => SET URI-Q=URI-G
        #    NO   => SET URI-Q=URI of the user agent's preferred TimeGate
        #    Go to START
        is_timegate = True
        original_url = org_uri
        new_input_url = response.links.get('timegate', DEFAULT_TIMEGATE+org_uri)
        return get_memento_url(new_input_url, accept_datetime)

