#!/usr/bin/python
#coding=utf-8
#author:auto_maker

from oreo.spiders.basesite import BasesiteSpider
from oreo.parser.liziqiang_yinguoshu_touzi_205 import Parseryinguoshu_touzi413

class Luntan(BasesiteSpider):
  name = 'liziqiang_yinguoshu_touzi_205'
  start_urls = ['https://www.innotree.cn/company/975329.html']
  parsers = [Parseryinguoshu_touzi413(),]
  xTargets = [ 
    {"xpath":"/sdfs","allow":(),"deny":(),"itemtype":"auto_item"},
  ]