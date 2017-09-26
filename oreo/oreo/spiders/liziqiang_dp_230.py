#!/usr/bin/python
#coding=utf-8
#author:liziqiang

from oreo.spiders.basesite import BasesiteSpider
from oreo.parser.liziqiang_dp_230 import Parserstore_dzdp448
from oreo.parser.liziqiang_dp_230 import Parserdianping_shop_list449
from oreo.parser.liziqiang_dp_230 import Parserstore_dzdp_empty450

class MySpider(BasesiteSpider):
  name = 'liziqiang_dp_230'
  #max_request_num = 100
  start_urls = [
    #{'url':'http://www.dianping.com/search/category/2/10/g508','link_types':['list_url']},
    ]
  parsers = [Parserstore_dzdp448(),Parserdianping_shop_list449(),Parserstore_dzdp_empty450(),]
  xTargets = { 
    'list_url':[
      {"xpath":"//div[@class='tit']/a[1]","allow":(),"deny":(),"link_types":["item_url"]},
      {"xpath":"//div[@class='page']//a","allow":(),"deny":(),"link_types":["list_url"]},
      ]
  }
