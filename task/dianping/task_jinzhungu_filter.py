#!/usr/bin/python
#coding=utf-8
#author:liziqiang
'''
  从mongo中导出一些目标数据向mongo发送消息。
'''

import logging,traceback,math,confs, sys, json, datetime, urlparse, re, math, time, urlparse

from pykafka import KafkaClient, Topic
from urllib import quote, unquote
from pymongo import MongoClient
from pymongo.collection import Collection
from ssdb import StrictSSDB

reload(sys)
sys.setdefaultencoding('utf8')

class ProgressRate:
  cnt = 0
  rate = 10000
  @staticmethod
  def progress():
    ProgressRate.cnt += 1
    if ProgressRate.cnt % ProgressRate.rate == 0:
      print 'now process at [%d] on [%s]' % (ProgressRate.cnt, datetime.datetime.now())

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
    self.linkbase = StrictSSDB(host = confs.SSDB_LINKBASE_HOST, port = confs.SSDB_LINKBASE_PORT)
  
  def task_from_file(self,file_in='data/pcauto_list.txt',spider_name='liziqiang_k_article_pcauto_17'):
    fin = open(file_in,'r')
    mongo_task_col = Collection(self.mongo_task_12, spider_name)
    item_col = Collection(self.mongo_oreo_12,'che300_price')
    i = 0
    for item in self.mongo_oreo_12.jingzhengu_item.find({'crawl_time':{'$lte':'20170330'}}):
    #for line in fin:
      #url = line.strip()
      url = item['from_url']
      if url == "":
        continue
      #old_item = self.mongo_oreo_12.jingzhengu_item.find_one({'from_url':url})
      #if old_item is not None:
        #print 'already ok'
        #continue
      print url
      linkinfo = {'url':url, 'from_url':url, 'spider_name':spider_name, 'item_type':'item_list', 'status':0, 'schedule_cnt':0, 'failed_cnt':0, 'in_time': math.floor(time.time()), 'update_time':math.floor(time.time())}
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
  processor.task_from_file(sys.argv[1],sys.argv[2])
  print 'ok'



