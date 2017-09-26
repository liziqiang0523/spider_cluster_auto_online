#!/usr/bin/python
#coding=utf-8
#author:auto_maker

from oreo.spiders.basesite import BasesiteSpider
from oreo.parser.liziqiang_spider_query_197 import Parserquery_spider_baidu399

class Luntan(BasesiteSpider):
  name = 'liziqiang_spider_query_197'
  start_urls = [
    #'http://s.tool.chinaz.com/baidu/words.aspx?kw=%E5%A4%B4%E7%96%BC&page=&by=0&pn='
  ]
  parsers = [Parserquery_spider_baidu399(),]
  xTargets = [ 
    {"xpath":"/sdfsdf","allow":(),"deny":(),"itemtype":"auto_item"},
  ]
