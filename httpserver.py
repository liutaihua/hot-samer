#!/usr/bin/env python
# encoding: utf-8

import os
import json
import sys
import requests
import urllib2
import random
import datetime

import tornado
import tornado.web
import tornado.wsgi
import tornado.options
import tornado.httpserver
import tornado.autoreload
import tornado.ioloop
from lib import session
from tornado import gen
from lib.base_httphandler import BaseHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        return self.render('index.html')


class SortSensesHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        return self.render('likes_sort.html')


class MsgIndex(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        return self.render('delivery_msg.html')

class FunIndex(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        return self.render('fun.html')


class PhotographyIndex(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        return self.render('photography.html')

class OthersIndex(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        return self.render('others.html')


class HotSamerHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        sort_by_likes = self.get_argument('by_likes', None)
        offset = int(self.get_argument('offset', 0)) * 100
        limit = int(self.get_argument('limit', 100))
        hot_level = self.get_argument('hot_level', '0')

        sql = "select photo, author_uid, author_name channel_id, views, likes " \
              "from same/user_ugc WHERE ("

        channel_ids = {
            '0': [1033563,1228982,1228982], # 默认腿, 性感, 贫乳3个频道
            '1': [1312542], # 拍画频道
            '2': [1002974, 1001617, 1187908],  # iphone摄影和instagrammer 频道
            '3': [967, 1021852, 1276224, 1099203], # 普通自拍
        }[hot_level]
        query_condition = ''
        for cid in channel_ids:
            query_condition += 'or channel_id=%s '%str(cid)
        query_condition = query_condition.lstrip('or')
        query_condition += ')'
        sql += query_condition

        if sort_by_likes:
            time_condition = datetime.datetime.now() - datetime.timedelta(days=3)
            sort_condition = 'and timestamp> "%s" order by likes desc limit %d offset %s' % (
            time_condition.isoformat(), limit, offset)
        else:
            sort_condition = 'order by timestamp desc limit %d offset %s' % (limit, offset)
        sql += sort_condition
        arg = urllib2.quote(sql)
        fetch_url = 'http://localhost:9200/_sql?sql=%s' % arg

        resp = yield self.fetch_url(fetch_url)
        if not resp:
            self.write(json.dumps([]))
            self.finish()
            raise gen.Return
        resp = json.loads(resp.body)
        self.set_header('Access-Control-Allow-Origin', '*')
        photo_list = []
        for i in resp['hits']['hits']:
            photo_info = i['_source']
            if not photo_info.get('photo'):
                continue
            photo_list.append(photo_info)
        self.write(json.dumps(photo_list))
        self.finish()
        raise gen.Return()


from same_spider.secret import header


class SamerProfileHandler(BaseHandler):
    @gen.coroutine
    def get(self, uid):
        fetch_url = 'https://v2.same.com/user/%s/profile' % uid
        resp = yield self.fetch_url(fetch_url, skip_except_handle=True, headers=header)
        data = {'code': 500}
        profile = {}
        if resp:
            if resp.code == 200:
                data = json.loads(resp.body)
        if data['code'] == 0:
            profile = data['data']['user']
        if 'join_at' in profile:
            profile['join_at'] = datetime.datetime.fromtimestamp(int(profile['join_at'])).strftime('%Y-%m-%d %H:%M:%S')
        self.render('user.html', profile=profile)
        raise gen.Return()


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return random.randint(range_start, range_end)


class DeliveryMessageHandler(BaseHandler):
    @gen.coroutine
    def post(self, to_uid):
        # fuid = self.get_argument('uid')
        name = self.get_argument('name')
        msg = self.get_argument('msg')
        fetch_url = 'https://im-xs.same.com/imuser/sendPmsg'
        seq = random_with_N_digits(8)
        fuid = '4306380'
        msg = u'有Samer在 http://hot-samer.club 给您托句话:' + msg
        body = {
            "cmd": "smsg",
            "op": 1,
            "body": {
                "sender_name": name or "未知",
                # "seq": "36303127",
                "seq": seq,
                "tuid": to_uid,
                "msg": msg,
                "fuid": fuid,
                "type": 1
            }
        }
        resp = yield self.fetch_url(fetch_url, skip_except_handle=True, method="POST", headers=header, body=body)
        # resp = requests.post(fetch_url, headers=header, json=body, verify=False)
        if resp:
            self.write(json.dumps(resp.body))
            self.finish()
        raise gen.Return()


handlers = [
    (r"/", MainHandler),
    (r"/senses", SortSensesHandler),
    (r"/hot-samer", HotSamerHandler),
    (r"/samer/(\d+)", SamerProfileHandler),
    (r"/fun", FunIndex),
    (r"/photography", PhotographyIndex),
    (r"/others", OthersIndex),
    # (r"/delivery", MsgIndex),
    # (r"/delivery/(\d+)", DeliveryMessageHandler),
    (r'/favicon.ico', tornado.web.StaticFileHandler, dict(url='/static/favicon.ico', permanent=False)),
]

settings = dict(
        cookie_secret="y+iqu2psQRyVqvC0UQDB+iDnfI5g3E5Yivpm62TDmUU=",
        debug=True,
        session_secret='terminus',
        session_dir='sessions',
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=False,
)


class Application(tornado.web.Application):
    def __init__(self):
        tornado.web.Application.__init__(self, handlers, **settings)
        # self.session_manager = session.TornadoSessionManager(settings["session_secret"], settings["session_dir"])
        # self.db = dbutils.Connection(
        #    host=options.DATABASE_HOST, database=options.DATABASE_NAME,
        #    user=options.DATABASE_USER, password=options.DATABASE_PASSWORD)


def main(port):
    tornado.options.parse_command_line()
    print "start on port %s..." % port
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(port)
    tornado.autoreload.start()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main(sys.argv[1])
