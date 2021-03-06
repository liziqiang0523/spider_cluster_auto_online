#!/usr/bin/python
#coding=utf-8
#author:shiyuming,liziqiang,liuchenggang
'''
  下载中间件：设置代理；更新url的下载状态
'''

import sys, logging, traceback, urlparse,random,base64,copy
from datetime import datetime
from urllib import getproxies, unquote, proxy_bypass
from scrapy.utils.httpobj import urlparse_cached
from oreo import settings
from oreo.user_agents import agents

from oreo.facade import facade
from twisted.internet.error import TimeoutError, DNSLookupError, ConnectionRefusedError, ConnectionDone, ConnectError, ConnectionLost, TCPTimedOutError
from scrapy.xlib.tx import ResponseFailed
from twisted.internet import defer
from scrapy.exceptions import IgnoreRequest
try:
    from urllib2 import _parse_proxy
except ImportError:
    from urllib.request import _parse_proxy
from six.moves.urllib.parse import urlunparse
from scrapy.utils.python import to_bytes
import base64

from six.moves.urllib.parse import urljoin
from w3lib.url import safe_url_string
from scrapy.downloadermiddlewares.redirect import BaseRedirectMiddleware

reload(sys)
sys.setdefaultencoding('utf8')

'''
  代理中间件
  放在默认的Proxy中间件之后，更靠近Downloader一些
'''

#判断是否死链
def is_url_deadlink(url):
  if 'error/' in url or '/error' in url or '404.' in url:
    return True
  return False

class Proxy100Middleware(object):

  def __init__(self):
    self.proxy_list = copy.copy(settings.PROXY_LIST)
    random.shuffle(self.proxy_list)

  def process_request(self,request,spider):
    if request.meta.get('no_proxy', 0) >= 1:
      logging.info('免代理 url=[%s]' % request.url)
      return
    if len(self.proxy_list) < 1:
      self.proxy_list = copy.copy(settings.PROXY_LIST)
      random.shuffle(self.proxy_list)
    proxy = self.proxy_list.pop()
    request.meta['proxy'] = proxy['proxy_url']
    proxy_user_pass = proxy['proxy_user_pass']
    encoded_user_pass = base64.encodestring(proxy_user_pass)
    request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass
    logging.info('设置代理为视频下载代理，请降低抓取频率。proxy:%s' % proxy['proxy_url'])

class AddProxy(object):
  
  def __init__(self):
    #代理池
    self.proxy_pool = {}
    #代理池最后更新时间
    self.lastupdate_minute = datetime.now().minute
    self.auth_encoding='latin-1'
  
  #更新代理池
  def update_proxy_pool(self):
    self.lastupdate_minute = datetime.now().minute
    proxy_list_http = facade.get_proxy(scheme = 'http')
    proxy_list_https = facade.get_proxy(scheme = 'https')
    proxy_list = proxy_list_http + proxy_list_https
    logging.info("update_proxy_pool 代理数量：http-%d https-%d at [%s]" % (len(proxy_list_http), len(proxy_list_https), datetime.now()))
    if len(proxy_list) < 100:
      logging.warning("代理耗尽，不能支持爬虫运行")
      print("代理耗尽，不能支持爬虫运行")
      sys.exit(1)
    for proxy in proxy_list:
      #parse proxy_url
      proxy_type, creds, proxy_url = self.get_proxy_one(proxy)
      self.proxy_pool.setdefault(proxy_type, [])
      self.proxy_pool[proxy_type].append([creds,proxy_url])
      #logging.debug('增加代理：proxy[%s] creds:[%s] proxy_url:[%s] now pool-len:%d' % (proxy, creds,proxy_url, len(self.proxy_pool)))
    logging.info('成功更新代理[%d]个 at:[%s]' % (len(proxy_list), datetime.now()))

  def get_proxy_one(self, url, orig_type = None):
    proxy_type, user, password, hostport = _parse_proxy(url)
    proxy_url = urlunparse((proxy_type or orig_type, hostport, '', '', '', ''))
    if user:
      user_pass = to_bytes(
        '%s:%s' % (unquote(user), unquote(password)),
      encoding=self.auth_encoding)
      creds = base64.b64encode(user_pass).strip()
    else:
      creds = None
    return proxy_type, creds, proxy_url

  #设置代理
  def process_request(self, request, spider):
    #无代理可用 或 不需要代理（如localhost）
    if request.meta.get('no_proxy', 0) >= 1:
      logging.info('免代理 url=[%s]' % request.url)
      return

    #按照scheme取代理
    parsed = urlparse_cached(request)
    scheme = parsed.scheme if parsed.scheme in self.proxy_pool else 'http'
    #不能使用代理
    if proxy_bypass(parsed.hostname):
      logging.info('不能使用代理. parsed.hostname:%s' % parsed.hostname)
      return

    if scheme not in self.proxy_pool or len(self.proxy_pool.get(scheme)) < 1:
      self.update_proxy_pool()
    if len(self.proxy_pool[scheme]) < 1:
      logging.warning("更新代理库后仍然没有适合[%s]的代理，使用http协议替换" % scheme)
      scheme = 'http'

    #设置代理
    creds,proxy_url = self.proxy_pool[scheme].pop()
    logging.debug('取出一个代理. creds=[%s] proxy_url=[%s]' % (creds, proxy_url))
    request.meta['proxy']=proxy_url
    if creds :
      request.headers['Porxy-Authorization'] = creds
    logging.debug('代理设置. url=[%s] proxy_url:%s' % (request.url, proxy_url))
    return

'''
  更新url的下载状态
  放在retry之前，更靠近downloader一些
'''
class StatusUpdater(object):
  
  def process_response(self, request, response, spider):
    url = response.url
    task_url = request.meta['url'] if 'url' in request.meta else 'nourl'
    status = response.status
    ret = facade.update_link_status(spider.name, url, status)
    #暂停该逻辑，因为可能导致百度爬虫的抓取干扰其他爬虫的链接发现
    #如果更新失败，则可能是该链接不存在与linkbase中，所以，如果该链接下载成功，应该将其保存到linkbase中，避免重复下载。前提是能从request中取到完整的linkinfo，且当前url与linkinfo中的url不一致（说明该url与linkbase中的该url是有关联且应该保存的）
    #if not ret and status == 200:
    #  linkinfo = request.meta
    #  linkinfo['url'] = url
    #  facade.save_2_linkbase(linkinfo)
    #  logging.info('save link that not exists in linkbase. url[%s]' % url)
    proxy_info = request.meta.get('proxy', '')
    logging.info('更新下载链接状态  status=[%s] url=[%s] tasl_url=[%s] proxy:%s' % (status, url, task_url, proxy_info))
    if response.status >= 400 or is_url_deadlink(url) or is_url_deadlink(task_url):
      facade.update_proxy(proxy = proxy_info, flag = 1)
      #抓失败则发送会任务队列调度 注意通过needrecrawl可以设置不走kafka调度 如在线爬虫是不需要这个重读调度的
      linkinfo = request.meta
      if 'spider_name' in linkinfo and settings.NEED_RECRAWL:
        logging.info("下载失败重回队列 url:%s" % linkinfo['url'])
        topic = linkinfo['spider_name']
        facade.send_linkinfo_back2_taskqueue(linkinfo, topic, status = status, url_resp = url)
    return response

'''
  每次用代理下载后，如果下载成功，代理有消息+1 失败则-1
  本中间件要放在比RetryMiddleware更靠近downloder的位置
  放在自己的代理中间件之后，更靠近downloder一些
'''
class ProxyValidUpdate(object):

  def process_response(self, request, response, spider):
    proxy = request.meta.get('proxy', '')
    if proxy == '':
      logging.info("无代理下载 status:%s. url:%s" % (response.status, request.url))
      return response
    if 200 <= response.status < 400 and not is_url_deadlink(response.url) and not is_url_deadlink(request.url):
      facade.update_proxy(proxy = proxy, flag = -1)
      logging.info("update proxy -1 激励代理. url:%s response-url[%s] proxy:%s status[%d]" % (request.url, response.url, proxy, response.status))
    else:
      facade.update_proxy(proxy = proxy, flag = 1)
      logging.info("update proxy +1 惩罚代理. url:%s response-url[%s] proxy:%s status[%d]" % (request.url, response.url, proxy, response.status))
    return response

'''
  处理下载异常，当发生下载异常时，如果是超时异常 
'''
class ExceptionHandler(object):
  #需要处理的异常
  EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError, 
      ConnectionRefusedError, ConnectionDone, ConnectError,
      ConnectionLost, TCPTimedOutError, ResponseFailed,
      IOError)
  
  def process_request(self, request, spider):
    logging.debug("ExceptionHandler记录发送req:%s" % request.url)
    return None

  def process_response(self, request, response, spider):
    logging.info("获得下载结果:%s  resp-url:%s" % (request.url, response.url))
    return response

  def process_exception(self, request, exception, spider):
    #处理downloader异常
    #打印出下载错误 可供估算代理有效率
    task_url = request.meta['url'] if 'url' in request.meta else 'nourl'
    proxy = request.meta['proxy'] if 'proxy' in request.meta else 'noproxy'
    logging.info("发现下载异常 [%s]. url-req:%s task-url[%s] proxy[%s]" % (exception, request.url, task_url, proxy))
    #更新代理 有效性-1
    if proxy == '':
      logging.info("发现下载异常，未使用代理. url:%s task_url:%s" % (request.url, task_url))
    else:
      facade.update_proxy(proxy = proxy, flag = 1)
      logging.info("update proxy +1 下载异常，惩罚代理. url:%s proxy:%s task_url:%s" % (request.url, proxy, task_url))
    #重新调度
    linkinfo = request.meta
    #print linkinfo
    if 'spider_name' in linkinfo and settings.NEED_RECRAWL:
      topic = linkinfo['spider_name']
      facade.send_linkinfo_back2_taskqueue(linkinfo, topic)
      logging.info("任务下载异常，重回任务下载队列. task:%s url-req:%s task_url:%s" % (topic, request.url, task_url))
    else:
      logging.info("任务下载异常，非linkinfo，不发送会任务下载队列 url-req:%s task_url:%s" % (request.url, task_url))
    #不需要其余的中间件进行处理了
    raise IgnoreRequest("任务下载异常，其他中间件忽略处理 url:%s. msg:[%s]" % (request.url, exception))
      
    return None


'''
  处理重定向百度链接抓取的请求:
    如果只是为了获得破解链接而不要求执行真实网页的抓取，则通过此中间件进行处理
    如果破解链接需要抓取真实网页，但不需要重复抓取真实网页
  处理方式：
    将跳转得到的真是网页写入response，返回response，不执行抓取。
'''
class RedirectBaiduencodingurlMiddleware(BaseRedirectMiddleware):
  
  def process_response(self, request, response, spider):
    #判断是否百度链接抓取
    if request.meta.get('baidu_justdecode', False) or (request.meta.get('baidu_decode', False) and request.meta.get('dup', False)):
      logging.debug("发现满足百度跳转链接处理流程的url. status:%s url:%s " % (response.status, request.url))

      if (request.meta.get('dont_redirect', False) or
          response.status in getattr(spider, 'handle_httpstatus_list', []) or
          response.status in request.meta.get('handle_httpstatus_list', []) or
          request.meta.get('handle_httpstatus_all', False)):
        logging.debug("不符合条件判断1 url:%s" % request.url)
        return response

      allowed_status = (301, 302, 303, 307)
      if 'Location' not in response.headers or response.status not in allowed_status:
        logging.debug("不符合条件判断2 url:%s" % request.url)
        return response

      location = safe_url_string(response.headers['location'])
      redirected_url = urljoin(request.url, location)
      #判断是否跳转到非百度域名
      domain_org = urlparse.urlparse(request.url).netloc
      domain_red = urlparse.urlparse(redirected_url).netloc
      logging.debug("处理百度跳转，domain_org:%s domain_red:%s" % (domain_org, domain_red))
      if domain_org == domain_red:
        return response
      logging.info("百度跳转处理成功，不执行真实url的抓取:%s baidu-url:%s" % (redirected_url, request.url))
      response_red = response.replace(url = redirected_url, status = 200, body = '')
      return response_red
    else:
      return response

class UserAgentMiddleware(object):
  def process_request(self,request,spider):
    agent = random.choice(agents)
    request.headers["User-Agent"] = agent
    logging.info("User-Agent:[%s]" % agent)

class CookiesMiddleware(object):
  def process_request(self,request,spider):
    cookie = facade.get_cookie()
    request.cookies = cookie
    logging.info("Cookie:[%s]" % cookie)

