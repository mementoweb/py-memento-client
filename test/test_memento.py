# -*- coding: utf-8 -*-
from memento_client import MementoClient
from memento_client.memento_client import MementoClientException
from memento_test.server import application as memento_test_app
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
import unittest
import logging
from datetime import datetime
from copy import deepcopy

#logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)

test_server = Client(memento_test_app, BaseResponse)


class MementoTest(unittest.TestCase):

    def test_get_original_uri(self):
        r = test_server.get("/tg/http://www.bbc.com")

        mc = MementoClient()
        assert mc.get_original_uri(None, response=r) == "http://www.bbc.com"

        env, r1 = test_server.get("/tg/http://www.bbc.com",
                                  headers=[("Prefer", "no_original_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        assert mc.get_original_uri(req_url, response=r1) == req_url

        r2 = test_server.get("/tg/http://www.bbc.com", headers=[("Prefer", "invalid_link_header")])
        with self.assertRaises(ValueError):
            mc.get_original_uri(req_url, response=r2)

        # from a memento
        env, r1 = test_server.get("/2015/http://www.bbc.com",
                                  headers=[("Prefer", "all_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        assert mc.get_original_uri(req_url, response=r1) == "http://www.bbc.com"

    def test_get_native_timegate_uri(self):

        # testing uri_r with native uri_g
        env, r = test_server.get("/", headers=[("Prefer", "native_tg_url")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.get_native_timegate_uri(req_url, None, response=r) is not None

        # testing uri_r with no native uri_g
        env, r = test_server.get("/", headers=[("Prefer", "no_native_tg_url")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.get_native_timegate_uri(req_url, None, response=r) is None

        # testing uri_r with redirects
        # redirection cannot be tested as the get_native_timegate_uri cannot
        # connect to the redirect uri.
        # TODO: refactor get_native_timegate_uri code for testing the redirects
        env, r = test_server.get("/", headers=[("Prefer", "redirect")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        mc.get_native_timegate_uri(req_url, None, response=r)
        # tests if the redirect counter has been incremented
        assert mc.native_redirect_count > 0

        # testing native url from TG response.. should return None
        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "all_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.get_native_timegate_uri(req_url, None, response=r) is None

        # testing native url from Memento... should also return None
        env, r = test_server.get("/2015/http://www.bbc.com",
                                 headers=[("Prefer", "all_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.get_native_timegate_uri(req_url, None, response=r) is None

    def test_is_timegate(self):

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "all_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "no_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "required_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "no_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "no_original_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "invalid_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        with self.assertRaises(ValueError):
            mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "no_accept_dt_error")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        with self.assertRaises(MementoClientException):
            mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "tg_no_redirect")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        # the method is only looking for rel=original, hence a bad dt shd not affect outcome
        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "invalid_dt_in_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "tg_200")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "tg_200_no_memento_dt_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "tg_302_no_location_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "tg_302_memento_dt_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/2015/http://www.bbc.com",
                                 headers=[("Prefer", "all_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/2015/http://www.bbc.com",
                                 headers=[("Prefer", "no_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

        env, r = test_server.get("/2015/http://www.bbc.com",
                                 headers=[("Prefer", "no_memento_dt_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_timegate(req_url, None, response=r)

    def test_is_memento(self):

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "all_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "no_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "no_link_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "no_vary_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "tg_200")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.is_memento(req_url, response=r)

        env, r = test_server.get("/tg/http://www.bbc.com",
                                 headers=[("Prefer", "tg_302_memento_dt_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "all_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "no_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "required_headers")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "no_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "no_original_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "no_memento_dt_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "invalid_memento_dt_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "invalid_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        with self.assertRaises(ValueError):
            mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "invalid_datetime_in_link_header")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert not mc.is_memento(req_url, response=r)

        env, r = test_server.get("/2016/http://www.bbc.com",
                                 headers=[("Prefer", "valid_archived_redirect")], as_tuple=True)
        req_url = env.get("werkzeug.request").url
        mc = MementoClient()
        assert mc.is_memento(req_url, response=r)

    def test_convert_to_datetime(self):

        assert isinstance(MementoClient.convert_to_datetime("Sun, 01 Apr 2010 12:00:00 GMT"), datetime)
        with self.assertRaises(ValueError):
            isinstance(MementoClient.convert_to_datetime("Sun, 01 Apr 2010 12:00:00 G"), datetime)
        with self.assertRaises(TypeError):
            isinstance(MementoClient.convert_to_datetime(datetime.now()), datetime)

        assert MementoClient.convert_to_datetime("") is None
        assert MementoClient.convert_to_datetime(None) is None

    def test_convert_to_http_datetime(self):

        now = MementoClient.convert_to_http_datetime(datetime.now())
        assert isinstance(now, str)
        assert isinstance(MementoClient.convert_to_datetime(now), datetime)

        with self.assertRaises(AttributeError):
            # passing string
            MementoClient.convert_to_http_datetime(now)

        assert MementoClient.convert_to_http_datetime("") is None
        assert MementoClient.convert_to_http_datetime(None) is None

    def test_parse_link_header(self):

        link_header = '<http://mementoweb.org/about/>;rel="original",' + \
            '<http://mementoarchive.lanl.gov/twa/memento/20160920175206/http://mementoweb.org/about/>' + \
            ';rel="memento last"; datetime="Tue, 20 Sep 2016 17:52:06 GMT",' + \
            '<http://mementoarchive.lanl.gov/ta/20091212013921/http://mementoweb.org/about/>' + \
            ';rel="memento first"; datetime="Sat, 12 Dec 2009 01:39:21 GMT",' + \
            '<http://mementoarchive.lanl.gov/tg/timemap/http://mementoweb.org/about/>' + \
            ';rel="timemap index"; type="application/link-format"'

        assert isinstance(MementoClient.parse_link_header(link_header), dict)
        with self.assertRaises(ValueError):
            MementoClient.parse_link_header(link_header[:-5])

        assert MementoClient.parse_link_header("") is None

    def validate_memento_info(self, m_info):
        if m_info.get("first"):
            assert isinstance(m_info.get("first").get("datetime"), datetime)
            assert len(m_info.get("first").get("uri")) > 0
        if m_info.get("last"):
            assert isinstance(m_info.get("first").get("datetime"), datetime)
            assert len(m_info.get("first").get("uri")) > 0
        if m_info.get("prev"):
            assert isinstance(m_info.get("first").get("datetime"), datetime)
            assert len(m_info.get("first").get("uri")) > 0
        if m_info.get("next"):
            assert isinstance(m_info.get("first").get("datetime"), datetime)
            assert len(m_info.get("first").get("uri")) > 0
        assert isinstance(m_info.get("closest").get("datetime"), datetime)
        assert len(m_info.get("closest").get("uri")) > 0

    def test_prepare_memento_response(self):
        mc = MementoClient()
        assert mc._MementoClient__prepare_memento_response() is None

        env, r = test_server.get("/2016/http://www.bbc.com", as_tuple=True)
        uri_m = env.get("werkzeug.request").url
        assert mc._MementoClient__prepare_memento_response(uri_m=uri_m).get("mementos").get("closest").get("uri")[0] \
               == uri_m

        dt_m = r.headers.get("Memento-Datetime")
        assert isinstance(mc._MementoClient__prepare_memento_response(uri_m=uri_m, dt_m=dt_m)\
                   .get("mementos").get("closest").get("datetime"), datetime)

        assert mc._MementoClient__prepare_memento_response(uri_m=uri_m, dt_m=dt_m, status_code=200) \
                          .get("mementos").get("closest").get("http_status_code") == 200

        link = r.headers.get("Link")
        m_info = mc._MementoClient__prepare_memento_response(uri_m=uri_m, dt_m=dt_m, link_header=link).get("mementos")
        self.validate_memento_info(m_info)

    def create_mock_responses(self, org_url, tg_url, org_prefer, tg_prefer, mem_location):
        if org_prefer:
            env, org_res = test_server.get(org_url,
                                           headers=[("Prefer", org_prefer)], as_tuple=True)
        else:
            env, org_res = test_server.get(org_url, as_tuple=True)
        req_url = env.get("werkzeug.request").url

        if tg_prefer:
            env, tg_res = test_server.get(tg_url,
                                          headers=[("Prefer", tg_prefer)], as_tuple=True)
        else:
            env, tg_res = test_server.get(tg_url, as_tuple=True)
        tg_res.request = env.get("werkzeug.request")
        if mem_location == "memento":
            tg_res.url = tg_res.request.url
        else:
            tg_res.url = tg_res.headers.get(mem_location)
        tg_res.history = []
        tg_res.history.append(tg_res)
        return req_url, org_res, tg_res

    def test_get_memento_info(self):

        # ----------------------------------------------------------------------------------- #
        # from original with native tg
        req_url, org_res, tg_res = self.create_mock_responses("/", "/tg/http://www.bbc.com",
                                                              "native_tg_url", "", "Location")
        mc = MementoClient()
        m_info = mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                     org_response=org_res, tg_response=tg_res).get("mementos")
        self.validate_memento_info(m_info)

        # ----------------------------------------------------------------------------------- #
        # from original with no native tg
        req_url, org_res, tg_res = self.create_mock_responses("/", "/tg/http://www.bbc.com",
                                                              "no_native_tg_url", "", "Location")
        mc = MementoClient(timegate_uri=tg_res.request.url)
        m_info = mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                     org_response=org_res, tg_response=tg_res).get("mementos")
        self.validate_memento_info(m_info)

        # ----------------------------------------------------------------------------------- #
        # from tg with 302
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "tg_302", "tg_302", "Location")
        mc = MementoClient()
        m_info = mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                     org_response=org_res, tg_response=tg_res).get("mementos")
        self.validate_memento_info(m_info)

        # ----------------------------------------------------------------------------------- #
        # from tg with 200
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "tg_200", "tg_200", "Content-Location")
        mc = MementoClient()
        m_info = mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                     org_response=org_res, tg_response=tg_res).get("mementos")
        self.validate_memento_info(m_info)

        # ----------------------------------------------------------------------------------- #
        # from tg with no headers
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "no_headers", "no_headers", "Location")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from tg with no vary header
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "no_vary_header", "no_vary_header", "Location")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from tg with no link header
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "no_link_header", "no_link_header", "Location")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from tg with only minimum required headers
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "required_headers", "required_headers", "Location")
        mc = MementoClient()
        m_info = mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                     org_response=org_res, tg_response=tg_res).get("mementos")
        assert len(m_info.get("closest").get("uri")) > 0

        # ----------------------------------------------------------------------------------- #
        # from tg with invalid vary header
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "", "invalid_vary_header", "Location")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from tg with no location header
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "", "tg_302_no_location_header", "Location")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from tg with memento dt header
        req_url, org_res, tg_res = self.create_mock_responses("/tg/http://www.bbc.com", "/tg/http://www.bbc.com",
                                                              "", "tg_302_memento_dt_header", "Location")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from memento with all headers
        req_url, org_res, tg_res = self.create_mock_responses("/2016/http://www.bbc.com", "/2016/http://www.bbc.com",
                                                              "", "all_headers", "memento")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from memento with no headers
        req_url, org_res, tg_res = self.create_mock_responses("/2016/http://www.bbc.com", "/2016/http://www.bbc.com",
                                                              "no_headers", "no_headers", "memento")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from memento with no memento datetime header
        req_url, org_res, tg_res = self.create_mock_responses("/2016/http://www.bbc.com", "/2016/http://www.bbc.com",
                                                              "", "no_memento_dt_header", "memento")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from memento with no original link header
        req_url, org_res, tg_res = self.create_mock_responses("/2016/http://www.bbc.com", "/2016/http://www.bbc.com",
                                                              "", "no_original_link_header", "memento")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from memento with valid internal redirect
        req_url, org_res, tg_res = self.create_mock_responses("/2016/http://www.bbc.com", "/2016/http://www.bbc.com",
                                                              "", "valid_internal_redirect", "memento")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

        # ----------------------------------------------------------------------------------- #
        # from memento with valid archived redirect
        req_url, org_res, tg_res = self.create_mock_responses("/2016/http://www.bbc.com", "/2016/http://www.bbc.com",
                                                              "", "valid_archived_redirect", "memento")
        mc = MementoClient()
        assert mc.get_memento_info(req_url, None, req_uri_response=org_res,
                                   org_response=org_res, tg_response=tg_res).get("mementos") is None

