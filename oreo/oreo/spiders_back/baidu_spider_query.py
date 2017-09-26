#!/usr/bin/python
#coding=utf-8
#author:liziqiang
'''
  破解百度抓取的爬虫
  采用多级联的抓取方式，下载部分还是交给爬虫，如何破解的部分是各站点不一样的，定向编码解决
  百度抓取第一步：
    使用特定的header下载首页，得到rsv_pq。在启动函数start_requests里发第一步请求。
  第二步：
    获取下载任务，通过query和第一步得到的rsv_pq拼出下载query下载链接 发送下载任务。
  第三步：
    从query的下载结果中解析搜索结果
'''

import sys, re,traceback, logging, math, time, datetime, urllib
from scrapy.spiders import Spider
from scrapy.http import Request
#from scrapy.baseparser import BaseParser
from oreo.facade import facade
from scrapy.linkextractors import LinkExtractor
from oreo import settings
from oreo.parser.baidu_query import BaiduQueryParser

reload(sys)
sys.setdefaultencoding('utf8')

class BaiduSpider(Spider):
  
  #爬虫的唯一id号，格式：20151109_16_01_59 有这个id，当爬虫的name相同时，能区别出实例
  mid = "mid"
  #以dianping网为例
  name = "baidu_query"
  task_query = "baidu_query"
  baidu_justdecode = False
  allowed_domain = []
  #其实抓取url 通常是列表页第一页 eg:http://www.dianping.com/search/category/2/0/p1
  start_urls = []
  #目标网页的所在区域和解析规则 eg： [{'xpath':'//li[contains(@class,"shopname")]/a[1]','allow':r'.*dianping.com/shop/\d+.*','deny':(),'itemtype':'shop'}]
  no_proxy = 0
  #最大调度数量 用于避免一个爬虫持续工作太久而导致内存占用量过大
  max_request_num = settings.MAX_REQ_NUM
  #是否执行跳转抓取。通常是允许的（False）
  dont_redirect = False
  #实际爬虫相应的解析器
  parsers = []
  #是否保存网f页
  drop_page = settings.DROP_PAGE
  #破解url结果保存表
  decode_url_table_name = 'baidu_seitem'
  #要抓多页的，或对同一个query使用不同语法抓取
  se_url_patterns = [
    'https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=0&rsv_idx=1&tn=baidu&wd=%s&rsv_pq=%s&rsv_t=%s&rqlang=cn&rsv_enter=1&rsv_sug3=6&rsv_sug1=5&rsv_sug7=100&rsv_sug2=0&inputT=809&rsv_sug4=1240&rsv_sug=1' 
    ]
  baiduparser = BaiduQueryParser()

  #初始进行调度
  def start_requests(self):
    #iqid参数的获取正则
    self.porg_pq = re.compile(r'name="rsv_pq" value="(\w+)"')
    self.porg_t = re.compile(r'name="rsv_t" value="([\w/+]+)"')
    self.porg_realurl = re.compile(r"META http-equiv=.*URL='(http[a-zA-z]*://.+)'")
    #mid赋值
    self.mid = datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")
    logging.info('mid[%s]初始调度...' % self.mid)
    #如果还有query，则触发第一步流程
    query_num =  facade.get_query_num(self.task_query)
    logging.info("任务队列中query总量:%s" % query_num)
    if query_num > 0:
      #第一步，通过代理下载获得cookie 尝试至少20次下载 以确保本次爬虫任务能进行下去
      for i in range(1):
        req = Request('http://www.baidu.com', dont_filter=True)
        req.meta['q_flag'] = 2
        logging.info('第一步，使用代理获取cookie')
        yield req

    #加载其他任务进行下载
    tasks = facade.get_task(self.name, self.max_request_num)
    logging.info("加载被中断任务数：%d" % len(tasks))
    for task in tasks:
      task['url'] = task['url'].replace('http://', 'https://')
      req = Request(task['url'], dont_filter=True)
      for k,v in task.items():
        if k in ['redirect_urls']: continue
        req.meta[k] = v
      yield req

  def parse(self, response):
    if response.status >= 400 or response.status < 200:
      logging.debug('下载失败. status:%s url-req:%s url-res:%s' % (response.status, response.request.url, response.url))
      return []
    #保存网页
    page_item = self.save_page(response)
    #通过req种的q_flag来判断上一步是第几步，决定下一步该怎么走
    q_flag = int(response.request.meta.get('q_flag', 1))
    logging.debug('q_flag:%d' % q_flag)
    #第二步：获取下载任务，通过query和第一步得到的rsv_pq拼出下载query下载链接 发送下载任务。
    if q_flag == 2:
      #print 'process_step2'
      return self.process_step2(response)
    #第2步：从query的下载结果中解析搜索结果，此时的搜索结果url是百度加密链接，需要破解，破解方式是把加密链接抓取一次302跳转
    elif q_flag == 3:
      #print 'process_step3'
      return self.process_step3(response, page_item)
    #第四步 破解加密连接请求返回结果。破解后的真实url就在其中，取出保存item
    elif q_flag == 4:
      #print 'process_step5'
      return self.process_step4(response, page_item)
    else:
      #print 'process_stepNULL'
      logging.warning("q_flag不合法:%s" % q_flag)
    return []

  #第二步：执行query查询，通过query和第一步得到的rsv_pq拼出下载query下载链接 发送下载任务。
  def process_step2(self, response):
    reqs = []
    body = response.body_as_unicode().encode('utf-8')
    rsv_pq = self.porg_pq.search(body)
    if rsv_pq is not None:
      rsv_pq = rsv_pq.group(0)
      logging.warning('第2步：得到了rsv_pq:%s' % rsv_pq)
    else:
      logging.warning('第2步失败：没有得到rsb_qd')
    rsv_t = self.porg_t.search(body)
    if rsv_t is not None:
      rsv_t = rsv_t.group(0)
      logging.info('第2步：得到了rsv_t:%s' % rsv_t)
    else:
      logging.info('第2步失败:没有得到rsv_t')
    if rsv_pq is None or rsv_t is None:
      return reqs
    #获取下载任务，通过query和第一步得到的rsv_pq拼出下载query下载链接 发送下载任务。
    for queryinfo in facade.get_query(self.task_query ,98500):# self.max_request_num / 4):
      #print queryinfo
      query_quote = queryinfo['query'] # urllib.quote(query)
      for pattern in self.se_url_patterns:
        url = pattern % (query_quote, rsv_pq, rsv_t)
        logging.debug('第2步，发送下载连接:%s' % url)
        req = Request(url, dont_filter=True)
        req.meta['q_flag'] = 3
        req.meta['query'] = query_quote
        #保存linkinfo
        linkinfo = {'url':url, 'from_url':'', 'ref_url':'', 'spider_name':self.name, 'status':0, 'failed_cnt':0, 'in_time':math.floor(time.time()), 'update_time':math.floor(time.time()), 'dont_redirect':self.dont_redirect}
        
        linkinfo.update(queryinfo)
        for k,v in linkinfo.items():
          if k in ['redirect_urls']: continue
          req.meta[k] = v
        reqs.append(req)
    #print '加载其他任务进行下载:%d' % len(reqs)
    return reqs

  #第三步：从query的下载结果中解析搜索结果，此时的搜索结果url是百度加密链接，需要破解，破解方式是把加密连接发送下载请求出去
  #顺便透传搜索结果中的title和summery
  def process_step3(self, response, page_item):
    reqs=[]
    items = self.baiduparser.process_page(page_item, html_body = page_item['html_body'] if 'html_body' in page_item else None,page_url=response.url)
    return 
    #items = self.baiduparser.process_page(page_item, html_body = page_item['html_body'] if 'html_body' in page_item else None, p_facade = facade)
    logging.info("第3步，解析搜索结果[%d]个" % len(items))
    linkinfos = []
    for item in items:
      reqs.append(req)
      linkinfo = {'url':item['url'], 'from_url':response.url, 'ref_url':response.url, 'spider_name':self.name, 'status':0, 'failed_cnt':0, 'in_time':math.floor(time.time()), 'update_time':math.floor(time.time()), 'dont_redirect':self.dont_redirect, 'query':response.request.meta.get('query', ''), 'baidu_decode':True, 'baidu_justdecode':self.baidu_justdecode}
      linkinfo['q_flag'] = 4
      #meta中加入query 上一步request的透传信息（在meta中以tst_开头的字段）
      self.process_tst_info(target = linkinfo, src = response.request.meta)
      self.process_tst_info(target = linkinfo, src = item)
      linkinfos.append(linkinfo)
    facade.save_links(linkinfos = linkinfos, from_url = response.url, topic = self.name, need_filter = False)
    return reqs

  #第四步：破解加密连接请求返回结果。破解后的真实url就在其中，取出保存item
  def process_step4(self, response, page_item):
    body = response.body_as_unicode().encode('utf-8')
    real_url = response.url
    logging.info('第4步：通过跳转破解加密连接，得到real_url:%s' % real_url)
    if 'www.baidu.com/link?url' in real_url:
      logging.warning("破解失败，链接仍然是百度加密url:%s" % real_url)
      return []
    #保存搜索结果
    item = {'real_url':real_url, 'crawl_time':math.floor(time.time()), 'query':response.request.meta.get('query','')}
    self.process_tst_info(target = item, src = response.request.meta)
    logging.debug("通过跳转破解加密连接seitem:%s" % item)
    #保存
    where = {'query':item.get('query',''), 'real_url':item.get('real_url', '')}
    facade.update_item(self.decode_url_table_name, where, item) 
    for parser in self.parsers:
      items = parser.process_page(page_item, html_body = page_item['html_body'] if 'html_body' in page_item else None, p_facade = facade)
      for item in items:
        #透传字段 
        self.process_tst_info(target = item, src = response.request.meta)
        parser.save_item(item)
        logging.debug('解析出的完整item:\n  %s' % '  \n '.join(['%s:%s' % (k,v) for k,v in item.items()]))
    return []
    
  #保存网页 -- page-body保存在FS中，结构化信息保存入mongo
  def save_page(self, response):
    body = ""
    encoding = ''
    try:
      body = response.body_as_unicode().encode('utf-8')
      logging.debug("成功取得respose-body req-url:%s resp-url:%s" % (response.url, response.request.url) )
    except Exception,e:
      logging.debug("获取respose-body失败 req-url:%s resp-url:%s" % (response.url, response.request.url) )
      return  None
    #meta中的信息是创建Request的时设置的
    page_item = response.meta
    page_item['url'] = response.request.url
    page_item['encoding_ori'] = encoding
    page_item['status'] = response.status
    page_item['spider_name'] = self.name
    page_item['ref_url'] = response.request.meta.get('from_url', '')
    facade.save_page(page_item, body, drop_page = self.drop_page)
    #避免将page本身保存到了数据库
    page_item['html_body'] = body
    return page_item

  #处理透传信息 把src中中以tst_开头的kv对复制到target字典对象中。 src是数据源，通常是response.request.meta target是透传信息要到达的item
  def process_tst_info(self, target = {}, src = {}):
    for k,v in src.items():
      if k[:4] == 'tst_':
        target[k] = v

