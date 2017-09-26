#!/usr/bin/python
#coding=utf-8
#author:auto_maker

import sys
from baseparser import BaseParser

class Parserstore_dzdp448(BaseParser):
  spider_name = "liziqiang_dp_230"
  parser_name = 'parse_item'
  link_types = ["item_url"]
  table_name = "store_dzdp"
  multi_block_rules =[
    {
      "pub_kv_rules":[
        {"name":"store_id","from_other":"url","regex":u"shop/(\d+)"},
        ],
      "xpath":"/html",
      "rules":[
        {"name":"city","xpath":u".//a[@class='city J-city']/text()","regex":u""},
        {"name":"store_city","xpath":u".//a[@class='city J-city']/text()","regex":u""},
        {"name":"store_name","xpath":u".//h1[@class='shop-name']/text()","regex":u""},
        {"name":"star","xpath":u".//span[contains(@class,'mid-rank-stars')]/@title","regex":u""},
        {"name":"review","xpath":u".//span[@id='reviewCount']//text()","regex":u"(\d+)"},
        {"name":"price","xpath":u".//span[@id='avgPriceTitle']//text()","regex":u"人均：(.*?)元"},
        {"name":"r_scores","xpath":u".//span[@id='comment_score']//text()","regex":u""},
        {"name":"address","xpath":u".//div[@class='expand-info address']//text()","regex":u""},
        {"name":"phone","xpath":u".//span[@itemprop='tel']//text()","regex":u""},
        {"name":"feature","xpath":u".//p[@class='expand-info J-service nug-shop-ab-special_a']//a/@class","regex":u""},
        {"name":"b_hours","xpath":u".//p[@class='info info-indent']//span[@class='item']/text()","regex":u""},
        {"name":"longitude","xpath":u".//div[@id='map']/img/@src","regex":u"center=(.*?),"},
        {"name":"latitude","xpath":u".//div[@id='map']/img/@src","regex":u",(.*?)&zoom"},
        {"name":"content","xpath":u".//div[@class='content']/span//text()","regex":u""},
        {"name":"correlation","xpath":u".//ul[@class='list J-ripple ripple']/li/a/@href","regex":u""},
        {"name":"fendian","xpath":u".//a[@class='branch J-branch']/text()","regex":u""},
        ]
      },
  ]
  must_keys = ["store_id","store_name","address"]
  replace_keys = ["store_id"]
class Parserdianping_shop_list449(BaseParser):
  spider_name = "liziqiang_dp_230"
  parser_name = 'parse_list'
  link_types = ["list_url"]
  table_name = "dianping_shop_list"
  multi_block_rules =[
    {
      "pub_kv_rules":[
        {"name":"mypos","xpath":u"//div[@class='bread J_bread']//text()","regex":u""},
        {"name":"city_id","from_other":"url","regex":u"category/(\d+)/"},
        {"name":"type1_id","from_other":"url","regex":u"category/\d+/(\d+)/"},
        {"name":"type2_id","from_other":"url","regex":u"category/\d+/\d+/(g\d+)"},
        {"name":"type1","from_other":"url","regex":u"//div[@class='bread J_bread']/span[2]//text()"},
        {"name":"type2","from_other":"url","regex":u"//div[@class='bread J_bread']/span[4]//text()"},
        ],
      "xpath":"//div[@id='shop-all-list']//li",
      "rules":[
        {"name":"store_name","xpath":u".//h4/text()","regex":u""},
        {"name":"store_url","xpath":u".//div[@class='tit']/a[1]/@href","regex":u""},
        {"name":"store_id","xpath":u".//div[@class='tit']/a[1]/@href","regex":u"shop/(\d+)"},
        {"name":"star","xpath":u".//div[@class='comment']/span/@title","regex":u""},
        {"name":"review","xpath":u".//a[@class='review-num']/b/text()","regex":u""},
        {"name":"price","xpath":u".//a[@class='mean-price']/b/text()","regex":u""},
        {"name":"r_scores","xpath":u".//span[@class='comment-list']//text()","regex":u""},
        {"name":"address","xpath":u".//span[@class='addr']//text()","regex":u""},
        {"name":"feature","xpath":u".//div[@class='promo-icon J_promo_icon']//a/@class","regex":u""},
        ]
      },
  ]
  must_keys = ["store_url","store_name"]
  replace_keys = ["store_url"]
class Parserstore_dzdp_empty450(BaseParser):
  spider_name = "liziqiang_dp_230"
  parser_name = 'parser_list_empty'
  link_types = ["list_url"]
  table_name = "store_dzdp_empty"
  multi_block_rules =[
    {
      "pub_kv_rules":[
        ],
      "xpath":"/html",
      "rules":[
        {"name":"empty","xpath":u".//div[@class='not-find-text']//text()","regex":u""},
        ]
      },
  ]
  must_keys = ["empty"]
  replace_keys = ["from_url"]
