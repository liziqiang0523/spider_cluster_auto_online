#!/usr/bin/python
#coding=utf-8
#author:liziqiang
'''
  从mongo中导出一些目标数据向mongo发送消息。
'''

import logging,traceback,math,confs, sys, json, datetime, urlparse, re, math, time, urlparse
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
    self.oreo_zebra_online = mongo_client_12.get_database('oreo_zebra_online')
    self.linkbase = StrictSSDB(host = confs.SSDB_LINKBASE_HOST, port = confs.SSDB_LINKBASE_PORT)
  
  def is_data_online(self,url=''):
    where = {'url':url}
    item = self.oreo_zebra_online.article_txt.find_one(where)
    if item is None:
      return False
    else:
      print 'already ok'
      return True
    

  def task_from_spider_name(self,spider_name='liziqiang_k_article_pcauto_17',allow_domains=''):
    #time_stamp = time.time() - 288880
    time_stamp = time.time() - 150000
    print 'time_stamp',time_stamp
    re_allow_domain = ''
    if len(allow_domains) > 0:
      re_allow_domain = allow_domains.replace(",",'|')
    where = {'spider_name':spider_name,'in_time':{'$gte':time_stamp},'url':{'$regex':re_allow_domain}}
    print where
    mongo_task_col = Collection(self.mongo_task_12, spider_name)
    i = 0
    cursor = self.mongo_oreo_12.linkbase.find(where)
    for item in cursor:
      url = item['url']
      if 'ightspeed' in url or 'gateway' in url or 'redirect.php' in url or self.is_data_online(url):
        continue
      linkinfo = {'url':url, 'from_url':url, 'spider_name':spider_name, 'item_type':'item_list', 'status':0, 'schedule_cnt':0, 'failed_cnt':0, 'in_time': item['in_time'], 'update_time':item['update_time'] if 'update_time' in item else math.floor(time.time())}
      print url
      mongo_task_col.insert(linkinfo)
      del linkinfo['_id']
      linkinfo_str = json.dumps(linkinfo, ensure_ascii = False, encoding = 'utf-8')
      self.linkbase.set(url, linkinfo_str)
      i += 1
    print ('%s send kafka massage number %d by spider name %s' % (datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S %A %B"),i,spider_name))
    print 'happy work'


if __name__ == "__main__":
  print 'sending...'
  processor = Send_kafka_from_mongo()
  processor.task_from_spider_name(sys.argv[1],sys.argv[2])
  print 'ok'



