
#coding=utf-8
from scrapy.spiders import  Spider
from scrapy.selector import Selector
from scrapy.http import  Request
from oreo.facade import facade
import re,json,urlparse,scrapy
import base64,sys,os,datetime,time
import requests,urllib,urllib2,logging
#from pybloomfilter import BloomFilter


class TaoChe(Spider):
  name="yinguoshu"
  start_urls=[]
  handle_httpstatus_list=[404]
  def __init__(self):
    self.headers = {
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrom/50.0.2661.75 Safari/537.36",
        "Referer":"https://www.innotree.cn/allProjects",
        "Host":"www.innotree.cn",
}
    self.cookie = {
        "_user_identify_":'4be9f36d-1489-3bf5-a768-1a9d2af89d70',
        "JSESSIONID":"aaaPgdm2Yb7ZThyvQF7Xv",
        "Hm_lvt_37854ae85b75cf05012d4d71db2a355a":"1496720517",
        "Hm_lpvt_37854ae85b75cf05012d4d71db2a355a":"1496726593",
        "uID":"447139",
        "sID":"72c5390dd25eacec73564e4d24eb9147",
     }
    #self.proxie={
    #    'http':'http://182.117.228.228:8888'
#}
  def start_requests(self):
    #url = "https://www.innotree.cn/ajax/bigdata/company/getList?type=&page=1&size=10&first_ids=&second_ids=&third_ids=130802&round=&area=1&tags="
    url = facade.load_yinguoshu_task(self.name)
    #url = 'https://www.innotree.cn/ajax/bigdata/company/getList?type=&page=1&size=10&first_ids=&second_ids=&third_ids=140304&round=-1&area=1&tags=%E7%94%B5%E5%AD%90%E5%95%86%E5%8A%A1'
    yield Request(url,headers=self.headers,meta={},cookies = self.cookie )

  def parse(self,response):
    return self.get_car_url(response)

  def get_car_url(self,response):
      html_body = response.body
      print html_body
      result = json.loads(html_body)
      page = result.get('data',{}).get('page',0)
      total = result.get('data',{}).get('total',0)
      third_ids = result.get('data',{}).get('third_ids','')
      round_id= result.get('data',{}).get('round_ids','')
      tags = result.get('data',{}).get('tags','')
      tags = urllib.quote(tags.encode('utf-8'))
      area = result.get('data',{}).get('area','')
      if page==1 and total > 10:
        for pn in range(2,total/10+2):
          new_url = "https://www.innotree.cn/ajax/bigdata/company/getList?type=&page=%d&size=10&first_ids=&second_ids=&third_ids=%s&round=%s&area=%s&tags=%s" % (pn,third_ids,round_id,area,tags)
          logging.info('挖掘出新链接[%s],来自：%s' % (new_url,response.url))
          facade.save_new_yinguoshu(new_url)
          print new_url
      data = result.get('data',{}).get('list',[])
      if len(data) == 0:
        facade.update_item('yinguoshu_no_item',{'from_url':response.url},{'from_url':response.url})
      for item in data:
        item['from_url'] = response.url
        item['crawl_time'] = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
        facade.update_item('yinguoshu_item',{'cid':item['cid']},item)
        #facade.save_yinguoshu(item)
        logging.info('save item:{"cid":"%s"}' % item['cid'])
