"""
Contains helper methods for the memento client.
"""

from lxml import etree
import requests
import sys

# Python 2.7 and 3.X support are different for urlparse
if sys.version_info[0] == 3:
    from io import StringIO
else:
    import StringIO


DEFAULT_ARCHIVE_REGISTRY_URI = \
    "http://labs.mementoweb.org/aggregator_config/archivelist.xml"


def get_archive_list(archive_registry_uri=DEFAULT_ARCHIVE_REGISTRY_URI):
    """
    This provides a list of archives and their corresponding timegates,
    so that one of them can be chosen as the preferred timegate.
    Retrieves a list of archives from the registry xml file, and provides the
    archive list along with their timegate uris.
    Use self.timegate_uri = "new timegate uri" to override the default
    timegate preference.

    :param archive_registry: (str) A valid base uri for the registry xml file.
    :return: (dict) A map of the archive id and their corresponding full name,
                timegate of the archive.
    """

    archive_list = {}
    response = requests.get(archive_registry_uri)
    # parse xml
    data = etree.parse(StringIO.StringIO(response.content))

    for link in data.xpath("./link"):
        arc_id = link.attrib["id"]
        name = link.attrib["longname"]
        timegate_uri = link.find("timegate").attrib["uri"]
        memento_status = link.find("archive").attrib["memento-status"]
        mem_status = False
        if memento_status == "yes":
            mem_status = True

        archive_list[arc_id] = {"name": name,
                                "timegate_uri": timegate_uri,
                                "memento_status": mem_status}

    return archive_list
