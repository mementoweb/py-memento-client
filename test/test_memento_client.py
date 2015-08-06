import pytest
from memento_client import MementoClient

def test_get_memento_uri_default():

    mc = MementoClient()

    input_uri_r = "http://www.cs.odu.edu"

    input_datetime = "Mon, 24 Apr 2010 19:00:00 GMT"

    actual_uri_m = mc.get_memento_uri(input_uri_r, input_datetime)

    expected_uri_m = "http://web.archive.org/web/20100502170247/http://www.cs.odu.edu/"

    assert expected_uri_m == actual_uri_m


def test_get_memento_uri_specified_timegate():

    mc = MementoClient(timegate_uri="http://www.webarchive.org/wayback/archive/")

    input_uri_r = "http://www.lanl.gov"

    input_datetime = "Wed, 19 Mar 2003 23:59:59"

    expected_uri_m = "http://www.webarchive.org.uk:80/wayback/archive/20080409230230/http://www.lanl.gov/"

    actual_uri_m = mc.get_memento_uri(input_uri_r, input_datetime)

    assert expected_uri_m == actual_uri_m

def test_get_native_timegate_uri():

    mc = MementoClient()

    input_uri_r = "http://metaarchive.org/metawiki/index.php/MetaWiki_Home"

    input_datetime = "Thu, 11 Dec 2013 14:00:04"

    expected_uri_g = "http://timetravel.mementoweb.org/mediawiki/timegate/http://metaarchive.org/metawiki/index.php/MetaWiki_Home"

    actual_uri_g = mc.get_native_timegate_uri(input_uri_r, input_datetime)

    assert expected_uri_g == actual_uri_g
