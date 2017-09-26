
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
  name="taochewuyou"
  start_urls=[]
  handle_httpstatus_list=[404]
  def __init__(self):
    self.headers = {
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrom/50.0.2661.75 Safari/537.36",
}
    self.city_list = [{"cityid":"762","city":"南京","changeFlag":"1"},
   {"cityid":"763","city":"镇江","changeFlag":"1"},
   {"cityid":"764","city":"无锡","changeFlag":"1"},
   {"cityid":"765","city":"苏州","changeFlag":"1"},
   {"cityid":"766","city":"江阴","changeFlag":"1"},
   {"cityid":"767","city":"宜兴","changeFlag":"1"},
   {"cityid":"768","city":"扬州","changeFlag":"1"},
   {"cityid":"769","city":"泰州","changeFlag":"1"},
   {"cityid":"770","city":"淮安","changeFlag":"1"},
   {"cityid":"771","city":"盐城","changeFlag":"1"},
   {"cityid":"772","city":"东台","changeFlag":"1"},
   {"cityid":"773","city":"宿迁","changeFlag":"1"},
   {"cityid":"1111111112","city":"南通","changeFlag":"1"},
   {"cityid":"1111111113","city":"常熟","changeFlag":"1"},
   {"cityid":"1111112346","city":"连云港","changeFlag":"1"},
   {"cityid":"1111112347","city":"张家港","changeFlag":"1"},
   {"cityid":"1111112349","city":"徐州","changeFlag":"1"},
   {"cityid":"1111112357","city":"常州","changeFlag":"1"},
   {"cityid":"1111112356","city":"昆山","changeFlag":"1"},
   {"cityid":"6564","city":"芜湖","changeFlag":"1"},
   {"cityid":"1111112348","city":"安庆","changeFlag":"1"},
   {"cityid":"1111112354","city":"滁州","changeFlag":"1"},
   {"cityid":"1111112358","city":"池州","changeFlag":"1"},
   {"cityid":"6557","city":"济宁","changeFlag":"1"},
   {"cityid":"6562","city":"邹城","changeFlag":"1"},
   {"cityid":"6563","city":"寿光","changeFlag":"1"},
   {"cityid":"1111112353","city":"枣庄","changeFlag":"1"},
   {"cityid":"6561","city":"湖州","changeFlag":"1"},
   {"cityid":"6566","city":"义乌","changeFlag":"1"},
   {"cityid":"1111112345","city":"金华","changeFlag":"1"},
   {"cityid":"1111112350","city":"衢州","changeFlag":"1"},
   {"cityid":"1111112352","city":"东阳","changeFlag":"1"},
   {"cityid":"1111112355","city":"永康","changeFlag":"1"},
   {"cityid":"1111112359","city":"诸暨","changeFlag":"1"},
   {"cityid":"6565","city":"新余","changeFlag":"1"},
   {"cityid":"1111112351","city":"上饶","changeFlag":"1"},]
    #self.proxie={
    #    'http':'http://182.117.228.228:8888'
#}
  def start_requests(self):
    #for data in self.city_list:
      data = {"cityid":"1111112351","city":"上饶","changeFlag":"1"}
      post_data = urllib.urlencode(data)
    #print post_data
      url = "http://ic5u.com/index.php/Home/HomeBase/changeCity"
      yield scrapy.FormRequest(url,headers=self.headers,meta={'city':data['city'],'q_flag':1},formdata=data)
    #yield Request(url,headers=self.headers,meta={},method='post',body=post_data,dont_filter=True)

  def parse(self,response):
    print response.headers
    city = response.request.meta.get('city','未知城市')
    q_flag = response.request.meta.get('q_flag',0)
    print city
    if q_flag == 1:
      cookie =  response.headers.getlist('Set-Cookie')
      print cookie
      try:
        r_cookie = cookie[0].split('PHPSESSID=')[-1].split(';')[0]
        print r_cookie
      except:
        pass
      print 'new'
      return Request('http://ic5u.com/index.php/Home/CarSearch/index/', meta={'q_flag':2},cookies = {'PHPSESSID':'ogiuqikudnu4is1hsg29h2dd13'})
      #return Request('http://ic5u.com/index.php/Home/CarSearch/index/', meta={'q_flag':2,'city':city,'page':1,'cookie_old':'ogiuqikudnu4is1hsg29h2dd13'},cookies = {'PHPSESSID':'ogiuqikudnu4is1hsg29h2dd13'})
      #return Request('http://ic5u.com/index.php/Home/CarSearch/index/p/1.html',meta={'q_flag':2,'city':city,'page':1,'cookie_old':r_cookie}, cookies = {'PHPSESSID':r_cookie})
    if q_flag == 2:
      return self.get_car_url(response)

  def get_car_url(self,response):
      html_body = response.body
      page = response.request.meta.get('page',0)
      city = response.request.meta.get('city',0)
      cookie_old = response.request.meta.get('cookie_old','')
      hxs = Selector(text = html_body)
      cars = hxs.xpath('//ul[@class="car-info-ul clearfix"]/li/a/@href').extract()
      # city = hxs.xpath('//span[@id="current_city"]/text()').extract()
      #print ''.join(city)
      print city
      for car in cars:
         #print car
         car_id = re.compile('\/info\/v\/(\d+)').findall(car)
         if car_id:
           car_id = car_id[0]
         else:
           continue
         print car_id
         url = 'http://ic5u.com%s' % car
         item = {'car_id':car_id,'city':city,'url':url}
         facade.update_item('taoche0515',{'car_id':car_id,'city':city},item)
         #self.mongo_db.car_list_url.update({'url':url,'city':city},item,True)
      if len(cars) == 12:
        next_page = page + 1
        next_url = 'http://ic5u.com/index.php/Home/CarSearch/index/p/%d.html' % next_page
        print 'next_page',next_url
        facade.update_item('taoche_linkbase',{'url':next_url,'city':city},{'url':next_url,'cookie_old':cookie_old,'page':page,'city':'city'})
        logging.info('保存城市%s,第%d页下一页的的链接：%s' %(city,page,next_url))
        print cookie_old
        return Request(next_url,meta={'q_flag':2,'city':city,'page':next_page,'cookie_old':cookie_old},cookies = {'PHPSESSID':cookie_old})
