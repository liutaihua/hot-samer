#!/usr/bin/env python
# encoding: utf-8

import sys
import gevent
import requests
requests.packages.urllib3.disable_warnings()
import json
from gevent import monkey
monkey.patch_all()

def get_channels_ids_with_cate_id(cate_id, offset=None):
    if offset:
        url = 'https://v2.same.com/channels/cate/%s?offset=%s' % (cate_id, offset)
    else:
        url = 'https://v2.same.com/channels/cate/%s' % cate_id
    try:
        print url
        res = requests.get(url, verify=False)
        data = json.loads(res.text)
        result = data['data']['results']
        return [i['id'] for i in result]
    except Exception, e:
        print '-------------err:', e
        return []

def get_photo_url_with_channel_id(channel_id, next_uri=None):
    if next_uri:
        url = 'https://v2.same.com' + next_uri
    else:
        url = 'https://v2.same.com/channel/%s/senses' % channel_id
    try:
        res = requests.get(url, verify=False)
        data = json.loads(res.text)
        result = data['data']['results']
        if not result:
            print 'empty channel content', url
            return [], None
        return result, data['data']['next']
    except Exception, e:
        print 'get_photo_url_with_channel_id err', e, url
        return [], None


def make_request(channel_id):
    msg_list = []
    page_last_time = None
    for page in range(1, 10):
        if not page_last_time:
            offset = None
        else:
            offset = str(page_last_time) + '3327330000'
        s_msg_list, page_last_time = get_photo_url_with_channel_id(channel_id, offset=offset)
        if page_last_time == 0:
            break
        msg_list.extend(s_msg_list)
    for url, txt in msg_list:
        print url, txt

if __name__ == "__main__":
    if sys.argv[1] == 'get_channel':
        channel_ids = []
        gs = []
        for page in range(1, 11):
            channel_ids.extend(get_channels_ids_with_cate_id(page))
        print channel_ids
        for i in channel_ids:
            gs.append(gevent.spawn(make_request, i))
        gevent.joinall(gs)
