#/usr/local/bin/python2.7
#coding=utf-8
#author:liziqiang

'''
去MySQL中获取爬虫的必要字段。然后组装成spider和paser文件并放到相应位置。然后执行。
1、生成程序
2、放到相应目录
3、执行程序：scrapy crwal spider_name
'''
import os,sys,time,json,re
import MySQLdb as mysqldb
from pymongo import MongoClient
from pymongo.collection import Collection
import urlparse
from datetime import datetime
import tornado.ioloop
import tornado.web
from tornado import httpserver
import traceback

class Process:
  def __init__(self):
    self.con = mysqldb.connect(host = '', port = 3306, user = '', passwd = '', db = 'ab', charset='utf8')
    self.cursor = self.con.cursor() 

  def __del__(self):
    self.cursor.close()
    self.con.close()

  def spider_maker(self,taskid=3):
    sql = 'select admin_name,spider_name,start_url,xpath from spider_task where taskid=%d' % taskid
    self.cursor.execute(sql)
    rows = self.cursor.fetchone()
    (admin_name,spider_name,start_url,xpath) = rows
    real_spider_name = '%s_%s_%d' % (admin_name,spider_name,taskid)
    spider_file = '/data/spider_cluster_auto_test/oreo/oreo/spiders/%s.py' % real_spider_name
    file_spider = open(spider_file,'w')
    file_spider.write('#!/usr/bin/python\n#coding=utf-8\n#author:auto_maker\n\nfrom oreo.spiders.basesite import BasesiteSpider\n')
    self.cursor.execute('select table_name from spider_paser where taskid=%d' % taskid)
    parsers = self.cursor.fetchall()
    parser_list = []
    for name in parsers:
      parser_name = 'Parser%s' % name
      parser_list.append(parser_name)
      file_spider.write('from oreo.parser.%s import %s\n' % (real_spider_name,parser_name))
    file_spider.write('\nclass Luntan(BasesiteSpider):\n\tmax_request_num = 0\n')
    #file_spider.write('\tallowed_domain = []\n')
    file_spider.write("\tname = '%s'\n\tstart_urls = ['%s']\n" % (real_spider_name,start_url))
    file_spider.write('\tparsers = [' % parser_list)
    for parser in parser_list:
      file_spider.write('%s(),' % parser)
    file_spider.write(']\n')
    file_spider.write('\txTargets = [ \n')
    xpath = json.loads(xpath)
    for item in xpath:
      file_spider.write('\t\t{"xpath":"%s","allow":(%s),"deny":(%s),"itemtype":"auto_item"},\n' % (item['xpath'],item['allow'],item['deny']))
    file_spider.write('\t]')
    return True,real_spider_name

  def parser_maker(self,taskid=3):
    sql = 'select admin_name,spider_name from spider_task where taskid=%d' % taskid
    self.cursor.execute(sql)
    rows = self.cursor.fetchone()
    (admin_name,spider_name) = rows
    real_spider_name = '%s_%s_%d' % (admin_name,spider_name,taskid)
    parser_file = '/data/spider_cluster_auto_test/oreo/oreo/parser/%s.py' % real_spider_name
    file_parser = open(parser_file,'w')
    file_parser.write('#!/usr/bin/python\n#coding=utf-8\n#author:auto_maker\n\nimport sys\nfrom baseparser import BaseParser\n\n')
    self.cursor.execute('select id,table_name,block_xpath,must_keys,replace_keys,pub_kv_rules,block_kv_rules,pub_from_other from spider_paser where taskid=%d' % taskid)
    parsers = self.cursor.fetchall()
    for pid,table_name,block_xpath,must_keys,replace_keys,pub_kv_rules,block_kv_rules,pub_from_other in parsers:
      #print pid,table_name,block_xpath,must_keys,replace_keys,pub_kv_rules,block_kv_rules,pub_from_other
      parser_name = 'Parser%s' % table_name
      file_parser.write('class %s(BaseParser):\n' % parser_name)
      file_parser.write('\tspider_name = "%s"\n' % real_spider_name)
      file_parser.write('\titem_type = "%s"\n' % table_name)
      file_parser.write('\ttable_name = "%s"\n' % table_name)
      file_parser.write('\tmulti_block_rules =[\n')
      file_parser.write('\t\t{\n')
      file_parser.write('\t\t\t"pub_kv_rules":[\n')
      pub_rules = json.loads(pub_kv_rules)
      for item in pub_rules:
        file_parser.write('\t\t\t\t{"name":"%s","xpath":"%s","regex":u"%s"},\n' % (item['pub_name'],item['pub_xpath'],item['pub_regx']))
      try:
        pub_from_other = json.loads(pub_from_other)
      except:
        pub_from_other = []
      for item in pub_from_other:
        file_parser.write('\t\t\t\t{"name":"%s","from_other","url","regex":u"%s"},\n')
      file_parser.write('\t\t\t\t],\n')
      file_parser.write('\t\t\t"xpath":"%s",\n' % block_xpath)
      file_parser.write('\t\t\t"rules":[\n')
      block_rules = json.loads(block_kv_rules)
      for item in block_rules:
        print item
        file_parser.write('\t\t\t\t{"name":"%s","xpath":".%s","regex":u"%s"},\n' % (item['blk_name'],item['blk_xpath'],item['blk_regx']))
      file_parser.write('\t\t\t\t]\n')
      file_parser.write('\t\t\t},\n')
      file_parser.write('\t]\n')
      must_keys = must_keys.split(',')
      m_key = ''
      for must_key in must_keys:
        m_key = m_key +  '"%s",' % must_key 
      file_parser.write('\tmust_keys = [%s]\n' % m_key[:-1])
      replace_key = ''
      replace_keys = replace_keys.split(',')
      for r_key in replace_keys:
        replace_key = replace_key + '"%s",' % r_key
      file_parser.write('\treplace_keys = [%s]\n' % replace_key[:-1])
      print '%s maked ok ' % parser_name
      return True

class SpiderServer(tornado.web.RequestHandler):
  def get(self):
    response = {}
    qid = self.get_argument('id')
    pro = Process()
    parser_status = pro.parser_maker(int(qid))
    (spider_status,spider_name) = pro.spider_maker(int(qid))
    if parser_status and spider_status:
      response['code'] = 200
    else:
      response['code'] = 400
    json_response = json.dumps(response, ensure_ascii=False)
    cmd = 'cd /data/spider_cluster_auto_test/oreo/ && scrapy crawl %s' % spider_name
    os.system(cmd)    
    self.write(json_response)

    
if __name__ == "__main__":
  processor = Process()
  processor.parser_maker(2)
  processor.spider_maker(2)
  print 'ok'

