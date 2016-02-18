#coding=utf8
import tornado.web
import tornado.httpserver
import tornado.httpclient

import os
import re
import json
import urllib2
import datetime


from urlparse import urljoin
from tornado.options import options
from tornado.httpclient import HTTPError
from tornado import gen
from tornado.log import app_log



from lib.httputil \
    import (set_response_info, wrap_response_body, fetch_and_trace_response, get_request_time)

import session
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from same_spider.secret import header



absolute_http_url_re = re.compile(r"^https?://", re.I)
es = Elasticsearch()


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        print self.application.db
        return self.application.db

    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.path = ''
        # self.session = session.TornadoSession(self.application.session_manager, self)

    @gen.coroutine
    def fetch_and_redirect(self, fetch_url, **kwargs):
        """处了fetch_url,其他的必须使用kwargs传递"""
        try:
            response = yield fetch_and_trace_response(fetch_url, **kwargs)
        except HTTPError as e:
            yield self.handle_fetch_exception(e, fetch_url)
            raise gen.Return()

        yield self.response_redirect(
            response.code, body=response.body,
            content_type=response.headers.get("Content-Type", None))
        raise gen.Return()


    @gen.coroutine
    def query_from_es(self, sql):
        sql = urllib2.quote(sql)
        fetch_url = 'http://localhost:9200/_sql?sql=%s' % sql
        response = yield self.fetch_url(fetch_url)
        raise gen.Return(response)

    @gen.coroutine
    def get_hottest_samer_list_from_es(self):
        early_time = datetime.datetime.now() - datetime.timedelta(days=7)
        query_ugc_sql = 'SELECT * FROM same/user_ugc WHERE timestamp>"%s" AND ' \
                        'likes>3 ORDER BY timestamp DESC LIMIT 2000 OFFSET 0' %\
                        (early_time.isoformat())
        print query_ugc_sql
        resp = yield self.query_from_es(query_ugc_sql)
        gen.Return(resp)

    @gen.coroutine
    def save_hottest_samer_list(self, data):
        pass

    @gen.coroutine
    def get_multi_profile_from_es(self, uids, skip_silence_user=False):
        sql = 'SELECT * FROM same/user_profile WHERE id in (%s)' % ','.join(map(str, uids))
        if skip_silence_user:
            sql += ' AND senses > 20'
        resp = yield self.query_from_es(sql)
        profile_list = []
        for i in json.loads(resp.body)['hits']['hits']:
            profile = i['_source']
            profile['_score'] = i['_score']
            profile_list.append(profile)
        # profile_list = [i['_source'] for i in json.loads(resp.body)['hits']['hits']]
        data = {}
        for profile in profile_list:
            profile['join_at'] = datetime.datetime.fromtimestamp(int(profile['join_at'])).strftime('%Y-%m-%d %H:%M:%S')
            data[profile['id']] = profile
        raise gen.Return(data)

    @gen.coroutine
    def get_profile(self, uid):
        profile = yield self.get_profile_from_es(uid)
        if not profile:
            profile = yield self.get_profile_from_same(uid)
        raise gen.Return(profile)

    @gen.coroutine
    def get_profile_from_es(self, uid):
        sql = 'SELECT * FROM same/user_profile WHERE id=%s' % uid
        resp = yield self.query_from_es(sql)
        profile = json.loads(resp.body)['hits']['hits']
        profile = profile[0]['_source'] if profile else {}
        if profile:
            profile['join_at'] = datetime.datetime.fromtimestamp(int(profile['join_at'])).strftime('%Y-%m-%d %H:%M:%S')
        raise gen.Return(profile)

    @gen.coroutine
    def get_profile_from_same(self, uid):
        fetch_url = 'https://v2.same.com/user/%s/profile' % uid
        resp = yield self.fetch_url(fetch_url, skip_except_handle=True, headers=header)
        data = {'code': 500}
        profile = {}
        if resp:
            if resp.code == 200:
                data = json.loads(resp.body)
        if data['code'] == 0:
            profile = data['data']['user']
            yield self.save_single_profile(profile)
            profile['join_at'] = datetime.datetime.fromtimestamp(int(profile['join_at'])).strftime('%Y-%m-%d %H:%M:%S')
        raise gen.Return(profile)


    @gen.coroutine
    def save_single_profile(self, profile):
        yield self.save_to_es(index='same', table='user_profile', uuid=profile['id'], data=profile)
        raise gen.Return()

    @gen.coroutine
    def save_to_es(self, index, table, uuid, data):
        es_data = {
            "_index": index,
            "_type": table,
            "id": uuid,
            '_source': data
        }
        res = helpers.bulk(es, [es_data])  # 这里的库不支持异步,忍了
        print 'save to es result:', res
        raise gen.Return()

    @gen.coroutine
    def fetch_url(self, fetch_url, skip_except_handle=False, **kwargs):
        try:
            response = yield fetch_and_trace_response(fetch_url, **kwargs)
        except HTTPError as e:
            if not skip_except_handle:
                yield self.handle_fetch_exception(e, fetch_url)
            raise gen.Return()
        raise gen.Return(response)

    @gen.coroutine
    def handle_fetch_exception(self, exception, fetch_url=""):
        """处理fetch一个url的时候返回的错误，这个里面可能会response"""
        if (not hasattr(exception, "code")) \
                or (not hasattr(exception, "response")):
            app_log.error(
                u"调用handle_fetch_exception出错，这个对象没有code于response属性")
            yield self.response_msg(400, 4001, u"服务器内部错误, exception没有code或者response属性")
            raise gen.Return()

        request_time = get_request_time(exception)
        err_msg = u"调用%s出错,外部服务器错误,http状态码: %s,错误消息: %s, request_time: [%sms]" \
                  % (fetch_url, exception.code, exception.message, request_time*1000)

        if exception.code == 599:
            # 这里不能使用599，599不在标准里面
            app_log.error(err_msg)
            yield self.response_msg(400, 1001, u"[外部服务器连接失败]-%s" % err_msg)
            raise gen.Return()
        elif exception.code == 600:
            app_log.error(u"[可能是socket错误]-%s" % err_msg)
            yield self.response_msg(400, 1001, u"[外部服务器连接失败]-%s" % err_msg)
            raise gen.Return()
        elif exception.code == 404:
            app_log.error(err_msg)
            yield self.response_msg(404, 1001, err_msg)
            raise gen.Return()
        elif exception.code == 405:
            app_log.error(err_msg)
            yield self.response_msg(405, 1001, err_msg)
            raise gen.Return()
        elif exception.code >= 500:
            app_log.error(err_msg)
            yield self.response_msg(400, 1001, err_msg)
            raise gen.Return()

        response = exception.response
        try:
            response = set_response_info(response)
        except AttributeError:
            # 如果服务器返回500可以运行到这里，此时response为None
            yield self.response_msg(400, 1004, u"外部服务器错误: %s" % fetch_url)
            raise gen.Return()

        # 因为是调用外部服务器，如果外部服务器返回错误，改写返回的code为1003
        # 原服务器的code保存在 _code的key里面
        yield self.response_redirect(response.code, 1003, response.body)
        raise gen.Return()


    @gen.coroutine
    def response_redirect(self, status_code=200, data_code=None, body=None,
                          content_type=None):
        """这个函数一般用于转发其他服务器的返回值
        返回body的内容
        status_code: 响应的状态码
        body: 响应的内容， 字典或者字符串
        content_type: 返回的类型
        data_code: 如果这个值存在，改写body里面的code值，同时保留一个副本在_code里面
        """
        if content_type:
            self.set_header("Content-Type", content_type)

        if not body:  # 这里直接返回
            yield self._response(status_code)
            raise gen.Return()

        if data_code:
            # 转换和验证body的格式
            if isinstance(body, (unicode, str)):
                try:
                    body = json.loads(body)
                except ValueError:
                    pass
            elif isinstance(body, dict):
                pass
            else:
                app_log.error(u"body 格式错误： %s" % repr(body))
                yield self.response_msg(400, 4001, u"服务器错误")
                raise gen.Return()

            # 有code值才会改写
            if isinstance(body, dict):
                if ("code" in body) and (body["code"] != 0):
                    body["_code"] = body["code"]
                    body["code"] = data_code

        yield self._response(status_code, body)


    @gen.coroutine
    def response_msg(self, status_code=200, data_code=0, content=None):
        """
        返回一个{"code": data_code, "msg": content}，对session做了处理，
        本来打算改写finish的，但是系统内部的finish是同步的，你懂的
        status_code: 响应的状态码
        content: 响应的内容
        data_code: {"code": data_code}
        """
        if not content:  # 这里直接返回
            yield self._response(status_code)
            raise gen.Return()

        if not isinstance(content, (unicode, str)):
            app_log.error(
                "In response_msg: content: %s is not a valid string!"
                % repr(content))
            self.set_status(400)
            content = wrap_response_body(
                4001, msg=u"内部服务器错误，返回错误的msg类型")
        else:
            content = wrap_response_body(data_code, msg=content)

        yield self._response(status_code, content)


    @gen.coroutine
    def _response(self, status_code=200, content=None):
        yield self._update_session()
        self.set_status(status_code)
        if content:
            self.write(content)
        self.finish()
        raise gen.Return()


    @gen.coroutine
    def _update_session(self):
        pass
        # 如果是匿名的session就不保存了
        # if "username" in self.session:
        #     self.set_cookie("username", self.session["username"])
        #     yield self.session.save()

        # self.set_secure_cookie("session_id", self.session.get("session_id"))
        # self.set_cookie("socket_id", self.session.get("session_id"))


    # platform apis, support sina, renren, douban
    def get_current_user(self):
        return None
        # return self.session.get('username')

    def get_user_id(self):
        return self.session.get('me').id

    def get_user_image(self):
        return self.session.get('me').profile_image_url

    def get_user_url(self):
        return self.session.get('me').url

    def get_host(self):
        """Returns the HTTP host using the environment or request headers."""
        return self.request.headers.get('Host')

    def build_absolute_uri(self, location=None):
        """
        Builds an absolute URI from the location and the variables available in
        this request. If no location is specified, the absolute URI is built on
        ``request.get_full_path()``.
        """
        if not location:
            location = ''
        if not absolute_http_url_re.match(location):
            current_uri = '%s://%s%s' % (self.is_secure() and 'https' or 'http',
                                         self.get_host(), self.path)
            location = urljoin(current_uri, location)
        return iri_to_uri(location)

    def is_secure(self):
        return os.environ.get("HTTPS") == "on"

    def get_error_html(self, status_code, exception=None, **kwargs):
        return self.render_string('_error.htm', status_code=status_code, exception=exception)


class ReqMixin(object):
    user_callback = {}

    def wait_for_request(self, callback):
        cls = ReqMixin
        cls.user_callback.update({self.get_user_id():callback})

    def new_req(self, req):
        cls = ReqMixin
        callback = cls.user_callback[self.get_user_id()]
        callback(req)

class ProxyHandler(BaseHandler, ReqMixin):
    @tornado.web.asynchronous
    def get(self, action):
        if action == 'update':
            self.wait_for_request(self.async_callback(self.send))

        elif action == 'request':
            http = tornado.httpclient.AsyncHTTPClient()
            http.fetch(self.get_argument('url'), callback=self.new_req)
            self.finish()


    def send(self, response):
        # Closed client connection
        if response.error:
            raise tornado.web.HTTPError(500)
        self.write(response.body)
        self.flush()

import os
import urllib

class Promise(object):
        pass



#from encoding import smart_str, iri_to_uri, force_unicode
def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    if isinstance(s, Promise):
        return unicode(s).encode(encoding, errors)
    elif not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                                           errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s

def iri_to_uri(iri):
    """
    Convert an Internationalized Resource Identifier (IRI) portion to a URI
    portion that is suitable for inclusion in a URL.

    This is the algorithm from section 3.1 of RFC 3987.  However, since we are
    assuming input is either UTF-8 or unicode already, we can simplify things a
    little from the full method.

    Returns an ASCII string containing the encoded result.
    """
    # The list of safe characters here is constructed from the "reserved" and
    # "unreserved" characters specified in sections 2.2 and 2.3 of RFC 3986:
    #     reserved    = gen-delims / sub-delims
    #     gen-delims  = ":" / "/" / "?" / "#" / "[" / "]" / "@"
    #     sub-delims  = "!" / "$" / "&" / "'" / "(" / ")"
    #                   / "*" / "+" / "," / ";" / "="
    #     unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
    # Of the unreserved characters, urllib.quote already considers all but
    # the ~ safe.
    # The % character is also added to the list of safe characters here, as the
    # end of section 3.1 of RFC 3987 specifically mentions that % must not be
    # converted.
    if iri is None:
        return iri
    return urllib.quote(smart_str(iri), safe="/#%[]=:;$&()+,!?*@'~")
