# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class OreoItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class DiorItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()
    tags = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
    task_info = scrapy.Field()
