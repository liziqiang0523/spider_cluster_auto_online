# -*- coding: utf-8 -*-

# Scrapy settings for oreo project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'oreo'

SPIDER_MODULES = ['oreo.spiders']
NEWSPIDER_MODULE = 'oreo.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)'
#USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 50
MAX_REQUESTS = 600
#每次下载最大任务数
MAX_REQ_NUM = 1000
# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0.91
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 500
CONCURRENT_REQUESTS_PER_IP = 500

# Disable cookies (enabled by default)
#COOKIES_ENABLED=False
COOKIES_ENABLED=True
COOKIES_DEBIG=True

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED=False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
   'Accept': '*/*',
   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'oreo.middlewares.downloadmiddleware.StatusUpdater': 499,
    'oreo.middlewares.downloadmiddleware.AddProxy': 752, 
    #'oreo.middlewares.downloadmiddleware.Proxy100Middleware': 102, 
    #'oreo.middlewares.downloadmiddleware.UserAgentMiddleware': 100, 
    #'oreo.middlewares.downloadmiddleware.CookiesMiddleware': 101, 
    'oreo.middlewares.downloadmiddleware.ProxyValidUpdate': 753,
    'oreo.middlewares.downloadmiddleware.ExceptionHandler': 899,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'oreo.pipelines.SomePipeline': 300,
#}


# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# NOTE: AutoThrottle will honour the standard settings for concurrency and delay
#AUTOTHROTTLE_ENABLED=True
# The initial download delay
#AUTOTHROTTLE_START_DELAY=5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY=60
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG=False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED=True
#HTTPCACHE_EXPIRATION_SECS=0
#HTTPCACHE_DIR='httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES=[]
#HTTPCACHE_STORAGE='scrapy.extensions.httpcache.FilesystemCacheStorage'

#mongo配置
MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27017
MONGO_DB_NAME = 'oreo'
MONGO_COLLECT_PAGE = 'page'

#SSDB-proxy配置
SSDB_PROXY_HOST = '127.0.0.1'
SSDB_PROXY_PORT = 8889

#SSDB-linkbase配置
SSDB_LINKBASE_HOST = '127.0.0.1'
SSDB_LINKBASE_PORT = 8881

#mongo 消息队列
MONGO_TASK_HOST = '127.0.0.1'
MONGO_TASK_PORT = 27017
MONGO_TASK_DB_NAME = 'task'

#SSDB-图片原始地址与下载地址的对应关系数据库
SSDB_IMGDB_HOST = '127.0.0.1'
SSDB_IMGDB_PORT = 8812
SSDB_IMGDB_HTABLE = 'dbm_spider_image'

#重试设置
RETRY_ENABLED = False
#RETRY_TIMES = 5
#RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409]
#抓失败则发送会kafka调度 通过needrecrawl可以设置不走kafka调度 如在线爬虫是不需要这个重读调度的
NEED_RECRAWL = True

#下载超时
DOWNLOAD_TIMEOUT = 15

#是否丢弃下载的原始网页 上线时去掉
DROP_PAGE = True
#DROP_PAGE = False

#日志设定 除此之外的log不要
#LOG_LEVEL = 'DEBUG'
LOG_LEVEL = 'INFO'
import os
LOG_PATH = os.getcwd() + '/log'
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)
LOG_FILE = '%s/scrapy.log' % LOG_PATH
LOG_FACADE = 'facade.log'
LOG_SPIDER = 'spider.log'
LOG_MIDDLEWARE = 'middleware.log'
#原始网页存储地
PAGE_PATH = os.getcwd() + '/log/pages'
if not os.path.exists(PAGE_PATH):
    os.makedirs(PAGE_PATH)
#图片下载设置
ITEM_PIPELINES = { 'oreo.pipelines.NewImagesPipeline': 1 }
#IMAGES_STORE = '/data1/netapp2/jingping_image/article_pic/'
IMAGES_STORE = os.getcwd() + '/log/article_pic/'
if not os.path.exists(IMAGES_STORE):
    os.makedirs(IMAGES_STORE)

HTTPERROR_ALLOW_ALL = True
EXTENSIONS = {
  'scrapy.telnet.TelnetConsole': None
 }
PROXY_LIST = [
  #{'proxy_url':'http://ip.hahado.cn:32999','proxy_user_pass':'wpp30:65512q'},
  {'proxy_url':'http://ip2.hahado.cn:40295','proxy_user_pass':'ydtsfojiay:qPJaObzKEYeHX'},
  {'proxy_url':'http://ip2.hahado.cn:40275','proxy_user_pass':'duoipvriezfde:bq4RYrQiWuQzv'},
  {'proxy_url':'http://ip2.hahado.cn:40271','proxy_user_pass':'duoipcnezxjlvkv:xXuXTPES9XPwp'},
  {'proxy_url':'http://ip2.hahado.cn:40263','proxy_user_pass':'duoipwpdlrfwc:fdFNb8g0bnn9I'},
]
