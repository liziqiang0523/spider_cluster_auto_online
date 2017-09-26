
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
  name="beijingxiandai"
  start_urls=[]
  login_post_data = {"xtczdm":"C1302SA04","xtczkl":"123456"}
  login_url = "https://124.42.120.211:8086/wxdms/login.do"
  handle_httpstatus_list=[404]

  def __init__(self):
    self.headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Host":"124.42.120.211:8086",
        "DNT":1,
         }

  def start_requests(self):
     return self.login()

  def login(self):
      post_data = urllib.urlencode(self.login_post_data)
      yield scrapy.FormRequest(self.login_url,headers=self.headers,meta={'q_flag':'login','cookiejar':1},formdata=self.login_post_data)


  def parse(self,response):
    req = []
    q_flag = response.request.meta.get('q_flag','')
    if q_flag == 'login':
      first_url = 'https://124.42.120.211:8086/wxdms/jsp/login/blank.jsp'
      req.append(Request(first_url,headers = self.headers ,meta={'q_flag':'first_url','cookiejar':response.meta['cookiejar']}))
      #req.append(Request(list_url,headers = self.headers ,meta={'q_flag':'list_url'},cookies = self.cookie))
    elif q_flag == 'first_url':
      request = self.parse_first(response)
      req.append(request)
    elif q_flag == 'list_url':
      request = self.parse_list_url(response)
      req.append(request)
    elif q_flag == 'item_url':
      self.parse_item_url(response)
    else:
      print q_flag

    return req

  def parse_first(self,response):
      print response.body,'first_url'
      #list_url = 'https://124.42.120.211:8086/wxdms/dlmaintenancordewx.do?action=queryforrclist&xsvinm=LNBRCFDK8HB211320&wxcpham=&wxdjzt=&wxjcrq=&endjcrq=&xtsjly=2&xttp=&wxkhxm=&wxwtbh='
      list_url = 'https://124.42.120.211:8086/wxdms/dlmaintenancordewx.do?wxwtid=3266389&action=dlMaintenancOrdeWXdetails'
      return Request(list_url,headers = self.headers , meta = {'q_flag':'list_url','cookiejar':response.meta['cookiejar']})
    

  def parse_list_url(self,response):
    print 'list_body',response.body
    item_url = 'https://124.42.120.211:8086/wxdms/dlmaintenancordewx.do?wxwtid=3266389&action=dlMaintenancOrdeWXdetails'
    return Request(item_url , headers = self.headers , meta= {'q_flag':'item_url','cookiejar':response.meta['cookiejar']})

  def parse_item_url(self,response):
    print 'item request.headers',response.request.headers
    print response.body
    print 'parse item url'
    pass

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
