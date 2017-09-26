#!/usr/bin/python
#coding=utf-8
#author:shiyuming.shi@gmail.com
'''
  这次重构，最主要的一点是把瑞士军刀的大函数拆解为多个功能较为单一的成员函数
  主函数重点是突出流程，成员函数封装业务细节，主次有别，利于程序的生长健壮，
  也增强代码的可阅读性
  还有一个不大和谐的地方是：之前我主要用骆驼命名规范，现在转为C++风格，只类名继续用骆驼。但没有转换完全，之前的命名没有全部改过来。
'''

import os, sys, re, hashlib, traceback, logging, datetime, time
from pymongo import MongoClient
from pymongo.collection import Collection
from bson.objectid import ObjectId
from lonlat import lonlat
from extractText import getText
from scrapy.http import TextResponse
from scrapy.selector import Selector
from extractText import doExtract
from readability.bireadability import Document
from get_content_base_v1 import Element
from oreo.facade import facade

reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
import settings

class BaseParser(object):
  is_process=False
  is_list=False
  other_fromurl = 'from_url'
  #爬虫名
  spider_name = ""
  #item保存的数据表名
  table_name = ""
  #结构化解析规则全部在这，包括公共解析字段 支持在同一个页面解析出多种、多类型的item，并且支持为items解析公共字段
  multi_block_rules = []
  #对url类的字段，如果是相对路径则补齐为绝对路径
  url_format = []
  url_prefix = ''
  #need_enter,需要特殊处理的rule['name']
  need_enter = []
  #换行最小字数要求 避免换行太频繁 
  min_section_num = 5
  #非空字段列表 如果解析不出这些字段（如为空）则判断item解析失败，警告并丢弃该item
  must_keys = []
  #更新替换item的依据：如果replace_keys一致，则认为两个item重复，将用新的item覆盖旧item。注意，是覆盖
  replace_keys = []
  #本解析器支持的定向解析domain，目前只用于搜索引擎的在线解析支持，其他地方暂时未用到，所有本字段为空则不作为过滤，否则必须要求待解析的item的url，domain必须在allowed_domain中，这和爬虫的这个字段效果相同
  allowed_domain = []
  #是否自动识别并抽取网页中的正文。默认是开启，如果识别到网页中存在主体文本块，则抽取title，时间，主文本内容（含图片），保存到同一个的artical_raw表中
  #文本识别比较慢，处理一个网页时需要几百毫秒，所有对大规模非文章咨询类的抓取，要在子类parser里关掉
  is_auto_extract_artical = False

  def __init__(self, is_auto_extract_artical = False):
    #解析结果
    self.is_auto_extract_artical = is_auto_extract_artical

  #离线解析入口函数
  #从mongo-page加载指定爬虫、指定类型的page-info，并从文件系统中加载page-body，使用scrapy的框架api，按照解析规则进行解析
  #update_time只需要提供天就行了
  def parse(self, update_time = '2015-08-17', url = None):
    time_begin = time.time()
    logging.basicConfig(level = logging.INFO, 
      format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', 
      datefmt = '%a, %d %b %Y %H:%M:%S',
      filename = '%s/%s_%s_%s.log' % (settings.LOG_PATH, self.spider_name, self.table_name, update_time.replace(':', '_')),
      filemode = 'w')
    print 'logfile:%s/%s_%s_%s.log' % (settings.LOG_PATH, self.spider_name, self.table_name, update_time.replace(':', '_'))
    #统计信息
    (cnt, cnt_suc, cnt_failed) = (0,0,0)
    #查找数据库
    where = {'spider_name' : self.spider_name, 'update_time':{'$regex':'%s.*' % update_time}}  
    if url != None: where['url'] = url
    logging.debug("parse find from db. where:%s" % where)
    #可能会失败，因parse
    #cursor = self.page_col.find(where)
    cursor = facade.get_allpage_forparse(where)
    for page_item in cursor:
      url = page_item['url']
      cnt += 1
      logging.debug('process item at[%d] parse_suc[%d] parse_failed[%d]' % (cnt, cnt_suc, cnt_failed))
      try:
        items = self.process_page(page_item)
      except Exception, e:
        cnt_failed += 1
        logging.error('parse occure Exception.msg:%s  url:%s' % (e, url))
        traceback.print_exc()
    time_end = time.time()
    logging.info('parse all Done. all_page num[%d] parse_suc[%d] parse_failed[%d] cost-time:[%d] seconds. speed[%0.1f]' % (cnt, cnt_suc, cnt_failed, time_end-time_begin, cnt/(time_end-time_begin)))

  #保存item到数据库的相应item表中
  def save_item(self, item):
    #where不能是None，不能是空（空则是所有进行更新），没有必要更新的都用id来做
    where = {}
    print item['from_url']
    print '**********************'
    for key in self.replace_keys:
      where[key] = item[key]
      if len(where) == 0:
        where["_id"] = ObjectId('123456789012')
        logging.error('get_update_where error! 没有配置replace_keys或replace_key不是must_keys')
    print where  
    #old_item = self.item_col.find_one(where)
    old_item = facade.find_one_item(self.table_name, where)
    if old_item is None:
      item['first_crawl_time'] = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
      if 'selled' in item:
        item['sell_time'] = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
    else:
      item['first_crawl_time'] = old_item['first_crawl_time'] if 'first_crawl_time' in old_item else old_item['frist_crawl_time']
      if 'selled' in item and 'sell_time' not in old_item:
        item['sell_time'] = item['crawl_time']
      if 'selled' in item and 'sell_time' in old_item:
        item['sell_time'] = old_item['sell_time']
    
    logging.debug('保存解析item. from url:%s get where for a item:%s' % (item['from_url'], where))
    #self.item_col.update(where, item, True)
    facade.update_item(self.table_name, where, item)
    
  def drop_item(self, url):
    #如果规则里面有dorp_item且不为空，说明item已经没用。需要删除,更新item状态添加字段drop_item:yes。
    car_id = re.findall(r'infoid=(\d+)',url)[0]
    where = {'car_id':car_id}
    #old_item = self.item_col.find(where)
    old_item = facade.find_one_item(self.table_name, where)
    for item in old_item:
      item['drop_item'] = 'yes'
      item['crawl_time'] = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
      #self.item_col.update(where, item, True)
      facade.update_item(self.table_name, where, item)
      
  #解析一个网页 返回解析结果(item-list)
  def process_page(self, page_item, html_body = None, page_url = ''):
    logging.debug('解析结果存放表:[%s]' % self.table_name)
    items = []
    domain = page_url.split('//')[-1].split('/')[0]
    if len(self.allowed_domain) > 0 and domain not in self.allowed_domain:
      logging.debug('parser domain not match. parser-tab-name[%s] domain[%s]' % (self.table_name, domain))
      return items
    html_body = page_item['html_body']
    html_body = html_body.replace('#src','src_real')
    if html_body == None:
      #从filesys中提取文件（htmlbody） 文件不一定存储在当前机器节点
      filename = "%s/%s" % (settings.PAGE_PATH, page_item['filename'])
      if not os.path.exists(filename):
        parts = filename.split("/")
        filename  = '%s/%s_%s' % ('/'.join(parts[:-1]), page_item['spider_name'], parts[-1])
        logging.debug('new filename:%s' % filename)
        if not os.path.exists(filename):
          logging.info('html file is exists ! filename[%s] url=[%s]' % (filename, page_item['url']))
          return items
      with open(filename) as fin:
        html_body = fin.read()
    if len(html_body) < 20:
      logging.warning('html file is to little! filename[%s] url=[%s]' % (page_item['filename'], page_item['url']))
      return items
    else:
      #正文抽取
      #logging.info(html_body)
      if self.is_auto_extract_artical and p_facade is not None:
        doc = Document(unicode(html_body).encode('utf-8'), encoding='utf-8')
        main_content = doc.summary()
        if len(main_content) > 20:
          logging.debug("extract main_content. len:%d" % len(main_content))
          item_article = {"title":doc.short_title(), "content":main_content, "from_url":page_item.get("url"), "spider_name":page_item.get("spider_name"), "pub_datetime":doc.post_time(), "crawl_datetime": datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%SZ") }
          facade.save_article_raw(item_article)
        else:
          logging.debug("extract main_content failed")

      #实例一个Response 进行规则结构化解析
      response = TextResponse(page_item['url'], body = html_body, encoding = 'utf-8')
      hxs = Selector(response)
      #遍历规则--block 一个网页有多个相同的item
      for block_rules in self.multi_block_rules:
        logging.debug('now the block_rules is:%s' % block_rules)
        #抽取公共kv对
        pub_kvs = self.process_rules(hxs, block_rules['pub_kv_rules'], page_item['url'])
        logging.debug('url:[%s] get pub_kvs:%s' % (page_item['url'], ' '.join(['%s:%s' % (k,v) for k,v in pub_kvs.items()])))
        #块解析--得到item所在的块列表blocks
        if 'xpath' not in block_rules:
          continue
        blocks = hxs.xpath(block_rules['xpath'])
        logging.debug('length of blocks[%d]' % len(blocks))
        #block-item挖取
        for block in blocks:
          #执行规则，挖出item
          item = self.process_rules(block, block_rules['rules'], page_item['url'])
          #加pub k-v对
          item.update(pub_kvs)
          #公共的默认字段
          item['crawl_time'] = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
          item['spider_name'] = page_item['spider_name']
          item['from_url'] = page_item['url']
          item['ref_url'] = page_item.get('ref_url', '')
          if page_item.get('query',None) is not None:
            item['query']=page_item['query']
          if self.is_list and 'content' in item:
            element=Element()
            item['content']=element.get_clean_list(item['content'])
          logging.debug('ref_url:%s from_url:%s' % (item['ref_url'], item['from_url']))
          if self.valid_by_mustkey(item, item['from_url']):
            items.append(item)
            self.process_content(item)

    logging.debug('item num:[%d]  list info--------------------------------------------------------------' % len(items))
    for item in items:
      logging.debug('解析出的完整item:\n  %s' % '  \n '.join(['%s:%s' % (k,v) for k,v in item.items()]))
      self.save_item(item)
    return items

  #执行解析规则，解析k-v对
  def process_rules(self, hxs, rules, url):
    #解析结果
    kvs = {}
    if len(rules) < 1:
      return kvs
    for rule in rules:
      #执行一个规则
      values = self.process_one_rule(hxs, rule, url)
      #滤掉空行 包括要过滤掉的行 及对指定字段的特别清理
      values = self.clean_extract_result(values, rule)
      if len(values) < 1: continue
      logging.debug('应用解析规则-[%s] result:%s' % (rule, ' '.join(values)))
      #提取的多个结果，只取第一个
      if 'only_one' in rule and rule['only_one'] and len(values) >= 1:
        logging.debug('rule has onlyone limit. values-ori[%s] rule-name[%s]' % (' '.join(values), rule['name']))
        values = values[:1]
      #对特别的结果话字段进行处理，如经纬度、imgurl、用换行符join， 加入kvs中
      self.process_special_kv(rule, values, kvs)
    return kvs

  #执行一个规则
  def process_one_rule(self, hxs, rule, url):
    values = []
    #从其他地方解析 比如目前支持的从url解析 从from解析
    if 'from_other' in rule:
      if rule['from_other'] == 'url':
        source = url
      else:
        logging.warning('从其他地方解析:目前支持的从url解析')
        return values
      if len(rule['regex']) < 1:
        logging.warning('从url等非页面源码中解析必须正则!')
        return values
      result = re.findall(rule['regex'], source)
      if len(result) > 0:
        for x in result:
          if '|' in rule['regex']:
            for y in x:
              if y != '':
                values.append(y)
          else:
            values.append(x)
        #values = result

    #只有xpath的情况
    elif len(rule['regex']) < 1 and len(rule['xpath']) > 1:
      values = hxs.xpath(rule['xpath']).extract()
      if len(values) < 1:
        logging.debug('解析[%s]失败. url[%s]' % (rule['name'], url))
    elif len(rule['regex']) > 1 and len(rule['xpath']) > 1:
      values = hxs.xpath(rule['xpath']).re(rule['regex'])
      if len(values) < 1:
        logging.debug('解析[%s]失败 url:[%s]' % (rule['name'], url))
    if rule['name'] == 'drop_item' and len(values) > 0:
      self.drop_item(url)
    return values

  #从html-body中抽取新链接，主要是处理api接口返回的url，对其中的部分url进行抓取，具体如何做是子类实现，基类只是一个兼容接口
  def extract_links(self, html_body, page_url):
    return []

  #滤掉空行 包括要过滤掉的行
  def clean_extract_result(self, values, rule):
    tmpvalues = []
    for p in values:
      p = p.replace('\r','').strip()
      if len(p) <= 0: continue
      #滤掉不需要抽出来的行
      if "drop_line" in rule and len(rule["drop_line"]) > 0:
        for drop in rule["drop_line"]:
          #p = p.replace(drop,'')
          if re.search(drop, p) != None:
            logging.debug('re matche dropline[%s],input[%s]' % (drop, p))
            continue
      tmpvalues.append(p)
    logging.debug('result clean:[%s]' % (' '.join(tmpvalues)))
    return tmpvalues

  #对特别的结果话字段进行处理，如经纬度、imgurl、用换行符join
  def process_special_kv(self, rule, values, kvs):
    if rule['name'] == 'lonlat':
      lonlattmp = lonlat()
      kvs['lat'], kvs['lng'] = lonlattmp.getlonlat(str(values[0]))
    #对url类的字段，如果是相对路径则补齐为绝对路径
    elif rule['name'] in self.url_format:
      new_links = []
      for p in values:
        #去掉非绝对路径的url
        if p[:7] == 'http://' or p[:8] == 'https://':
          new_links.append(p)
        else:
          new_links.append('%s/%s' % (self.url_prefix, p))
          logging.debug('补齐url字段[%s] name[%s]' % (p, rule['name']))
      if 'only_one' in rule and rule['only_one'] and len(new_links) >= 1:
        kvs[rule['name']] = new_links[0]
      else:
        kvs[rule['name']] = ' '.join(new_links)
    #需要用换行回车而不是空格来join抽取结果
    elif rule['name'] in self.need_enter:
      kvs[rule['name']] = 'spider_split'.join(values)
    else:
      kvs[rule['name']]=" ".join(values)
  
  def valid_by_mustkey(self, item, url):
    #判断item的必须字段是否为空
    for key in self.must_keys:
      if key not in item or len(item[key]) < 1:
        logging.warning('item缺少非空字段[%s] 丢弃. tab_name[%s] parser:[%s] url:%s' % (key, self.table_name, self.__class__, url))
        logging.debug('item当前的信息:\n%s' % ' \n '.join(['%s:%s' % (k,v) for k,v in item.items()]))
        return False
    return True

  def process_content(self,item):
    if not self.is_process:
      return
    try:
      facade.send_pic_task(item)
    except Exception,e:
      logging.error(e)
