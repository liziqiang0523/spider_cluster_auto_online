#coding=utf-8
#author: shiyuming
"""
    问答相关查询服务
    使用tornade来作web-server
"""

import urlparse
import json, time
from datetime import datetime
import tornado.ioloop
import tornado.web
from tornado import httpserver
from ssdb import StrictSSDB
import traceback

import logging

ssdb_qarel = StrictSSDB(host = '115.182.70.149', port = 8888)
class HandlerFirstKnn(tornado.web.RequestHandler):
    
    #get 请求处理
    def get(self):
        response = {}
        qid = self.get_argument('id', '')
        qarel = ssdb_qarel.get(qid)
        if qarel is None:
            response['wenda_recommend'] = []
            response['code'] = 400
        else:
            response = json.loads(qarel)
            response['code'] = 200
        json_response = json.dumps(response, ensure_ascii=False)
        self.write(json_response)

    #post 请求处理
    def post(self):
        response = {}
        data = json.loads(self.request.body)
        qid = data['id']
        qarel = ssdb_qarel.get(qid)
        if qarel is None:
            response['wenda_recommend'] = []
            response['code'] = 400
        else:
            response = json.loads(qarel)
            response['code'] = 200
        json_response = json.dumps(response, ensure_ascii=False)
        self.write(json_response)

if __name__ == '__main__':
    ip = '0.0.0.0'
    app = tornado.web.Application([
            (r"/.*", HandlerFirstKnn),
            ])
    print 'Starting server for knn_first, use <Ctrl-C> to stop'
    server = httpserver.HTTPServer(app)
    server.bind(9999, address=ip)
    server.start(0)
    tornado.ioloop.IOLoop.instance().start()
        
