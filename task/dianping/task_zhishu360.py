#!/usr/bin/python
#coding=utf-8
#author:liziqiang
'''
从mongo获query， 组装成linkinfo 发送到消息队列。

'''

import logging,traceback,math,confs, sys, json, datetime, urlparse, re, math, time, urlparse
from urllib import quote, unquote
from pymongo import MongoClient
from pymongo.collection import Collection
from ssdb import StrictSSDB

reload(sys)
sys.setdefaultencoding('utf8')


class Send_kafka_from_mongo():
  def __init__(self):
    mongo_client = MongoClient(host = confs.MONGO_HOST, port = confs.MONGO_PORT)
    self.mongo_db = mongo_client.get_database(confs.MONGO_DB_NAME)
    self.mongo_oreo = mongo_client.get_database(confs.MONGO_DB_OREO)
    self.mongo_task = mongo_client.get_database('task')
    mongo_client_11 = MongoClient(host = '172.16.40.11', port = confs.MONGO_PORT)
    self.mongo_task_11 = mongo_client_11.get_database('task')
    self.mongo_oreo_11 = mongo_client_11.get_database(confs.MONGO_DB_OREO)

    mongo_client_12 = MongoClient(host = '172.16.40.12', port = confs.MONGO_PORT)
    self.mongo_task_12 = mongo_client_12.get_database('task')
    self.mongo_oreo_12 = mongo_client_12.get_database(confs.MONGO_DB_OREO)
    mongo_client_35 = MongoClient(host = '172.16.40.35', port = confs.MONGO_PORT)
    self.mongo_oreo_35 = mongo_client_35.get_database('oreo')
    self.linkbase = StrictSSDB(host = confs.SSDB_LINKBASE_HOST, port = confs.SSDB_LINKBASE_PORT)
  

  def task_zhishu360(self):
    spider_name = 'zhishu360'
    mongo_task_col = Collection(self.mongo_task_12, spider_name)
    url_partten = {
      1:'http://index.haosou.com/index/overviewJson?area=全国&q=query_partten',
      2:'http://index.haosou.com/index/soIndexJson?area=全国&q=query_partten',
      3:'http://index.haosou.com/index/soMediaJson?q=query_partten',
      4:'http://index.haosou.com/index/indexqueryhour?q=query_partten&t=30',
      5:'http://index.haosou.com/index/radarJson?t=30&q=query_partten',
      6:'http://index.haosou.com/index/indexquerygraph?t=30&area=全国&q=query_partten',
    }
    i = 0
    cursor = self.mongo_oreo_35.video_maoyan_mobile.find()
    for item in cursor:
      for key in url_partten.keys():
        query = item['name']
        url = url_partten[key].replace('query_partten',query)
        print url
        q_flag = key
        linkinfo = {'url':url, 'q_flag':q_flag , 'query':query,  'from_url':url, 'spider_name':spider_name, 'item_type':'item_url', 'status':0, 'schedule_cnt':0, 'failed_cnt':0, 'in_time': math.floor(time.time()), 'update_time':math.floor(time.time())}
        #print linkinfo 
        mongo_task_col.insert(linkinfo)
        del linkinfo['_id']
        linkinfo_str = json.dumps(linkinfo, ensure_ascii = False, encoding = 'utf-8')
        self.linkbase.set(url, linkinfo_str)
        i += 1
    print ('%s send kafka massage number %d by spider name %s' % (datetime.datetime.now().strftime("%Y-%m-%d  %H:%m:%S %A %B"),i,spider_name))
    print 'happy work'


if __name__ == "__main__":
  print 'sending...'
  processor = Send_kafka_from_mongo()
  processor.task_zhishu360()
  print 'ok'



