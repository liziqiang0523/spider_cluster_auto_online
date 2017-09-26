#!/usr/bin/python
#coding=utf-8
#author:liziqiang
import HTMLParser
'''
  爬虫基类

  每只爬虫起来之后主要只做3件事：
  1、拿到任务（消息队列和start_url），发送请求。
  2、请求成功后去挖掘新的url,挖掘到新的url 只存数据库。 不继续请求。 
  3、请求成功后去 解析出干净的结构化数据。 


logging.basicConfig(level = logging.INFO, 
  format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', 
  datefmt = '%a, %d %b %Y %H:%M:%S',
  filename = '%s/%s' % (settings.LOG_PATH, settings.LOG_SPIDER),
  filemode = 'a')
'''

import sys, re,traceback, logging, math, time, datetime
#from requestscheduler import RequestScheduler
from scrapy.spiders import Spider
from scrapy.http import Request
#from scrapy.baseparser import BaseParser
from oreo.facade import facade
from scrapy.linkextractors import LinkExtractor
from oreo import settings

reload(sys)
sys.setdefaultencoding('utf8')

class BasesiteSpider(Spider):
  
  #爬虫的唯一id号，格式：20151109_16_01_59 有这个id，当爬虫的name相同时，能区别出实例
  mid = "mid"
  #以dianping网为例
  name = ""
  allowed_domain = []
  #其实抓取url 通常是列表页第一页 eg:http://www.dianping.com/search/category/2/0/p1
  start_urls = [{'url':'xxx','parser_ranks':[],'link_types':['list_url']}]
  #目标网页的所在区域和解析规则 eg： {'list_url':[{'xpath':'//li[contains(@class,"shopname")]/a[1]','allow':r'.*dianping.com/shop/\d+.*','deny':()}]}
  xTargets = {}
  #列表页至少要挖出的item数量
  min_itemnum = 1 
  min_listnum = 1 
  #是否需要代理 1-不需要代理 0-需要代理
  no_proxy = 0
  #Request调度器
  topic = ''
  scheduler = None
  #最大调度数量 用于避免一个爬虫持续工作太久而导致内存占用量过大
  max_request_num = settings.MAX_REQ_NUM
  #是否执行跳转抓取。通常是允许的（False）
  dont_redirect = False
  #实际爬虫相应的解析器
  parsers = []
  #是否保存网f页
  #drop_page = False
  drop_page = settings.DROP_PAGE
  header_rq=None
  urls_requested = set()
  urls_suc = set()
  urls_failed = set()
  
  def __init__(self,query = None , *args , **kwargs):
    super(BasesiteSpider,self).__init__(*args,**kwargs)
    self.query=query
    if query != None:
      self.start_urls = ['http://s.weibo.com/list/relpage?search=%s&limitType=article&page=1' % query ]

  #初始进行调度 避免种子也被屏蔽而导致爬虫启动不起来
  def start_requests(self):
    #mid赋值
    self.mid = datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")
    for url in self.start_urls:
      req = self.make_requests_from_url(url['url'])
      req.meta['no_proxy'] = self.no_proxy
      req.meta['parser_ranks'] = url.get('parser_ranks',[])
      req.meta['link_types'] = url.get('link_types','')
      yield req
    logging.info('mid[%s]初始调度...' % self.mid)
    for task in facade.get_task(self.name, self.max_request_num):
      domain = task['url'].split('://')[-1].split('/')[0]
      if len(self.allowed_domain) > 0 and domain not in self.allowed_domain:
        facade.delete_domain_no_match(task['url'])
        logging.info('domain not in allowed_domain and delete it from linkbase.url:%s' % task['url'])
        continue
      #脏url过滤
      #changed by gxc at 2017/2/9 change:添加header
      req = Request(task['url'], dont_filter=True,headers=self.header_rq)
      req.meta['no_proxy'] = self.no_proxy
      for k,v in task.items():
        req.meta[k] = v
      yield req
  
  def parse(self, response):
    requests, linkinfos, dups = [], [], set()
    #无效下载 直接返回补充的url 而不进行保存的解析url
    if response.status >= 400 or response.status < 200:
      proxy = response.meta['proxy'] if 'proxy' in response.meta else ''
      task_url = response.meta['url'] if 'url' in response.meta else 'nourl'
      logging.warning("crawl failed. url[%s] task-url[%s] status[%d] proxy:[%s]" % (response.url, task_url, response.status, proxy))
      return requests
    logging.info('成功获得response. status=[%d]' % response.status)
    #保存网页
    page_item = self.save_page(response)
    if page_item is None:
      return requests

    #从response中解析出新的链保存到linkbase和消息队列中。
    linkinfos = self.extract_links(response, dups)
    facade.save_links(linkinfos = linkinfos, from_url = response.url, topic = self.name)
    link_types = response.request.meta.get('link_types','')
    for link_type in link_types:
      for parser in self.parsers:
        if link_type not in  parser.link_types:
          continue
        items = parser.process_page(page_item, html_body = page_item['html_body'] if 'html_body' in page_item else None, page_url = response.request.url)
        if len(items) < 1:
          logging.warning('parser:[%s] 没有从 url:%s中 解析到 item，不符合预期' % (parser.parser_name,response.request.url))
        logging.info('parser:[%s] 解析url:%s 完成，获得item数量 %d ----------' % (parser.parser_name,response.url, len(items)))

    return requests

  #保存网页 -- page-body保存在FS中，结构化信息保存入mongo
  def save_page(self, response):
    body = ""
    try:
      body = response.body_as_unicode().encode('utf-8')
      logging.debug("通过body_as_unicode()获得html-body . " )
    except Exception,e:
      logging.warning('通过body_as_unicode()获得html-body失败 ')
      return  None
    #meta中的信息是创建Request的时设置的
    page_item = response.meta
    page_item['url'] = response.url
    page_item['status'] = response.status
    page_item['spider_name'] = self.name
    page_item['ref_url'] = response.request.meta.get('from_url', '')
    if response.request.meta.get('query',None) is not None:
      page_item['query']=response.request.meta['query']
    facade.save_page(page_item, body, drop_page = self.drop_page)
    #避免将page本身保存到了数据库
    page_item['html_body'] = body
    return page_item
    
  #按规则发掘链接
  def extract_links(self, response, dups):
    #用target页的规则挖需要解析url
    link_types = response.request.meta.get('link_types',[])
    logging.info('url:%s , link_types:[%s]' % (response.request.url,' '.join(link_types)))
    linkinfos = []
    for link_type in link_types:
      xtargets = self.xTargets.get(link_type,[])
      for p in xtargets:
        linkinfos.extend(self.extract_links_withrule(response, dups, p))
    return linkinfos

  #使用指定的rule对response进行解析 rule={'xpath':'','allow':(),'deny':(),'link_types':[]}
  def extract_links_withrule(self, response, dups, rule):
    logging.debug('执行extract-link. rule:%s' % rule)
    linkinfos = []
    if rule.get('xpath', None) is None or len(rule.get('xpath')) < 1:
      logging.debug("rule没有xpath，不执行具体的解析")
      return linkinfos
    sgml = LinkExtractor(allow_domains=self.allowed_domain, restrict_xpaths = (rule['xpath']), allow=rule['allow'], deny=rule['deny'],tags=('a'))
    links = sgml.extract_links(response)
    logging.info('从xpath挖出item-url数量[%d] url[%s] xpath:%s ' % (len(links), response.url, rule['xpath']))
    for link in links:
      if link.url in dups: continue
      dups.add(link.url)
      linkinfo = {'url':link.url, 'from_url':response.url, 'spider_name':self.name, 'status':0, 'schedule_cnt':0, 'failed_cnt':0, 'in_time':math.floor(time.time()), 'update_time':math.floor(time.time()), 'dont_redirect':self.dont_redirect,'link_types':rule.get('link_types',[])}
      if rule.get('rule', None) is not None:
        linkinfo['rule'] = rule.get('rule')
      linkinfos.append(linkinfo)
      logging.debug('target link:%s from_url:%s' % (link.url, response.url))
    logging.debug('[%d]个targetLink extract from url:%s' % (len(linkinfos), response.url))
    if rule['xpath'] == 'regex':
      html_parser = HTMLParser.HTMLParser()
      txt = html_parser.unescape(response.body)
      urls = re.findall(rule['allow'],txt)
      logging.info('从regex挖出item-url数量[%d] url[%s] xpath:%s ' % (len(urls), response.url, rule['xpath']))
      for url in urls:
        if url in dups: continue
        dups.add(url)
        linkinfo = {'url':url, 'from_url':response.url, 'spider_name':self.name, 'status':0, 'schedule_cnt':0, 'failed_cnt':0, 'in_time':math.floor(time.time()), 'update_time':math.floor(time.time()), 'dont_redirect':self.dont_redirect}
        linkinfos.append(linkinfo)
        logging.debug('target link:%s from_url:%s' % (url, response.url))
    if len(linkinfos) == 0:
      spider_warning = {'spider_name':self.name,'rule':str(rule),'url':response.request.url}
      facade.update_item('spider_warning',{'rule':str(rule),'url':response.request.url},spider_warning)
      logging.warning('spider_name:%s,xtarget rule:%s,url:%s 挖掘到的新链接为0 ，不符合预期' % (self.name,str(rule),response.request.url))

    return linkinfos
