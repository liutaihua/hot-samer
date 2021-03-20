#!/usr/bin/env python
# encoding: utf-8

import random
import json
import copy
import pwd
import os
import datetime
from tornado import gen
import tornado.web
import pylibmc as memcache
from lib.base_httphandler import BaseHandler

USER = pwd.getpwuid(os.getuid())[0]
if USER == 'liutaihua':
    # for my private secret
    from same_spider.secret_liutaihua import header
else:
    from same_spider.secret import header

mc = memcache.Client(['127.0.0.1:11211'])

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        #return self.finish({'res': "衙门严打,临时停服"})
        return self.render('index-test.html')

class NotFoundPage(BaseHandler):
    def get(self):
        return self.finish("美女全跑光了(此频道20点后开放), 没找到任何东西...")


class SortSensesHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        return self.render('likes_sort.html')


class LetterIndex(tornado.web.RequestHandler):
    def get(self, uid):
        self.set_header('Access-Control-Allow-Origin', '*')
        return self.render('letter.html', tuid=uid)

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

class LetterResultIndex(BaseHandler):
    def get(self, tuid, success_or_failed):
        return self.render('success_or_failed.html', tuid=tuid, success_or_failed=success_or_failed)

class TestIndex(BaseHandler):
    def get(self):
        return self.render('index-test.html')



class HotSamerHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        sort_by_likes = self.get_argument('by_likes', None)
        offset = int(self.get_argument('offset', 0)) * 100
        limit = int(self.get_argument('limit', 100))
        hot_level = self.get_argument('hot_level', '0')

        sql = "select id, photo, author_uid, author_name channel_id, views, likes " \
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
            sort_condition = 'and timestamp> "%s" order by likes desc,views desc,timestamp desc ' \
                             'limit %d offset %s' % (time_condition.isoformat(), limit, offset)
        else:
            sort_condition = 'order by timestamp desc limit %d' % limit
        if offset:
            sort_condition += ' offset %s' % offset
        sql += sort_condition
        photo_list = yield self.query_from_es(sql)
        self.set_header('Access-Control-Allow-Origin', '*')
        for photo_info in copy.deepcopy(photo_list):
            if not photo_info.get('photo'):
                photo_list.remove(photo_info)
        # if sort_by_likes:
        #     # 热频道
        #     tumblr_resp = self.query_from_es('select * from tumblr/pic order by timestamp desc limit 10')
        self.write(json.dumps(photo_list))
        self.flush()
        self.finish()
        raise gen.Return()


class SamerProfileHandler(BaseHandler):
    @gen.coroutine
    def get(self, uid):
        profile = yield self.get_profile(uid)
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
                if 'likes' not in i:
                    i['likes'] = 0
                latest_news.append(i)
        self.render('user.html', profile=profile, latest_news=latest_news)
        raise gen.Return()


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return random.randint(range_start, range_end)


class LetterHandler(BaseHandler):
    @gen.coroutine
    def get(self, uid):
        profile = yield self.get_profile(uid)
        self.render('letter.html', tuid=uid, profile=profile)
        raise gen.Return()

    @gen.coroutine
    def post(self, to_uid):
        # fuid = self.get_argument('uid')
        # name = self.get_argument('name')
        msg = self.get_argument('msg')
        fetch_url = 'https://im-xs.same.com/imuser/sendPmsg'
        seq = random_with_N_digits(8)
        fuid = '6017298'
        msg = u'有Samer在 hot-samer.club 给您发匿名私信:\n' + msg
        body = {
            "cmd": "smsg",
            "op": 1,
            "body": {
                "sender_name": "匿名",
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
            if resp.code != 200:
                self.redirect('/letter/%s/failed'%to_uid)
                # self.write('发生失败, 可能由于网络或Same服务器问题, 请手动返回')
                # self.flush()
            elif json.loads(resp.body)['code'] == 0:
                print(resp.body)
                self.redirect('/letter/%s/success'%to_uid)
                # self.write(json.dumps(resp.body))
                # self.write('发生成功, 请手工返回')
                # self.flush()
            else:
                self.redirect('/letter/%s/failed'%to_uid)
                # self.write('发生失败, 可能由于网络或Same服务器问题, 请手动返回')
                # self.flush()
                # self.set_status(301)
                # self.set_header("Location", 'http://localhost:8080/samer/%s'%to_uid)
                # yield gen.Task(IOLoop.instance().add_timeout, time.time() + 5)            # self.finish()
        # self.redirect('/samer/%s' % to_uid)
        else:
            self.write('发生失败, 可能由于网络或Same服务器问题, 请手动返回')
            self.flush()
        raise gen.Return()


class SamerStarHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        early_time = datetime.datetime.now() - datetime.timedelta(days=7)
        query_ugc_sql = 'SELECT * FROM same/user_ugc WHERE timestamp>"%s" AND ' \
                        'likes>5 ORDER BY timestamp DESC,likes DESC,views DESC LIMIT 1000 OFFSET 0' %\
                        (early_time.isoformat())
        print(query_ugc_sql)
        ugc_list = yield self.query_from_es(query_ugc_sql)
        rank_data = {}
        for ugc in ugc_list:
            rank_data.setdefault(str(ugc['author_uid']), 0)
            rank_data[str(ugc['author_uid'])] += int(ugc['likes'])
        uids = rank_data.keys()
        profile_list = {}
        for sub_uids in [uids[i:i + 200] for i in range(0, len(uids), 200)]:
            sub_profile_list = yield self.get_multi_profile_from_es(sub_uids, skip_silence_user=True)
            profile_list.update(sub_profile_list)
        for uid, profile in profile_list.items():
            profile['likes_count'] = rank_data[str(uid)]
        profile_list = sorted(profile_list.items(), key=lambda x:x[1]['likes_count'], reverse=True)
        self.render('user_list.html', profile_list=profile_list, from_search_page=False)
        raise gen.Return()


class SearchHandler(BaseHandler):
    def get(self):
        self.render("search.html")

    @gen.coroutine
    def post(self):
        keyword = self.get_argument('name')
        client_format = self.get_argument('format', None)
        profile_list = []
        if not keyword:
            self.render('user_list.html', profile_list=profile_list, from_search_page=True)
            raise gen.Return()
        keyword = keyword.encode('utf8')
        # 先查profile表
        profile_list_dict = yield self.get_profile_with_name(keyword)
        sql = 'SELECT author_uid FROM same/user_ugc where author_name="%s"' % keyword
        # ugc表也查一次
        data = yield self.query_from_es(sql)
        uids = [i['author_uid'] for i in data]
        if len(uids) > 100:
            uids = uids[:100]
        if uids:
            profile_dict_from_ugc = yield self.get_multi_profile_from_es(uids)
            profile_list_dict.update(profile_dict_from_ugc)
        if not profile_list_dict:
            # 还是没有, 就搜索发帖内容中的匹配
            sql = 'SELECT * FROM same/user_ugc where txt="%s"' % keyword
            data = yield self.query_from_es(sql)

            uids = [i['author_uid'] for i in data]
            if len(uids) > 100:
                uids = uids[:100]
            if uids:
                profile_dict_from_ugc = yield self.get_multi_profile_from_es(uids)
                profile_list_dict.update(profile_dict_from_ugc)

        profile_list = sorted(profile_list_dict.items(), key=lambda x:x[1]['_score'], reverse=True)
        if client_format == 'json':
            self.finish(json.dumps(profile_list))
        else:
            self.render('user_list.html', profile_list=profile_list, from_search_page=True)
        raise gen.Return()

class PopularMusicHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        filter_date = datetime.datetime.now() - datetime.timedelta(days=7)
        sql = 'SELECT * FROM same/music where timestamp>"%s" AND likes>3 ' \
              'order by likes desc,views desc,timestamp desc LIMIT 200' %(filter_date.isoformat())
        music_list = yield self.query_from_es(sql)
        print(music_list)
        self.render('music_list.html', music_list=music_list)
        raise gen.Return()

class LikesHandler(BaseHandler):
    @gen.coroutine
    def post(self, photo_id):
        is_succeed = yield self.update_likes(photo_id)
        self.finish(json.dumps({'code': 0, 'res': is_succeed}))
        raise gen.Return()

class TumblrHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        pic_list = []
        tumblr_resp = yield self.query_from_es('SELECT * FROM tumblr/pic ORDER BY timestamp DESC LIMIT 200')
        if tumblr_resp:
            for idx, pic in enumerate(tumblr_resp):
                pic_list.append({
                    'views': 0,
                    'photo': pic['photo'],
                    'author_name': pic.get('author_name') or 'N/A',
                    'author_uid': 0,
                    'likes': 99,
                    'id': idx
                })
        self.finish(json.dumps(pic_list))
        raise gen.Return()

class PopularChannelsHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        filter_date = datetime.datetime.now() - datetime.timedelta(days=1)
        sql = 'SELECT channel_id, COUNT(*) as ugc_count FROM same/user_ugc ' \
                                            'WHERE timestamp>"%s" GROUP BY channel_id ORDER BY ugc_count DESC LIMIT 30' % filter_date.isoformat()
        channels_data = yield self.query_from_es(sql, need_aggregations=True, aggregations_key='channel_id')
        channels_list = []
        for info in channels_data:
            channel_info = yield self.get_channel_info(info['key'])
            channel_info['created_at'] = datetime.datetime.fromtimestamp(int(channel_info['created_at']))
            channel_info['updated_at'] = datetime.datetime.fromtimestamp(int(channel_info['updated_at']))
            channel_info['ugc_count'] = info['ugc_count']['value']
            channels_list.append((info['key'], channel_info))
        self.render('channels.html', channels_list=channels_list)
        raise gen.Return()

class ChannelSensesHandler(BaseHandler):
    @gen.coroutine
    def get(self, cid):
        sql = 'SELECT * FROM same/user_ugc WHERE channel_id=%s ORDER BY timestamp DESC limit 2000' % cid
        results_list = yield self.query_from_es(sql)
        channel_name = yield self.query_from_es('SELECT name FROM same/channels WHERE id=%s' % cid)
        # self.finish(json.dumps(results_list))
        for i in results_list:
            i['created_at'] = datetime.datetime.fromtimestamp(int(i['created_at']))
        self.render('channel_senses.html', ugc_list=results_list, channel_name=channel_name[0]['name'])
        raise gen.Return()


class BlogHandler(tornado.web.RequestHandler):
    def get(self, action):
        self.set_header('Access-Control-Allow-Origin', '*')
        if action == 'like_count':
            user = self.get_argument('user')
            article_name = '-'.join(self.get_argument('name', '').split(' '))
            count = mc.get('%s_liked_count'%article_name) or 0
            liked = mc.get('%s_like_%s'%(user, article_name)) is not None or False
            return self.finish({'liked': liked, 'count': count, 'user': user})

    def post(self, action):
        self.set_header('Access-Control-Allow-Origin', '*')
        if action == 'like':
            user = self.get_argument('user')
            article_name = '-'.join(self.get_argument('name', '').split(' '))
            key = '%s_liked_count'%article_name
            if mc.get(key) is None:
                mc.set(key, 0)
            like_count = mc.incr(key)
            return self.finish({'liked': True, 'count': like_count, 'user': user})
        elif action == 'unlike':
            user = self.get_argument('user')
            article_name = '-'.join(self.get_argument('name', '').split(' '))
            key = '%s_liked_count'%article_name
            if mc.get(key) is None:
                mc.set(key, 1)
            like_count = mc.decr(key)
            return self.finish({'liked': False, 'count': like_count, 'user': user})
