#!/usr/bin/python
#coding=utf-8
#author:auto_maker

from oreo.spiders.basesite import BasesiteSpider
from oreo.parser.liziqiang_xiaozhu_221 import Parserxiaozhu_city436
from oreo.parser.liziqiang_xiaozhu_221 import Parserxiaozhu_item437

class Luntan(BasesiteSpider):
  max_request_num = 8
  name = 'liziqiang_xiaozhu_221'
  start_urls = [
    #'http://www.xiaozhu2.com/car/999bccf9534ff968ae5b.html'
  ]
  parsers = [Parserxiaozhu_city436(),Parserxiaozhu_item437(),]
  xTargets = [ 
    {"xpath":"//div[@class='caritem-thumb']/a","allow":(),"deny":(),"itemtype":"auto_item"},
    {"xpath":"//div[@class='esc-buycar-pagination']//a","allow":(),"deny":(),"itemtype":"auto_item"},
    {"xpath":"//div[@class='all-brand-bd']//a","allow":(),"deny":(),"itemtype":"auto_item"},
    {"xpath":"//div[@class='esc-tab']/a[3]","allow":(),"deny":(),"itemtype":"auto_item"},
  ]
