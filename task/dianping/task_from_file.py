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
    mongo_client = MongoClient(host = '127.0.0.1', port = confs.MONGO_PORT)
    self.mongo_oreo = mongo_client.get_database(confs.MONGO_DB_OREO)
    self.mongo_task = mongo_client.get_database('task')
    self.linkbase = StrictSSDB(host = '127.0.0.1', port = 8881)
  
  def task_from_file(self,file_in='dianping_id.txt',spider_name='liziqiang_dp_230'):
    citys = self.get_id_list('dp_city.txt')
    type1s = self.get_id_list('dp_type1.txt')
    type2s = self.get_id_list('dp_type2.txt')
    mongo_task_col = Collection(self.mongo_task, spider_name)
    i = 0
    for city in citys:
      for type1 in type1s:
        for type2 in type2s:
          url = 'http://www.dianping.com/search/category/%s/%s/%s' % (city,type1,type2)
          linkinfo = {'url':url, 'from_url':url, 'spider_name':spider_name, 'link_types':['list_url'], 'status':0, 'schedule_cnt':0, 'failed_cnt':0, 'in_time': math.floor(time.time()), 'update_time':math.floor(time.time())}
          mongo_task_col.insert(linkinfo)
          del linkinfo['_id']
          linkinfo_str = json.dumps(linkinfo, ensure_ascii = False, encoding = 'utf-8')
          self.linkbase.set(url, linkinfo_str)
          i += 1
    print ('%s send kafka massage number %d by spider name %s' % (datetime.datetime.now().strftime("%Y-%m-%d  %H:%m:%S %A %B"),i,spider_name))
    print 'happy work'
  
  def get_id_list(self,file_name):
    fin = open(file_name,'r')
    ids = []
    for line in fin:
      i = line.strip()
      ids.append(i)
    return ids

if __name__ == "__main__":
  print 'sending...'
  processor = Send_kafka_from_mongo()
  processor.task_from_file()
  #processor.task_from_file(sys.argv[1],sys.argv[2])
  print 'ok'



