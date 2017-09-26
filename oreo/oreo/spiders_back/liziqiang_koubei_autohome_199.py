#!/usr/bin/python
#coding=utf-8
#author:auto_maker

from oreo.spiders.basesite import BasesiteSpider
from oreo.parser.liziqiang_koubei_autohome_199 import Parserkoubei_autohome_from_list402

class Luntan(BasesiteSpider):
  name = 'liziqiang_koubei_autohome_199'
  max_request_num = 1
  not_request = ['summarykey=-1']
  start_urls = [
  #'http://k.autohome.com.cn/spec/19201/ge10/index_6.html?summarykey=1120629'
  ]
  parsers = [Parserkoubei_autohome_from_list402(),]
  xTargets = [ 
    {"xpath":"//div[@class='page-cont']//a","allow":('summarykey'),"deny":(),"itemtype":"auto_item"},
    {"xpath":"//div[@class='revision-impress ']//a","allow":(),"deny":(),"itemtype":"auto_item"},
  ]
