from scrapy.spiders import  Spider
from scrapy.http import  Request
from oreo.facade import facade
import re,json
import base64,sys,os,datetime,time
import requests,urllib,urllib2
#from pybloomfilter import BloomFilter


class Che300Spider(Spider):
  name="koubei_autohome"
  start_urls=[
  #'https://42.81.9.47/autov7.9.5/alibi/seriesalibiinfos-pm1-ss135-st0-p1-s20-sy0.json'
  'https://112.65.117.189/autov7.9.5/alibi/alibiinfobase-pm1-k189277.json'
  ]
  handle_httpstatus_list=[404]
  def __init__(self):
    self.headers = {
    'User-Agent': 'iPhone?8.1.2?autohome?7.9.5?iPhone',
    'Host':'koubei.app.autohome.com.cn'
}
    #self.proxie={
        #'http':'http://182.117.228.228:8888'
#}
  def start_requests(self):
    for item in facade.get_task('koubei_autohome'):
      if 'url' in item:
        yield Request(item.get('url',''),headers=self.headers,meta={},dont_filter=True)
    for url in self.start_urls:
      yield  Request(url,headers=self.headers,meta={},dont_filter=True)

  def parse(self,response):
    info_content=response.body
    url=response.url
    info_json=json.loads(info_content)
    info_json['crawl_time']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    facade.update_item('koubei_autohome_app',{'from_url':url},info_json)
