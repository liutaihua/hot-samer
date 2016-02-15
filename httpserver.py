#!/usr/bin/env python
# encoding: utf-8

import os
import json
import sys
import requests
import urllib2
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

class HotSamerHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        offset = int(self.get_argument('offset', 0)) * 100
        sql = 'select photo, author_uid, author_name channel_id, views, likes ' \
              'from same/user_ugc where (channel_id=1033563 or channel_id=1228982 or channel_id=1228982) ' \
              'order by timestamp desc limit 100 offset %s' % offset
        # resp = requests.get('http://localhost:9200/_sql?sql=%s' % sql)
        # if resp.status_code != 200:
        #     return self.finish('')
        # resp = json.loads(resp.text)
        arg = urllib2.quote(sql)
        fetch_url = 'http://localhost:9200/_sql?sql=%s' % arg

        # yield self.fetch_and_redirect(fetch_url)
        resp = yield self.fetch_url(fetch_url)
        resp = json.loads(resp.body)
        self.set_header('Access-Control-Allow-Origin', '*')
        photo_list = []
        for i in resp['hits']['hits']:
            photo_info = i['_source']
            if not photo_info.get('photo'):
                continue
            photo_list.append(photo_info)
        self.write(json.dumps(photo_list))
        # self.write(json.dumps(resp['hits']['hits']))
        self.finish()
        raise gen.Return()

from same_spider.secret import header

class SamerProfileHandler(BaseHandler):
    @gen.coroutine
    def get(self, uid):
        fetch_url = 'https://v2.same.com/user/%s/profile' % uid
        resp = yield self.fetch_url(fetch_url, headers=header)
        data = {'code': 500}
        if resp:
            if resp.code == 200:
                data = json.loads(resp.body)
        if data['code'] != 0:
            # self.write(json.dumps({}))
            profile = {}
        else:
            # self.write(json.dumps(resp))
            profile = data['data']['user']
        # print profile, resp.code
        # self.finish()
        if 'join_at' in profile:
            profile['join_at'] = datetime.datetime.fromtimestamp(int(profile['join_at'])).strftime('%Y-%m-%d %H:%M:%S')
        self.render('user.html', profile=profile)
        raise gen.Return()


handlers = [
    (r"/", MainHandler),
    (r"/hot-samer", HotSamerHandler),
    (r"/samer/(\d+)", SamerProfileHandler),
    (r'/favicon.ico', tornado.web.StaticFileHandler,dict(url='/static/favicon.ico',permanent=False)),
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
