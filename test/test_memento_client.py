import pytest
import csv
import datetime
import sys
import requests
from memento_client import MementoClient
import memento_client


def load_testdata(filename, keylist):

    testdata = []

    with open(filename, 'rt') as csvfile:

        datareader = csv.DictReader(csvfile, delimiter=',', quotechar='"',
            quoting=csv.QUOTE_ALL, skipinitialspace=True)

        for row in datareader:

            datarow = []
            # oddly, sometimes the final " is left in the data
            datarow.append(row[keylist[0]].rstrip('"'))

            if 'Accept-Datetime' in row:
                acc_dt = row['Accept-Datetime'].strip() # workaround for extra space added sometimes?
                accept_datetime = datetime.datetime.strptime(acc_dt, "%a, %d %b %Y %H:%M:%S GMT")
                datarow.append(accept_datetime)

            if len(keylist) > 2:
                for item in keylist[2:]:
                    datarow.append(row[item])

            testdata.append( datarow )

    return testdata


memento_uri_default_testdata = load_testdata(
    "test/memento_uri_default_testdata.csv",
    [ "Input URI-R", "Accept-Datetime", "Expected URI-M" ] )

specified_timegate_testdata = load_testdata(
    "test/specified_timegate_testdata.csv",
    [ "Input URI-R", "Accept-Datetime", "Input URI-G", "Expected URI-M" ] )

native_timegate_testdata = load_testdata(
    "test/native_timegate_testdata.csv",
    [ "Input URI-R", "Accept-Datetime", "Expected URI-G" ] )

mementos_only_testdata = load_testdata(
    "test/mementos_only_testdata.csv",
    [ "Input URI-M" ]
    )

non_compliant_mementos_testdata = load_testdata(
    "test/non_compliant_mementos_testdata.csv",
    [ "Input URI-M" ]
    )

mementos_not_found_testdata = load_testdata(
    "test/mementos_not_in_archive_testdata.csv",
    [ "Input URI-R", "Accept-Datetime", "Input URI-G" ] )

nonexistent_urirs = load_testdata(
    "test/nonexistent_urirs_testdata.csv",
    [ "Input URI-R" ]
    )


@pytest.mark.parametrize("input_uri_r,input_datetime,expected_uri_m", memento_uri_default_testdata)
def test_get_memento_uri_default(input_uri_r, input_datetime, expected_uri_m):

    mc = MementoClient()

    actual_uri_m = mc.get_memento_info(input_uri_r, input_datetime).get("mementos").get("closest").get("uri")[0]

    assert expected_uri_m == actual_uri_m

@pytest.mark.parametrize("input_uri_r,input_datetime,input_timegate,expected_uri_m", specified_timegate_testdata)
def test_get_memento_uri_specified_timegate(input_uri_r, input_datetime, input_timegate, expected_uri_m):

    mc = MementoClient(timegate_uri=input_timegate, check_native_timegate=False)

    actual_uri_m = mc.get_memento_info(input_uri_r, input_datetime).get("mementos").get("closest").get("uri")[0]

    assert expected_uri_m == actual_uri_m

@pytest.mark.parametrize("input_uri_r,input_datetime,expected_uri_g", native_timegate_testdata)
def test_get_native_timegate_uri(input_uri_r, input_datetime, expected_uri_g):

    mc = MementoClient(check_native_timegate=True)

    actual_uri_g = mc.get_native_timegate_uri(input_uri_r, input_datetime)

    assert expected_uri_g == actual_uri_g

@pytest.mark.parametrize("input_uri_m", mementos_only_testdata)
def test_determine_if_memento(input_uri_m):

    # TODO: pytest did not seem to split this into arguments
    input_uri_m = input_uri_m[0]

    status = MementoClient.is_memento(input_uri_m)

    assert True == status

@pytest.mark.parametrize("input_uri_m", non_compliant_mementos_testdata)
def test_get_memento_data_non_compliant(input_uri_m):

    # TODO: pytest did not seem to split this into arguments
    input_uri_m = input_uri_m[0]

    mc = MementoClient()
    
    accept_datetime = datetime.datetime.strptime("Thu, 01 Jan 1970 00:00:00 GMT", "%a, %d %b %Y %H:%M:%S GMT")

    original_uri = mc.get_memento_info(input_uri_m, accept_datetime).get("original_uri")

    assert input_uri_m == original_uri

@pytest.mark.parametrize("input_uri_r,input_datetime,input_uri_g", mementos_not_found_testdata)
def test_mementos_not_in_archive_uri(input_uri_r, input_datetime, input_uri_g):

    mc = MementoClient(timegate_uri=input_uri_g)

    accept_datetime = datetime.datetime.strptime("Thu, 01 Jan 1970 00:00:00 GMT", "%a, %d %b %Y %H:%M:%S GMT")

    original_uri = mc.get_memento_info(input_uri_r, accept_datetime).get("original_uri")

    assert input_uri_r == original_uri

@pytest.mark.skipif('darwin' in sys.platform, reason="requests on Linux behaves differently than OSX")
def test_bad_timegate_linux():

    input_uri_r = "http://www.cnn.com"
    bad_uri_g = "http://www.example.com"
    accept_datetime = datetime.datetime.strptime("Thu, 01 Jan 1970 00:00:00 GMT", "%a, %d %b %Y %H:%M:%S GMT")

    mc = MementoClient(timegate_uri=bad_uri_g)

    with pytest.raises(requests.ConnectionError):
        original_uri = mc.get_memento_info(input_uri_r, accept_datetime).get("original_uri")


@pytest.mark.skipif('linux' in sys.platform, reason="requests on OSX behaves differently than Linux")
def test_bad_timegate_osx():

    input_uri_r = "http://www.cnn.com"
    bad_uri_g = "http://www.example.com"
    accept_datetime = datetime.datetime.strptime("Thu, 01 Jan 1970 00:00:00 GMT", "%a, %d %b %Y %H:%M:%S GMT")

    mc = MementoClient(timegate_uri=bad_uri_g)

    original_uri = mc.get_memento_info(input_uri_r, accept_datetime).get("original_uri")

    assert input_uri_r == original_uri

@pytest.mark.parametrize("input_uri_r", nonexistent_urirs)
def test_nonexistent_urirs(input_uri_r):

    input_uri_r = input_uri_r[0]

    accept_datetime = datetime.datetime.strptime("Thu, 01 Jan 1970 00:00:00 GMT", "%a, %d %b %Y %H:%M:%S GMT")

    mc = MementoClient()

    memento_info = mc.get_memento_info(input_uri_r, accept_datetime)

    assert memento_info.get("original_uri") == input_uri_r

    assert memento_info.get("timegate_uri") == 'http://timetravel.mementoweb.org/timegate/{}'.format(input_uri_r)


def good_url_slash_at_end():

    input_uri_r = "http://www.cnn.com/"
    
    mc = MementoClient()
    dt = datetime.datetime.strptime("Tue, 11 Sep 2001 08:45:45 GMT", "%a, %d %b %Y %H:%M:%S GMT")
    
    uri_m = mc.get_memento_info(input_uri_r, dt).get("mementos").get("closest").get("uri")[0]

    assert uri_m == 'http://webarchive.loc.gov/all/20010911181528/http://www2.cnn.com/'
