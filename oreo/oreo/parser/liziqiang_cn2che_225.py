#!/usr/bin/python
#coding=utf-8
#author:auto_maker

import sys
from baseparser import BaseParser

class Parsercn2che_item442(BaseParser):
  spider_name = "liziqiang_cn2che_225"
  item_type = "cn2che_item"
  table_name = "cn2che_item"
  multi_block_rules =[
    {
      "pub_kv_rules":[
        {"name":"car_id","from_other":"url","regex":u"carinfo_(\d+).html"},
        ],
      "xpath":"/html",
      "rules":[
        {"name":"car_name","xpath":u".//h1[@id='title']//text()","regex":u""},
        {"name":"price","xpath":u".//strong[@id='price']/text()","regex":u""},
        {"name":"regest_date","xpath":u".//li[@id='spdate']//text()","regex":u"(\d{4}-\d+)"},
        {"name":"mileage","xpath":u".//div[@class='Detailed']//dl//ol/li[7]/text()","regex":u""},
        {"name":"area","xpath":u".//div[@class='Detailed']//dl//ol/li[8]/text()","regex":u""},
        {"name":"shelf_time","xpath":u".//div[@class='Detailed']//dl//ol/li[9]/text()","regex":u""},
        {"name":"tele","xpath":u".//b[@id='phone']/text()","regex":u""},
        {"name":"owner","xpath":u".//dt[@id='linkman']//text()","regex":u""},
        {"name":"user_type","xpath":u".//h2[@id='caruser']/text()","regex":u""},
        {"name":"total_num","xpath":u".//strong[@id='carcount']//text()","regex":u""},
        {"name":"gear","xpath":u".//div[@id='de01']//tbody/tr[2]/td[2]/text()","regex":u""},
        {"name":"pailiang","xpath":u".//div[@id='de01']//tbody/tr[2]/td[6]/text()","regex":u""},
        ]
      },
  ]
  must_keys = ["tele","car_id","car_name"]
  replace_keys = ["car_id"]
