#coding=utf-8
#auhtor:shiyuming,liziqiang
'''
  spider中间件
'''

from oreo.facade import facade
from oreo.items import ImgItem
from user_agents import agents

class ImgItemMiddleware(object):
	'''
	加载img item 供imgpipeline下载图片
	'''
	
	def __init__(self):
		#self.facade = Facade()
		print 'debug:下载图片中间件启动.'
	
	def process_spider_output(self, response, result, spider):
		items = facade.getImgItem(spiderName=spider.name,url_num=5)
		newResults = []
		for item in items:
			imgItem = ImgItem()
			imgItem['imgUrl'] = item['imgUrl']
			imgItem['spiderName'] = item['spiderName']
			newResults.append(imgItem)
			print 'debug:imgurl=[%s]' % imgItem['imgUrl']
		newResults.extend(result)
		print 'debug:the num of newResults =[%d]' % len(newResults)
		
		return newResults

