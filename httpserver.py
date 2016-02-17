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
              "from same/user_ugc"

        channel_ids = {
            '0': [1033563,1228982,1228982], # 默认腿, 性感, 贫乳3个频道
            '1': [1312542], # 拍画频道
            '2': [1002974, 1001617, 1187908],  # iphone摄影和instagrammer 频道
            '3': [967, 1021852, 1276224, 1099203], # 普通自拍
        }[hot_level]
        query_condition = ' WHERE channel_id in (%s)' % ','.join(map(str, channel_ids))
        sql += query_condition

        if sort_by_likes:
            time_condition = datetime.datetime.now() - datetime.timedelta(days=3)
            sort_condition = 'and timestamp> "%s" order by likes desc limit %d offset %s' % (
            time_condition.isoformat(), limit, offset)
        else:
            sort_condition = 'order by timestamp desc limit %d offset %s' % (limit, offset)
        sql += sort_condition
        resp = yield self.query_from_es(sql)
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
        profile = yield self.get_profile_from_es(uid)
        if not profile:
            profile = yield self.get_profile_from_same(uid)
        fetch_url = 'https://v2.same.com/user/%s/senses' % uid
        resp2 = yield self.fetch_url(fetch_url, skip_except_handle=True, headers=header)
        news_data = {'code': 500}
        latest_news = []
        if resp2:
            if resp2.code == 200:
                news_data = json.loads(resp2.body)
        if news_data['code'] == 0:
            for i in news_data['data']['results']:
                i['created_at'] = datetime.datetime.fromtimestamp(int(i['created_at'])).strftime('%Y-%m-%d %H:%M:%S')
                latest_news.append(i)
        self.render('user.html', profile=profile, latest_news=latest_news)
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


class HotestSamerRankHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        early_time = datetime.datetime.now() - datetime.timedelta(days=7)
        query_ugc_sql = 'SELECT * FROM same/user_ugc WHERE timestamp>"%s" LIMIT 2000 OFFSET 0' %\
                        (early_time.isoformat())
        print query_ugc_sql
        resp = yield self.query_from_es(query_ugc_sql)
        rank_data = {}
        if resp:
            for ugc in json.loads(resp.body)['hits']['hits']:
                ugc = ugc['_source']
                rank_data.setdefault(str(ugc['author_uid']), 0)
                rank_data[str(ugc['author_uid'])] += int(ugc['likes'])
        uids = rank_data.keys()
        profile_list = {}
        if len(uids) > 200:
            for sub_uids in [uids[i:i+200] for i in range(0, len(uids), 200)]:
                sub_profile_list = yield self.get_multi_profile_from_es(sub_uids)
                profile_list.update(sub_profile_list)
        for uid, profile in profile_list.items():
            profile['likes_count'] = rank_data[str(uid)]
        profile_list = sorted(profile_list.items(), key=lambda x:x[1]['likes_count'], reverse=True)
        self.render('hottest_rank.html', profile_list=profile_list)
        raise gen.Return()


handlers = [
    (r"/", MainHandler),
    (r"/senses", SortSensesHandler),
    (r"/hot-samer", HotSamerHandler),
    (r"/samer/(\d+)", SamerProfileHandler),
    (r"/fun", FunIndex),
    (r"/photography", PhotographyIndex),
    (r"/others", OthersIndex),
    (r"/hottest-rank", HotestSamerRankHandler),
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
