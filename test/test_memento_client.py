import pytest
import csv
import datetime
from memento_client import MementoClient

def load_testdata(filename, keylist):

    testdata = []

    with open(filename, 'rb') as csvfile:

        datareader = csv.DictReader(csvfile, delimiter=',', quotechar='"',
            quoting=csv.QUOTE_ALL, skipinitialspace=True)

        for row in datareader:
            accept_datetime = datetime.datetime.strptime(row['Accept-Datetime'], "%a, %d %b %Y %H:%M:%S GMT")
            datarow = []

            datarow.append(row[keylist[0]])
            datarow.append(accept_datetime)

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

@pytest.mark.parametrize("input_uri_r,input_datetime,expected_uri_m", memento_uri_default_testdata)
def test_get_memento_uri_default(input_uri_r, input_datetime, expected_uri_m):

    mc = MementoClient()

    actual_uri_m = mc.get_memento_uri(input_uri_r, input_datetime)

    assert expected_uri_m == actual_uri_m

@pytest.mark.parametrize("input_uri_r,input_datetime,input_timegate,expected_uri_m", specified_timegate_testdata)
def test_get_memento_uri_specified_timegate(input_uri_r, input_datetime, input_timegate, expected_uri_m):

    mc = MementoClient(timegate_uri=input_timegate)

    actual_uri_m = mc.get_memento_uri(input_uri_r, input_datetime)

    assert expected_uri_m == actual_uri_m

@pytest.mark.parametrize("input_uri_r,input_datetime,expected_uri_g", native_timegate_testdata)
def test_get_native_timegate_uri(input_uri_r, input_datetime, expected_uri_g):

    mc = MementoClient()

    actual_uri_g = mc.get_native_timegate_uri(input_uri_r, input_datetime)

    assert expected_uri_g == actual_uri_g
