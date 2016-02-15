#!/usr/bin/env python
# encoding: utf-8

import os
import json
import sys
import requests

import tornado
import tornado.web
import tornado.wsgi
import tornado.options
import tornado.httpserver
import tornado.autoreload
import tornado.ioloop
from lib import session
from lib.base_httphandler import BaseHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        offset = int(self.get_argument('offset', 0)) * 100
        sql = 'select photo from same/user_ugc where channel_id=1033563 limit 100 offset %s' % offset
        resp = requests.get('http://localhost:9200/_sql?sql=%s' % sql)
        if resp.status_code != 200:
            return self.finish('')
        resp = json.loads(resp.text)
        self.set_header('Access-Control-Allow-Origin', '*')
        photo_list = []
        for i in resp['hits']['hits']:
            photo_list.append(i['_source']['photo'])
        return self.finish(json.dumps(photo_list))


handlers = [
    (r"/", MainHandler),
    (r"/hot-samer", MainHandler),
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
