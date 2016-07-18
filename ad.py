#!/usr/bin/env python
# encoding: utf-8

import json
import time
import random
import requests
from handler import random_with_N_digits
from same_spider.secret import header


def get_latest_ugc_author_uids():
    try:
        res = requests.get('http://localhost:9200/_sql?sql=select * from same/music order by timestamp desc limit 30')
        if res.status_code == 200:
            return [i['_source']['author_uid'] for i in json.loads(res.text)['hits']['hits']]
    except Exception, e:
        print 'err when get uids', e
        return []


def send_ad(msg):
    fetch_url = 'https://im-xs.same.com/imuser/sendPmsg'
    fuid = '6017298'
    for to_uid in get_latest_ugc_author_uids():
        print to_uid
        body = {
            "cmd": "smsg",
            "op": 1,
            "body": {
                "sender_name": "匿名",
                "seq": random_with_N_digits(8),
                "tuid": to_uid,
                "msg": msg,
                "fuid": fuid,
                "type": 1
            }
        }
        try:
            res = requests.post(fetch_url, headers=header, data=json.dumps(body), verify=False)
            if res.status_code == 200:
                print res.text
            else:
                print 'got incorrect status code'
        except Exception, e:
            print 'failed send ad:', msg, e
        time.sleep(random.randint(10,42))

if __name__ == "__main__":
    #msg = 'same星人,快来HOT-SAMER俱乐部看精彩集合,浏览Samer红人榜,网址:\nhttp://hot-samer.club'
    msg = 'samer俱乐部，所有samer大尺度自拍都在这里了\n http://hot-samer.club'
    send_ad(msg)

