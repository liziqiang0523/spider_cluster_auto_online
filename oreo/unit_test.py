#!/usr/local/bin/python
#coding=utf-8
#author:shiyuming
#对facade进行测试

import sys,traceback,logging

logging.basicConfig(level = logging.DEBUG, 
  format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', 
  datefmt = '%a, %d %b %Y %H:%M:%S',
  filename = './log/unit_test.log',
  filemode = 'w')

'''
from oreo.spiders.requestscheduler import RequestScheduler
scheduler = RequestScheduler(topic = 'ask120')
scheduler.get_request()

sys.exit(0)
from scrapy.http.request import Request
from scrapy.http.response import Response

from oreo.middlewares.downloadmiddleware import AddProxy, StatusUpdater, ProxyValidUpdate
req = Request("http://www.mdomain.com/1")
resp = Response('http://www.mdomain.com/1')
adder = AddProxy()
adder.process_request(req, None)
#status_updater = StatusUpdater()
#status_updater.process_response(req, resp, None)
#proxy_updater = ProxyValidUpdate()
#proxy_updater.process_response(req, resp, None)


sys.exit(0)
from oreo.spiders.basesite import BasesiteSpider
from scrapy.http.response import Response
spider = BasesiteSpider()
resp = Response('http://www.mdomain.com')
spider.parse(resp)



sys.exit(0)
from oreo.spiders.requestscheduler import RequestScheduler
scheduler = RequestScheduler('mdomain.com')
def process():
  requests = scheduler.process(None)
  for request in requests:
    print request.meta
process()
sys.exit(0)
'''


from oreo.facade import facade

urlinfo = {'spider_name':'ask120', 'url':'http://www.120ask.com/question/15014422.htm'}
facade.send_linkinfo_2_kafka(urlinfo, 'ask120')
#facade.update_schedule_time(urlinfo['spider_name'], urlinfo['url'])

def save_page():
  page_body = '<html>xxxx</html>'
  url = 'http://test3.html'
  page_item = {'url':url, 'spider_name':'test'}
  facade.save_page(page_item, page_body)
#save_page()

#facade.get_page_filename('http://test3.html')

#测试失败：kafka中积压的消息不会去取
#linkbase测试正常
def save_links():
  linkinfos = [{'from_url':'http://www.baidu.com', 'url':'http://www.mdomain.com/12', 'spider_name':'spider1', 'item_type':'question'}]
  facade.save_links(linkinfos = linkinfos, from_url = 'http:www.fromurl.com', topic = 'spider1')
  print 'save link SUC'
#save_links()

def update_link_status():
  facade.update_link_status("jd", 'http://item.jd.com/1442986812.html', 200)
  print 'Done'
#update_link_status()

def get_proxy():
  proxy_list = facade.get_proxy()
  print proxy_list
  if len(proxy_list) > 0:
    #print '\n'.join(proxy_list)
    print 'get proxy_list[%d] first:%s' % (len(proxy_list), proxy_list[0])
  else:
    print 'get proxy empty'
#get_proxy()

#测试更新代理的效果计数
#facade.update_proxy("http://120.198.245.36:8080", -1, need_add_when_notexists = True)

facade.import_proxy("./data/tmp_proxy.txt")

#测试更新linkinfo中的调度次数
#facade.update_schedule_time('ask120', 'http://www.120ask.com/question/49396776.htm')

#清理代理数据库，只保留制定数量，其余淘汰
#facade.clean_proxy()
