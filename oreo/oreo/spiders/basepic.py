# -*- coding: utf-8 -*-
#author:shiyuming,liziqiang
'''
图片现在基类
'''
import sys, traceback, logging, math, time, datetime
from oreo.spiders.basesite import BasesiteSpider
from scrapy.http import Request
from scrapy.spiders import CrawlSpider
from oreo.facade import facade
from oreo.items import DiorItem
from scrapy.loader import ItemLoader, Identity
from oreo import settings

class BasePicSpider(BasesiteSpider):
  name = "article_pic_new"
  max_request_num = settings.MAX_REQ_NUM
  start_urls = [
    'http://www.xin.com/beijing/'
    #'https://www.baidu.com/'
    #'http://news.xinmin.cn/'
    #'http://www.autohome.com.cn/news/'
     ]

  #初始进行调度 避免种子也被屏蔽而导致爬虫启动不起来
  def start_requests(self):
    #mid赋值
    self.mid = datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")
    for url in self.start_urls:
      yield Request(url, dont_filter=True, meta={'no_proxy':1})
    logging.info('mid[%s]初始调度...' % self.mid)
  
  def parse(self, response):
    items = []
    '''
    #测试
    img_urls = [
    "http://img0.utuku.china.com/620x0/auto/20161124/bf0cacb8-b879-43dd-b065-11b037d135f1.jpg",
    "http://img1.utuku.china.com/620x0/auto/20161124/31b00dad-08f7-420a-a810-dee0b6720114.jpg",
    "http://img3.cache.netease.com/photo/0008/2013-04-20/8STF8M0O5AAQ0008.jpg",
    "http://www.autohome.com.cn/669/",
    "http://img.carimg.com/product/1_500/1554/4aeede3957faa.jpg",
    "http://www.uncars.com/guide/gccm/images/2009/7/28/2009728CC46375A6621455A9D09BE21DD29302E.jpg",
    "http://img4.bitautoimg.com/autoalbum//files/20101019/125/550x366.jpg",
    "http://img0.pcauto.com.cn/pcauto/1104/05/1444864_1444864_21.jpg",
    "http://www.uncars.com/guide/gccm/images/2009/11/9/2009119E451CA141E614A6597D4CFFDA98C57A2.jpg",
    "http://img.carimg.com/product/1_500/1534/4ae9e64e001ee.jpg",
    ]
    for img_url in img_urls:
      item = DiorItem()
      item['image_urls'] = [img_url]
      item['task_info'] = { img_url:{'failed_cnt':0,'in_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} }
      items.append(item)
    return items
    '''

    img_urls, task_info = facade.get_task_imgs(self.name,self.max_request_num)
    for img in img_urls:
      item = DiorItem()
      item['image_urls'] = [img]
      item['task_info'] = {img: task_info[img]}
      items.append(item)
    return items
