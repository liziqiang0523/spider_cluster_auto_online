#!/usr/bin/python
#coding=utf-8
#author:auto_maker

from oreo.spiders.basesite import BasesiteSpider
from oreo.parser.liziqiang_cn2che_225 import Parsercn2che_item442

class Luntan(BasesiteSpider):
  name = 'test_spider'
  max_request_num = 1
  start_urls = [
    #{'url':'http://www.cn2che.com/buycar/c12b0c0s0p0c0m0p1c0r0m1i0o0o2','link_type':'list_url','parser_ranks':[]},
    ]
  parsers = [Parsercn2che_item442(),]
  xTargets =  {
   'list_url': [
      {"xpath":"//div[@class='cheyuan buycheyuan']//ul/li//dl//dt/a","allow":(),"deny":(),"parser_ranks":[1],'link_type':'item_url'},
      {"xpath":"//div[@class='NewPage']//a","allow":(),"deny":(),"parser_ranks":[],'link_type':'list_url'}
      
      ]
  }
