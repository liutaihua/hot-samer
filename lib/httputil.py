# -*- coding: utf-8 -*-

import json

from tornado.httpclient import HTTPError
from tornado.httpclient import HTTPRequest as OutRequest
from tornado.log import app_log
from tornado import gen

# from management.model.trace import Trace
# from lib.patch import AsyncHTTPClient
from tornado.httpclient import HTTPResponse, HTTPError, AsyncHTTPClient



def wrap_response_body(code=0, **kwargs):
    """
    基本上就是一个包裹函数
    wrap_response_body(code=4, msg="help", user="lily") =>
    {
        "code": 4,
        "msg": "help",
        "user": "lily",
    }
    """
    if not code:
        code = 0
    body = {"code": code}
    body.update(kwargs)
    return body


def set_response_info(response, code=400, body=u"外部服务器错误",
                      content_type="application/json"):
    """
    如果response没有相关的初始值，这里会尝试设置
    尝试设置response的code和body，如果存在不设置
    可能会抛出AttributeError，比如response为None的时候
    """
    if not hasattr(response, "code"):
        setattr(response, "code", code)
    if not hasattr(response, "body"):
        setattr(response, "body", body)

    # 尝试获取content_type，默认使用json
    try:
        content_type = response.headers["Content-Type"]
    except AttributeError:  # 没有headers属性
        content_type = content_type
        setattr(response, "header", {"Content-Type": content_type})
    except ValueError:  # 没有相关的type
        response.headers["Content-Type"] = content_type

    return response


@gen.coroutine
def fetch_and_trace_response(
        request_url, body=None, method="GET", description=None,
        username=None, connect_timeout=2, request_timeout=8):
    """
    获取一个response，如果请求成功返回response，同时记录日志，如果请求失败，
    抛出错误：
    request_url: 请求的url
    body: 请求的参数
    method: 请求的方法
    description: 描述请求做的事情，如果没有，默认不记录
    """
    client = AsyncHTTPClient()
    if method:
        method = method.upper()
    if isinstance(body, dict):
        body = json.dumps(body)
    request = OutRequest(
        request_url, body=body, method=method, request_timeout=request_timeout,
        connect_timeout=connect_timeout)
    try:
        response = yield client.fetch(request)
    except HTTPError as e:
        # 如果请求返回的不是200，同样需要记录请求的日志
        # if description:
        #     try:
        #         yield Trace.trace_url(
        #             description, request, e.response, username)
        #     except Exception as e:
        #         app_log.error(u"插入操作日志出错： %s" % e.message)

        request_time = get_request_time(e)
        app_log.info(
            u"[request] time [%sms], method [%s], url [%s], code [%s], msg [%s]"
            % (request_time*1000, method, request_url, e.code, e.message))

        # 这里不该打日志，所有不是200的状态码都在这里返回，外层捕获的时候使用
        raise HTTPError(e.code, e.message, e.response)
    except Exception as e:
        request_time = get_request_time(e)
        error_message = e.message + " [request time: {0}ms]".format(request_time * 1000)
        app_log.error(u"may be caused by network connection, error message [%s]" % error_message)
        raise HTTPError(600, u"未知错误，可能是网络连接问题: %s" % error_message)

    # 返回值200也需要记录到数据库
    # if description:
    #     try:
    #         yield Trace.trace_url(description, request, response, username)
    #     except Exception as e:
    #         app_log.error(u"插入操作日志出错： %s" % e.message)

    app_log.info(
        u"[request] time [%sms], method [%s], url [%s], code [%s]"
        % (response.request_time*1000, method, request_url, response.code))
    raise gen.Return(response)


def get_request_time(exception):
    """ 通过exception获取可能存在的request time """
    request_time = -1
    if hasattr(exception, "response"):
        request_time = exception.response.request_time if exception.response else -1
    return request_time