#!/usr/bin/python
#coding=utf-8
#author: shiyuming,liziqiang
'''
  爬虫与各种数据库或消息队列的交互层
  目前的功能包括：
    spider-调度从monog task 获取link-infos，创建Request加入下载调度；放入spider中间件中 不在此
    downloader中间件从linkbase获取最新的下载代理，用于轮训下载；放入downloader中间件自己维护
    downloader中间件更新link的下载状态（成功，或失败次数+1，更新到linkbase中）
    spider对下载成功的网页，保存到mongo中（page+linkinfo）；从网页中解析出新的url，判断是否在linkbase中，如果不在（新链接）则写入linkbase中并写入kafuka的不同主题队列中
    linkbase使用SSDB linkinfo:from_url, url, spider_name, item_type, status, schedule_cnt, failed_cnt, in_time, update_time 作为一个json保存在SSDB的value中 key是url
    linkbase的信息也会在mongo中放一份，便于统计分析和重抓调度
    爬虫离线解析mongo中的page，并把item保存到mongo中
    代理管理: 从ssdb的proxy存储实例中加载管理
logging.basicConfig(level = logging.INFO, 
  format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', 
  datefmt = '%a, %d %b %Y %H:%M:%S',
  filename = '%s/%s' % (settings.LOG_PATH, settings.LOG_FACADE),
  filemode = 'a')
'''

import sys, hashlib, os, re, string, traceback, datetime, time, json, math, logging, urlparse, threading, random
import logging
import settings
from pymongo import MongoClient
from pymongo.collection import Collection
from ssdb import StrictSSDB
#from pykafka import KafkaClient, Topic
from pymongo import IndexModel, ASCENDING, DESCENDING

reload(sys)
sys.setdefaultencoding('utf8')

# 数据库适配器
class Facade():

  def __init__(self):
    #mongo用于存储原始page
    mongo_client = MongoClient(host = settings.MONGO_HOST, port = settings.MONGO_PORT)
    self.mongo_db = mongo_client.get_database(settings.MONGO_DB_NAME)
    self.mongo_page_col = Collection(self.mongo_db, settings.MONGO_COLLECT_PAGE)
    mongo_task_client = MongoClient(host = settings.MONGO_TASK_HOST, port = settings.MONGO_PORT)
    self.mongo_task = mongo_task_client.get_database(settings.MONGO_TASK_DB_NAME)
    self.mongo_dead_col = Collection(self.mongo_task, "dead_col")
    #SSDB用于存储linkbase 使用api的形式与Redis类似
    self.linkbase = StrictSSDB(host = settings.SSDB_LINKBASE_HOST, port = settings.SSDB_LINKBASE_PORT)
    #self.linkbase_mongo = self.mongo_db.linkbase
    self.linkbase_mongo = Collection(self.mongo_db, "linkbase")
    StrictSSDB(host = settings.SSDB_LINKBASE_HOST, port = settings.SSDB_LINKBASE_PORT)
    #kafuka
    #self.kafka = KafkaClient(settings.KAFKA_HOSTPORT)
    #self.link_producer = None
    #self.last_topic = None
    #proxy管理
    self.proxy = StrictSSDB(host = settings.SSDB_PROXY_HOST, port = settings.SSDB_PROXY_PORT)
    #图片原始地址与下载地址的对应关系数据库
    self.imageurl_mapper = StrictSSDB(host = settings.SSDB_IMGDB_HOST, port = settings.SSDB_IMGDB_PORT)
    #保存网页到文件系统中
    self.last_save_time = '2015_01_01_01'
    self.lock_savepage = threading.RLock()
    #代理的最大失败次数，超过这个数就不再选用并且从数据中删除
    self.max_failed_time = 50
    #最大调度次数 
    self.max_schedule_cnt = 50
    #最大下载失败次数 超过这个数就认为是死链。包括因为代理时效导致的下载失败 这不可避免地会有误判
    self.max_failed_cnt = 50
    self.cols_hasindex = set()

  #把成功下载图片地址与图片原始地址保存入库
  def save_imgs_suc(self, item, cost = 0):
    try:
      where = { 'file_name':item['file_name'] }
      self.mongo_db.suc_pic.update(where,item,True)
      self.imageurl_mapper.hset(settings.SSDB_IMGDB_HTABLE, item['url'], item['file_name'])
      time_begin = datetime.datetime.strptime(item.get('in_time',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')
      time_end = datetime.datetime.strptime(item.get('suc_time',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')
      cost = time_end - time_begin
      logging.info('下载成功的图片写入库 耗时:%s in_time:%s now:%s img_org:%s img_local:%s' % (cost.total_seconds(), time_begin, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item['url'], item['file_name']))
    except Exception,e:
      logging.warning("保存下载成功的图片状态时异常 img-url:%s  mgs:%s" % (item, e))

  #将下载失败的图片送回图片下载消息队列
  def save_imgs_failed(self, task_mq_name, urls_failed_info):
    if len(urls_failed_info) < 1: return
    logging.info('下载失败的图片任务重新入队列, num:%d, detail...' % (len(urls_failed_info)))
    #detail = [ '%s:%d' % (url, cnt) for url, cnt in urls_failed_info.items() ]
    #logging.info('failed-pic-url:%s ' % '\n'.join(detail))
    task_col = Collection(self.mongo_task, task_mq_name)
    #task_col.insert_many([{'url':url, 'failed_cnt':failed_cnt} for url, failed_cnt in urls_failed_info.items()])
    for url,item in urls_failed_info.items():
      fail_item = {'url':url,'in_time':item.get('in_time',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) , 'failed_cnt':item.get('failed_cnt',0) , 'update_time':item.get('update_time',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
      task_col.insert(fail_item)
      logging.info('重入队列图片链接:%s' % fail_item.get('url')) 

  #获得抓取任务 返回图片url列表和每个url的下载情况
  def get_task_imgs(self, topic, maxrequest = 1000, max_cnt_failed = 100):
    task_col = Collection(self.mongo_task, topic)
    tasks = []
    task_info = {}
    for i in range(maxrequest):
      item = task_col.find_one_and_delete({})
      if item is None:
        break
      if 'player.youku.com' in item['url'] or item['url'][:7] not in ['http://','https:/']:
        continue
      #死链逻辑
      if item.get('failed_cnt', 0 ) >= max_cnt_failed:
        logging.info("图片死链:%d   %s" % (item.get('failed_cnt', 0), item.get('url', '')) )
        self.mongo_db.pic_bad_link.update({'url':item.get('url','')},{'failed_cnt':item.get('failed_cnt', 0), 'url':item.get('url', '')},True)
        logging.info("图片死链，已经进入到死链表中。以后不再抓取.URL:%s" % item.get('url', ''))
        continue
      tasks.append(item['url'])
      if 'in_time' not in item:
        logging.info("图片任务无in_time  img-url:%s" % item['url'])
      task_info[item['url']] = {'failed_cnt':item.get('failed_cnt', 0),'in_time':item.get('in_time',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
    logging.info("加载图片下载任务数:%d task-name:%s " % (len(tasks), topic))
    return tasks, task_info

  #去数据库（mongo）查询到所有待解析的page
  def get_allpage_forparse(self, where):
    if url != None:
      where['ur'] = url
    cursor = self.mongo_page_col.find(where)
    for page_item in cursor:
      logging.debug('get page_item:%s' % page_item)
      yield page_item

  #统一保存item
  def update_item(self, col_name, where, item):
    item_col = Collection(self.mongo_db, col_name)
    item_col.update(where, item, True)
    logging.debug("更新item. where:%s" % where)
    #给where中的字段建索引
    col_name = '%s_%s' % (col_name, ''.join(where.keys()))
    if col_name not in self.cols_hasindex:
      idxes = ([(key, ASCENDING) for key in where.keys()])
      #print 'indexes:', idxes
      index = IndexModel(idxes)
      item_col.create_indexes([index])
      self.cols_hasindex.add(col_name)
    else:
      pass
      #print 'colname:%s has idx' % col_name

  #获得抓取任务
  def get_task(self, topic, maxrequest = 1000, max_cnt_failed = 50):
    #死链collection
    task_col = Collection(self.mongo_task, topic)
    tasks = []
    for i in range(maxrequest):
      item = task_col.find_one_and_delete({})
      if item is None:
        break
      #死链逻辑
      if item.get('failed_cnt', 0 ) >= max_cnt_failed:
        logging.info("任务死链:%d   %s" % (item.get('failed_cnt', 0), item.get('url', '')) )
        self.mongo_dead_col.insert(item)
        continue
      if '_id' in item: del item['_id']
      tasks.append(item)
    logging.info("load tasks:%d maxrequest:%d from mqname:[%s] host:[%s] port[%s] db-name:[%s]" % (len(tasks), maxrequest, topic, settings.MONGO_TASK_HOST, settings.MONGO_PORT, settings.MONGO_TASK_DB_NAME))
    return tasks

  #获得待处理的query数量
  def get_query_num(self, col_query_name):
    col_query = Collection(self.mongo_task, col_query_name)
    num = col_query.count()
    return num

  #获得待处理的query列表
  def get_query(self, col_query_name, maxrequest = 1000, max_cnt_failed = 50):
    col_query = Collection(self.mongo_task, col_query_name)
    queryinfos = []
    for i in range(maxrequest):
      item = col_query.find_one_and_delete({})
      if item is None:
        break
      if '_id' in item: del item['_id']
      queryinfos.append(item)
    logging.info('加载query-[%s]数量:%d' % (col_query_name, len(queryinfos)))
    return queryinfos

  #保存db到mongo中
  def save_page(self, page_item, page_body, drop_page = False):
    if drop_page:
      return []
    page_item['update_time'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
      #self.mongo_page_col.insert(page_item)
      #page_item['page'] = snappy.compress(page_item['page'])
      self.lock_savepage.acquire()
      filename, relative_filename = self.get_page_filename(page_item['spider_name'], page_item['url'])
      logging.info('url[%s] get filename[%s] relative_filename[%s]' % (page_item['url'], filename, relative_filename))
      page_item['filename'] = relative_filename
      with open(filename, 'w') as fin:
        fin.write(page_body)
      self.lock_savepage.release()
      self.mongo_page_col.update({'url':page_item['url']}, {"$set":page_item}, True)
    except Exception, e:
      logging.warning("insert failed: url:%s  exception:%s" % (page_item['url'], e))
      pass

  # 得到网页保存路径
  def get_page_filename(self, spider_name, url):
    if len(url) < 1:
      logging.warning('getPagePath failed! because url in NULL')
      return None,None
    cur_time = datetime.datetime.now()
    day = cur_time.strftime('%Y_%m_%d')
    hour = cur_time.hour
    minute = cur_time.minute
    now = cur_time.strftime('%Y_%m_%d_%H_%M')
    #准备目录
    if now != self.last_save_time:
      new_path = "%s/%s/%s/%s/" % (settings.PAGE_PATH, day, hour, minute)
      try:
        os.makedirs(new_path)
      except Exception,e:
        logging.warning("mkdir exception. path[%s] exception:%s" % (new_path, e))
      self.last_save_time = now 
    url_md5 = hashlib.md5(url).hexdigest()
    filename = "%s/%s/%s/%s/%s_%s.html" % (settings.PAGE_PATH, day, hour, minute, spider_name, url_md5)
    relative_filename = "%s/%s/%s/%s_%s.html" % (day, hour, minute, spider_name, url_md5)
    return (filename, relative_filename)

  #判断是否在linkbase中，如果不在（新链接）则写入linkbase中并写入kafuka的不同主题队列中
  #linkinfo:from_url, url, spider_name, item_type, status, schedule_cnt, failed_cnt, in_time, update_time 作为一个json保存在SSDB的value中 key是url
  #def save_links(self, linkinfos = [], from_url = '', topic = '', need_filter = False):
  def save_links(self, linkinfos = [], from_url = '', topic = '', need_filter = True):
    task_col = Collection(self.mongo_task, topic)
    #need_filter：默认是都要经过linkbase过滤的。但百度爬虫部分流程可能不需要。此时需要标识出链接重复与否
    if need_filter:
      new_linkinfos = [linkinfo for linkinfo in linkinfos if not self.linkbase.exists(linkinfo["url"])]
    else:
      new_linkinfos = []
      for linkinfo in linkinfos:
        if self.linkbase.exists(linkinfo["url"]):
          linkinfo['dup'] = True
          logging.debug('重复但仍要执行抓取的链接:%s' % linkinfo['url'])
        new_linkinfos.append(linkinfo)

    logging.info('new_linkinfos[%d] ori_linkinfos[%d] fromurl:%s' % (len(new_linkinfos),len(linkinfos),from_url))
    #发送到kafka后，保存如linkbase
    messages = []
    for linkinfo in new_linkinfos:
      #检查必须字段
      if 'from_url' not in linkinfo or 'url' not in linkinfo or 'spider_name' not in linkinfo:
        logging.warning('bad linkinfo:%s' % json.dumps(linkinfo, ensure_ascii = False, encoding = 'utf-8'))
        continue
      task_col.insert(linkinfo)
      try:
        del linkinfo['_id']
      except:
        pass
      linkinfo_str = json.dumps(linkinfo, ensure_ascii = False, encoding = 'utf-8')
      #logging.debug('topic:%s linkinfo_str:%s' % (topic, linkinfo_str))
      messages.append(linkinfo_str)
      key = linkinfo['url']
      self.linkbase.set(key, linkinfo_str)
      self.mongo_db.linkbase.update({'url':key}, linkinfo, True)
      logging.debug('保存到linkbase: %s' % key)
  
  #保存到linkbase中。使用场景是：百度等搜索引擎爬虫的抓取结果存在302跳转，初始是百度加密链接，跳转后的连接也需要加入linkbase中，避免下一次的重复抓取
  def save_2_linkbase(self, linkinfo):
    if '_id' in linkinfo:
      del linkinfo['_id']
    key = linkinfo['url']
    linkinfo_str = json.dumps(linkinfo, ensure_ascii = False, encoding = 'utf-8')
    self.linkbase.set(key, linkinfo_str)
    self.mongo_db.linkbase.update({'url':key}, linkinfo, True)

  #重新发送linkinfo到kafka 在下载失败时 在download-retry的时候调用（确认retry已经超过了最大次数时，放弃下载了）
  #应该从linkbase中取得linkinfo（通过url、spider_name） 以便是kafka的link状态和linkbase同步 目前scheduler_cnt和failed_cnt是以linkbase为准
  def send_linkinfo_2_kafka(self, linkinfo, topic):
    linkinfo = self.update_schedule_time(linkinfo.get('spider_name', ''), linkinfo['url'])
    if linkinfo == None: return
    logging.debug('发送会下载队列. now scheduler-cnt[%d] failed-cnt[%d] url:%s' % (linkinfo['schedule_cnt'], linkinfo['failed_cnt'], linkinfo['url']))
    #调度次数或下载次数太多 则认为可能是死链 不在进行调度了
    if int(linkinfo['schedule_cnt']) > self.max_schedule_cnt or int(linkinfo['failed_cnt']) > self.max_failed_cnt:
      logging.warning('失败次数太多被判断为死链 url:%s' % linkinfo['url'])
      return
    if self.link_producer == None:
      self.link_producer = self.kafka.topics[topic].get_producer()
      self.last_topic = topic
    elif topic != self.last_topic:
      self.link_producer = self.kafka.topics[topic].get_producer()
      logging.warning("topic update from[%s] to [%s]" % (topic, self.last_topic))
      self.last_topic = topic
    message = json.dumps(linkinfo, ensure_ascii = False, encoding = 'utf-8')
    ret = self.link_producer.produce([message])
    logging.debug("save to kafka suc! ret:%s" % ret)

  #重新发送linkinfo到mongo 在下载失败时 在download-retry的时候调用（确认retry已经超过了最大次数时，放弃下载了）
  #应该从linkbase中取得linkinfo（通过url、spider_name） 以便是mongo 任务的link状态和linkbase同步 目前scheduler_cnt和failed_cnt是以linkbase为准
  def send_linkinfo_back2_taskqueue(self, linkinfo, topic, status = None, url_resp = None):
    #判断是否用跳转后的链接更新linkinfo里的url。在百度抓取过程中链接会重定向到真实链接，并对真实链接进行调度下载，真实链接下载失败回队列重试时应该用真是队列而非原始百度加密链接，避免重复跳转破解工作
    linkinfo = self.update_schedule_time(linkinfo['spider_name'], linkinfo['url'], org_item = linkinfo)
    if status is not None and url_resp is not None:
      domain_org = self.get_mdomain_from_url(linkinfo.get('url', ''))
      domain_jump = self.get_mdomain_from_url(url_resp)
      logging.debug("尝试更新linkinfo-url。domain_org:%s domain_jump:%s" % (domain_org, domain_jump))
      if domain_org == 'baidu.com' and domain_org != domain_jump:
        logging.info("破解百度链接，重入队列时更新url。org:[%s] new:[%s]" % (linkinfo.get('url', ''), url_resp))
        linkinfo['url'] = url_resp
    if linkinfo == None: 
      logging.info('发送回消息队列时，因linkinfo为None，忽略')
      return
    logging.debug('发送回消息队列. now scheduler-cnt[%d] failed-cnt[%d] url:%s' % (linkinfo.get('schedule_cnt', 0), linkinfo['failed_cnt'], linkinfo['url']))
    #调度次数或下载次数太多 则认为可能是死链 不在进行调度了
    if int(linkinfo.get('schedule_cnt', 0)) > self.max_schedule_cnt or int(linkinfo['failed_cnt']) > self.max_failed_cnt:
      logging.warning('调度次数或下载次数太多 url:%s' % linkinfo['url'])
      return
    task_col = Collection(self.mongo_task, topic) 
    task_col.insert(linkinfo)

  #从url中取出主域名
  def get_mdomain_from_url(self, url):
    domain = urlparse.urlparse(url).netloc
    parts = domain.split(".")
    if len(parts) == 3:
      return '.'.join(parts[-2:])
    elif len(parts) > 3:
      if 'com.cn' in domain or 'net.cn' in domain:
        return '.'.join(parts[-3:])
      else:
        return '.'.join(parts[-2:])
    else:
      return ''

  #downloader中间件更新link的下载状态（成功，或失败次数+1，更新到linkbase中）
  def update_link_status(self, spider_name, url, status):
    key = url
    link_info = self.linkbase.get(key)
    #logging.debug('get link_info from linkbase:%s' % link_info)
    if link_info == None or link_info == "":
      logging.warning('update_link_status failed for url not exist! key:%s' % key)
      return False
    else:
      item = json.loads(link_info)
      item['status'] = status
      if 400 <= status < 600:
        item['failed_cnt'] = item.get('failed_cnt', 0) + 1
      self.linkbase.set(key, json.dumps(item, ensure_ascii = False, encoding = 'utf-8'))
      try:
        #self.linkbase_mongo.update({'url':key}, item, True)
        self.mongo_db.linkbase.update({'url':key}, item, True)
      except Exception,e:
        logging.warning('update_link_status in mongo-linkbase failed key:%s item:%s' % (key, json.dumps(item, ensure_ascii = False, encoding = 'utf-8') ) )
        logging.warning('exp-into:%s' % e)
      logging.info('update_link_status suc. key:%s' % key)
      return True

  #url被调度一次，就+1 维护url被调度的次数
  #废掉
  def update_schedule_time(self, spider_name, url, org_item):
    key = url
    link_info = self.linkbase.get(key)
    if link_info == None or link_info == "":
      return org_item
    else:
      item = json.loads(link_info)
      #item['schedule_cnt'] = int(item['schedule_cnt']) + 1
      #self.linkbase.set(key, json.dumps(item, ensure_ascii = False, encoding = 'utf-8'))
      #self.linkbase_mongo.update({'url':key}, item, True)
      #self.mongo_db.linkbase.update({'url':key}, item, True)
      #logging.debug('update_link_status suc. key:%s scheduler_cnt:%s' % (key, item['schedule_cnt']))
      return item

  #从文件中导入代理列表
  def import_proxy(self, file_in):
    fin = open(file_in)
    for line in fin:
      (proxy, value) = line.strip().split('\t')
      self.proxy.set(proxy, int(value))
    fin.close()

  #一次性从代理库中取出一批代理
  #代理的综合失败次数要小于阀值
  #代理库中加载出来的key的形式：scheme://xx.xx.xx:port
  #http和https协议各一半
  def get_proxy(self, scheme = 'http', limit = 10000, min_live = 3000, max_ftime = 100):
    items = self.proxy.scan(scheme, '', limit)
    proxy_list_kv = [(k,v) for k,v in items.items()]
    if len(proxy_list_kv) <= 100:
      logging.warning('代理库中的代理数量少于100:%d' % len(proxy_list_kv))
    #按照失败次数排序，使失败次数最大的排在最前面
    proxy_list_sortedkv = sorted(proxy_list_kv, key = lambda x: int(x[-1]))
    proxy_list = [k for (k,v) in proxy_list_sortedkv[: min_live * 2]]
    return proxy_list

  #更新代理 失败则value+1 成功则-1
  def update_proxy(self, proxy = "http://xx.xx.xx.xx:1234", flag = 1, need_add_when_notexists = False):
    cnt = self.proxy.get(proxy)
    if cnt == None or cnt == "":
      #logging.info('proxy not exist! proxy:%s' % proxy)
      if need_add_when_notexists:
        self.proxy.set(proxy, 0)
      return 
    #最大有效性不超过不超过-100
    value = -100 if int(cnt)+flag < -100 else int(cnt)+flag
    logging.debug('反馈代理状态[%s] 失败数 %d to %d ' % (proxy, int(cnt), value))
    self.proxy.set(proxy, value)

  def find_one_item(self, col_name, where):
    item_col = Collection(self.mongo_db, col_name) 
    old_item = item_col.find_one(where)
    return old_item


  #获取一个之前准备好的cookie
  def get_cookie(self):
    cursor = self.mongo_db.cookies.find()
    cookies = []
    for cookie in cursor:
      del cookie['_id']
      del cookie['username']
      cookies.append(cookie)
    cookie = random.choice(cookies)
    return cookie

  #获取 代理
  def get_proxy_one(self):
    ip = self.proxy.get('video_proxy_ip_che300')
    proxy = 'https://%s:8888' % ip
    return proxy

  def send_pic_task(self,item):
    content=item.get('content',None)
    if isinstance(content,list):
      nowdate=datetime.datetime.now().strftime('%Y-%m-%d %h:%M:%s')
      tasks=[]
      for cont in content:
        if cont.get('tp','')=='img':
          if len(cont['ct'])<4:
            continue
          picinfo={'url':cont['ct'],'update_time':nowdate,'in_time':nowdate,'failed_cnt':0}
          #self.mongo_pictask.insert(picinfo)
          tasks.append(picinfo)
      self.mongo_pictask.insert_many(tasks)
    else:
      logging.info('item is not list... ...')

  def save_new_yinguoshu(self,url):
    self.mongo_db.linkbase_yinguoshu.insert({'url':url})
    self.mongo_task.yinguoshu.insert({'url':url})

  def save_yinguoshu(self,item):
    self.mongo_db.yinguoshu_item.update({'cid':item['cid']},item,True)

  def load_yinguoshu_task(self,spider_name):
    col = self.mongo_task[spider_name]
    url = col.find_one_and_delete({})
    return url.get('url','')

facade = Facade()
#facade.get_proxy_one()
