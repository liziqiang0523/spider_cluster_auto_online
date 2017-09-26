#coding=utf-8
"""
Images Pipeline

See documentation in topics/media-pipeline.rst
"""

import hashlib
import six

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
import io

from PIL import Image

from scrapy.utils.misc import md5sum
from scrapy.http import Request
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FileException, FilesPipeline
from scrapy.pipelines.images import ImagesPipeline
from scrapy.pipelines.images import ImageException
from scrapy.utils.log import failure_to_exc_info
import logging
import datetime


from facade import facade
import time

class NewImagesPipeline(ImagesPipeline):
    """Abstract pipeline that implement the image thumbnail generation logic

    """
    #下载图片成功需要写入库中，失败则写回到相应task表中
    def item_completed(self, results, item, info):
        urls_suc = { x['url']:x['path'] for ok, x in results if ok }
        #下载成功则保存图片原始url与下载后的图片文件名对应关系
        for url, path in urls_suc.items():
            urls_suc_info = item['task_info'].get(url,{})
            if 'in_time' not in urls_suc_info:
                logging.warning("pipeline发现图片信息无in_time url:%s" % url)
            in_time = urls_suc_info.get('in_time',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            failed_cnt = urls_suc_info.get('failed_cnt',0)
            sucimg = {'url':url, 'file_name':path , 'suc_time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") , 'in_time':in_time , 'failed_cnt':failed_cnt}
            facade.save_imgs_suc(sucimg)
        #下载失败的图片连接重回相应的下载任务库
        urls_failed = [ x for x in item['image_urls'] if x not in urls_suc ]
        urls_failed_info = {}
        for url in urls_failed:
            urls_failed_info[url] = item['task_info'].get(url,{})
            failed_cnt = urls_failed_info[url].get('failed_cnt',0) + 1
            in_time = urls_failed_info[url].get('in_time',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            update_time = urls_failed_info[url].get('update_time',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            fail_info = {'failed_cnt':failed_cnt , 'in_time':in_time , 'update_time':update_time }
            urls_failed_info[url] = fail_info
        facade.save_imgs_failed(info.spider.name, urls_failed_info)
        for ok, value in results:
            if not ok:
                #print 'xxxxxxxxxxx'
                #print failure_to_exc_info(value)
                break
        if isinstance(item, dict) or self.IMAGES_RESULT_FIELD in item.fields:
            item[self.IMAGES_RESULT_FIELD] = [x for ok, x in results if ok]
        return item

    def get_images(self, response, request, info):
        path = self.file_path(request, response=response, info=info)
        #orig_image = Image.open(BytesIO(response.body))
        try:
            orig_image = Image.open(BytesIO(response.body))
        except Exception,e:
            print "url:%s  get_images failed:%s try io.BytersIO" % (request.url, e)
            try:
                orig_image = Image.open(io.BytesIO(response.body))
            except Exception,e:
                print "failed again. url:%s  get_images failed:%s try io.BytersIO" % (request.url, e)
                '''
                print "failed again. url:%s  get_images failed:%s try io.BytersIO" % (request.url, e)
                fout = open('/data/spider_cluster_pic_10_dev_test/oreo/log/%s' % path, 'w')
                fout.write(response.body)
                fout.close()
                '''
                raise ImageException("图片流处理失败。返回的html-body不是图片流")

        width, height = orig_image.size
        if width < self.min_width or height < self.min_height:
            raise ImageException("Image too small (%dx%d < %dx%d)" %
                                 (width, height, self.min_width, self.min_height))

        image, buf = self.convert_image(orig_image)
        yield path, image, buf

        for thumb_id, size in six.iteritems(self.thumbs):
            thumb_path = self.thumb_path(request, thumb_id, response=response, info=info)
            thumb_image, thumb_buf = self.convert_image(image, size)
            yield thumb_path, thumb_image, thumb_buf

    def file_path(self, request, response=None, info=None):
        ## start of deprecation warning block (can be removed in the future)
        def _warn():
            from scrapy.exceptions import ScrapyDeprecationWarning
            import warnings
            warnings.warn('ImagesPipeline.image_key(url) and file_key(url) methods are deprecated, '
                          'please use file_path(request, response=None, info=None) instead',
                          category=ScrapyDeprecationWarning, stacklevel=1)

        # check if called from image_key or file_key with url as first argument
        if not isinstance(request, Request):
            _warn()
            url = request
        else:
            url = request.url

        # detect if file_key() or image_key() methods have been overridden
        if not hasattr(self.file_key, '_base'):
            _warn()
            return self.file_key(url)
        elif not hasattr(self.image_key, '_base'):
            _warn()
            return self.image_key(url)
        ## end of deprecation warning block
        sign = 'www'
        url =  url + sign 
        m = hashlib.md5()
        m.update(url)
        md5 = m.hexdigest()
        
        #image_guid = hashlib.sha1(url).hexdigest()  # change to request.url after deprecation
        image_guid = md5  # change to request.url after deprecation
        #print("image_guid:%s" % image_guid)
        return '%s.jpg' % (image_guid)
