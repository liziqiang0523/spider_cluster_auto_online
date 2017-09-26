#!/usr/local/bin/python2.7/python
#coding=utf-8
#author:liziqiang
'''
  定期从api拉proxy，写入SSDB的proxy
'''

import sys, confs, urllib2, logging, datetime
from ssdb import StrictSSDB
#sys.path.append("/data/warningmail/")
#from except_mail_warning import *
logging.basicConfig(level = logging.INFO, 
  format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', 
  datefmt = '%a, %d %b %Y %H:%M:%S',
  stream = sys.stdout)

class AddProxy:
  def __init__(self):
    self.apis_all = {
        #未绕防火墙，直接请求的。
        #"https":"http://ttvp.daxiangip.com/ip/?tid=559466752999190&num=5000&protocol=https&foreign=none",
        #"http":"http://ttvp.daxiangip.com/ip/?tid=559466752999190&num=5000&protocol=http&foreign=none",
        #从佛山机房绕
        #"https":"",
        #"http":"",
        }
    self.apis_filter = {
        "https":"",
        "http":"",
        }
    self.proxy_db = StrictSSDB(host = confs.SSDB_PROXY_HOST, port = confs.SSDB_PROXY_PORT)

  def process_rawtxt(self, api_url, schema):
    print 'api_url:%s' % api_url
    response = urllib2.urlopen(api_url)
    page = response.read()
    parts = page.strip().split("\n")
    print 'get proxy num:[%d] at [%s]' % (len(parts), datetime.datetime.now())
    for part in parts:
      if len(part.strip()) < 6: continue
      if len(part.split(":")) != 2: continue
      proxy = "%s://%s" % (schema, part.strip())
      if self.proxy_db.get(proxy):
        pass
        #print self.proxy_db.get(proxy)
      else:
        print proxy
        self.proxy_db.set(proxy, 0)

  def process_all(self):
    for schema, api in self.apis_all.items():
      self.process_rawtxt(api, schema) 

  def process_inc(self):
    for schema, api in self.apis_filter.items():
      self.process_rawtxt(api, schema) 

  #清理代理数据库，只保留制定数量，其余淘汰
  def clean_proxy(self, min_live = 3000, max_ftime = 50, limit = 200000):
    items = self.proxy_db.scan('', '', limit)
    proxy_list_kv = [(k,v) for k,v in items.items()]
    #失败次数最小的排在最前面
    proxy_list_sortedkv = sorted(proxy_list_kv, key = lambda x: int(x[-1]))
    #删除失败次数过多的
    total, cnt = 0, 0
    #遍历
    for (k,v) in proxy_list_sortedkv[500:]:
      total += 1
      #为零的 不过滤
      if int(v) >= max_ftime:
        self.proxy_db.delete(k)
        cnt += 1
        logging.info('清除失败次数过多的代理[%s] value[%s]' % (k, v))
    logging.info('清除失败次数过多的代理[%d]个 总数[%d]' % (cnt, len(items)))
      
    #10万以后的代理基本可以认为是无效的积压代理，应删除掉
    for (k,v) in proxy_list_sortedkv[10000:]:
      self.proxy_db.delete(k)
      logging.info("清除长尾代理")

if __name__ == "__main__":
  adder = AddProxy()
  try:
   #默认进行增量更新
   if len(sys.argv) == 1:
     print 'update proxy increment'
     adder.process_inc()
   elif sys.argv[1] == "all":
     print 'update proxy all'
     adder.process_all()
     adder.clean_proxy()
   elif sys.argv[1] == 'clean':
     print 'clean proxy'
     adder.clean_proxy()
  except  Exception, e:
    print e
    #except_mail = Except_mail()
    #except_mail.send_mail(cmd_dic = {
     # 'warning':'维护8889代理池，新增、更新代理异常',
     # 'path':'/data/spider_cluster_auto_online/data_process/addproxy.py',
     # 'interval_time':300})
