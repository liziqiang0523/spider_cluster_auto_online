#!/usr/bin/python
#coding=utf-8
#author:auto_maker

from oreo.spiders.basesite import BasesiteSpider
from oreo.parser.liziqiang_cn2che_225 import Parsercn2che_item442

class Luntan(BasesiteSpider):
  name = 'liziqiang_cn2che_225'
  start_urls = [
    'http://www.cn2che.com/buycar/c1b0c0s0p0c0m0p1c0r0m1i0o0o2',
    'http://www.cn2che.com/buycar/c2b0c0s0p0c0m0p1c0r0m1i0o0o2',
    'http://www.cn2che.com/buycar/c3b0c0s0p0c0m0p1c0r0m1i0o0o2',
    'http://www.cn2che.com/buycar/c4b0c0s0p0c0m0p1c0r0m1i0o0o2',
    'http://www.cn2che.com/buycar/c8b0c0s0p0c0m0p1c0r0m1i0o0o2',
    'http://www.cn2che.com/buycar/c12b0c0s0p0c0m0p1c0r0m1i0o0o2',
    ]
  parsers = [Parsercn2che_item442(),]
  xTargets = [ 
    {"xpath":"//div[@class='cheyuan buycheyuan']//ul/li//dl//dt/a","allow":(),"deny":(),"itemtype":"auto_item"},
    {"xpath":"//div[@class='NewPage']//a","allow":(),"deny":(),"itemtype":"auto_item"},
  ]
