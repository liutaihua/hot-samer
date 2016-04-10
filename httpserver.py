#!/usr/bin/env python
# encoding: utf-8

import os
import json
import sys
import pwd
import time
import requests
import urllib2
import copy
import random
import datetime
import platform

import tornado
import tornado.web
import tornado.wsgi
import tornado.options
import tornado.httpserver
import tornado.autoreload
import tornado.ioloop
from lib import session
from tornado import gen
from tornado.ioloop import IOLoop

from handler import (MainHandler, SortSensesHandler, HotSamerHandler, SamerProfileHandler,
                     FunIndex, PhotographyIndex, OthersIndex, SamerStarHandler,
                     SearchHandler, PopularMusicHandler, LetterResultIndex, LetterHandler,
                     TestIndex, TumblrHandler, LikesHandler, NotFoundPage, PopularChannels)

handlers = [
    (r"/", MainHandler),
    (r"/senses", SortSensesHandler),
    (r"/hot-samer", HotSamerHandler),
    (r"/samer/(\d+)", SamerProfileHandler),
    (r"/fun", FunIndex),
    (r"/photography", PhotographyIndex),
    (r"/others", OthersIndex),
    (r"/samer-star", SamerStarHandler),
    (r"/search", SearchHandler),
    (r"/music", PopularMusicHandler),
    (r"/letter/(\d+)/(.*)", LetterResultIndex),
    (r"/letter/(\d+)", LetterHandler),
    (r"/lab", TestIndex),
    (r"/tumblr", TumblrHandler),
    (r"/photo/(\d+)/likes", LikesHandler),
    (r"/404", NotFoundPage),
    (r"/channels", PopularChannels),
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
    if platform.system() == 'Darwin':
        tornado.autoreload.start()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main(sys.argv[1])
