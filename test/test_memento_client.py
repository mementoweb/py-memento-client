import pytest
import csv
import datetime
from memento_client import MementoClient

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

@pytest.mark.parametrize("input_uri_r,input_datetime,expected_uri_m", memento_uri_default_testdata)
def test_get_memento_uri_default(input_uri_r, input_datetime, expected_uri_m):

    mc = MementoClient()

    actual_uri_m = mc.get_memento_info(input_uri_r, input_datetime).get("closest").get("uri")

    assert expected_uri_m == actual_uri_m

@pytest.mark.parametrize("input_uri_r,input_datetime,input_timegate,expected_uri_m", specified_timegate_testdata)
def test_get_memento_uri_specified_timegate(input_uri_r, input_datetime, input_timegate, expected_uri_m):

    mc = MementoClient(timegate_uri=input_timegate, check_native_timegate=False)

    actual_uri_m = mc.get_memento_info(input_uri_r, input_datetime).get("closest").get("uri")

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

    mc = MementoClient()

    status = mc.determine_if_memento(input_uri_m)

    assert True == status
