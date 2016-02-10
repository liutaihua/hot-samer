#!/usr/bin/env python
# encoding: utf-8

import sys
import json
import gevent
import time
import requests
requests.packages.urllib3.disable_warnings()

from gevent import monkey
monkey.patch_all()

header = {
    'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9',
    'timezone':	'Asia/Shanghai',
    'Advertising-UUID': '3FA4E87E-0BC6-456B-9418-A3BF6B60A306',
    'User-Agent': 'same-appstore2/400 (iPhone; iOS 9.2.1; Scale/2.00)',
    'Proxy-Connection': 'keep-alive',
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    'Machine': 'ios|301|iPhone OS 9.2.1|iPhone|640|1096',
    'X-same-Device-UUID': 'FF9B6ABE-8872-4F30-ABAC-F2D5A5F98F5D',
    'encode_type': 'json',
    'Connection': 'keep-alive',
    #'Authorization': 'Token 1453861675-3c1c8c4bf2f99639-4306380',
    'X-Same-Request-ID': 'D7B623C1-103D-4F6D-B9D0-8ADC98E1D961',
    'Accept-Encoding': 'gzip, deflate'
}


cookies = {'PHPSESSID': 'hlmq75sibuksac6h71c1avdab1'}
def send(product_id):
    data = {'address_id': 53036, 'product_id': product_id}
    header['Authorization'] = 'Token ' + sys.argv[1]
    while True:
        try:
            res = requests.post('https://payment.ohsame.com/order_create', headers=header, cookies=cookies, verify=False, data=data)
            d = json.loads(res.text)
            if int(d.get('code', 1)) == 0:
                print '------------------ success ------------------', product_id, res.text
                return
            else:
                print product_id, d['detail']
        except Exception, e:
            print '============err', e
        gevent.sleep(0.05)

def get_categories():
    #res = requests.get('https://resource.ohsame.com/categories/categories-list-cate.html?no-control&cate=2', headers=header, cookies=cookies, verify=False)
    print sys.argv[2]
    header['Authorization'] = 'Token 1453861675-3c1c8c4bf2f99639-4306380'
    header['Content-Type'] = 'application/json'
    res = requests.get(sys.argv[2], headers=header, verify=False)
    print res.text

def yangmao():
    header['Authorization'] = 'Token 1453861675-3c1c8c4bf2f99639-4306380'
    header['Content-Type'] = 'application/json'
    res = requests.post(sys.argv[2], headers=header, verify=False)
    print res.text

def get_user_profile(uid):
    url = 'https://v2.same.com/user/%s/profile' % uid
    header['Authorization'] = 'Token 1453861675-3c1c8c4bf2f99639-4306380'
    try:
        print url
        res = requests.get(url, verify=False, headers=header)
        data = json.loads(res.text)
        if int(data.get('code', 1)) == 0:
            return data['data']
        else:
            return {}
    except ValueError as e:
        print 'res ValueError',e, url, res.text
    except Exception, e:
        print '-------------err:', e, url

def get_user_recent_ugc_list(uid):
    results = []
    now = time.time()
    last_results, next_uri = get_user_senses_and_next_url(uid)
    results.extend(last_results)
    while len(last_results) > 0:
        if (now - int(float(last_results[-1]['created_at']))) > 86400 * 30 * 6:
            break
        last_results, next_uri = get_user_senses_and_next_url(uid, next_uri)
        gevent.sleep(0.1)
        results.extend(last_results)
    return results


def get_user_senses_and_next_url(uid, next_uri=None):
    if next_uri:
        url = 'https://v2.same.com' + next_uri
    else:
        url = 'https://v2.same.com/user/%s/senses' % uid
    header['Authorization'] = 'Token 1453861675-3c1c8c4bf2f99639-4306380'
    try:
        print url
        res = requests.get(url, verify=False, headers=header)
        data = json.loads(res.text)
        if int(data.get('code', 1)) == 0:
            return data['data'].get('results', []), data['data'].get('next')
        else:
            return [], None
    except ValueError as e:
        print 'res ValueError',e, url, res.text
    except Exception, e:
        print '-------------err:', e, url
    return [], None

def get_activity_senses(cid):
    header['Authorization'] = 'Token 1453861675-3c1c8c4bf2f99639-4306380'
    url = 'http://v2.same.com/activity/senses/channel/1021984?order=hostest&from=-7%20day'
    requests.get(url, verify=False)

if __name__ == "__main__":
    if sys.argv[1] == 'category':
        get_categories()

    elif sys.argv[1] == 'yangmao':
        yangmao()
    elif sys.argv[1] == 'get_profile':
        print get_user_profile(int(sys.argv[2]))
    elif sys.argv[1] == 'get_senses':
        print len(get_user_senses(int(sys.argv[2])))
    else:
        gs = []
        for product_id in [747, 748,749,750]:
            for i in range(10):
                gs.append(gevent.spawn(send, product_id))
        gevent.joinall(gs)
