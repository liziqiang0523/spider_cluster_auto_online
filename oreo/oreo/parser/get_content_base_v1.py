#!/bin/bash/python
#coding=utf-8
#author:liziqiang,sunlewei
'''
输入：content html
输出：所有段落清洗过后的list
功能：对content 的 html 片段进行处理。段落是文本的就抽取出来所有的文本放入输出的list中， 段落是图片的就抽取出来图片的URL放入输出的list中。

'''

import codecs,hashlib,csv, sys, json, datetime, urlparse, re, math, time, urlparse
from urllib import quote, unquote
import urllib,time,urllib2, json,sys,datetime,re,math
import traceback
import HTMLParser
from scrapy.http import TextResponse
from scrapy.selector import Selector

reload(sys)
sys.setdefaultencoding('utf-8')
class Element:
  
  font_num=150
  re_blank = '\s'#匹配空白字符正则
  re_replace = '(\[.*?\])|(您可以点击这里查看详情)|(有关该车的更多信息，)|(您可以点击这里查看详情。)|(分享到：.*?shareIn(tcO);)|(回顶部)|(&amp)'#替换段落文本正则
  re_tag = '(<table.*?>.*?</table>)|(<script.*?>.*?</script>)|(<link.*?>.*?</link>)|(<style.*?>.*?</style>)' #标签过滤正则
  re_continue = '更多精彩视|多款重磅新车发布|新车试驾性能测试就在汽车之家评测频道|版权声明'#过滤段落字符
  re_break = '相关内容回顾|相关文章：|更多阅读：|相关链接|相关阅读|相关文章链接|分页导航|推荐阅读|查看同类文章：|更多精彩内容：|欢迎订阅微信公众号《买车顾问》|了解更多'#段落终止正则
  passage_tag = '#xin_com_passage_split_tag#'#分段标签
  #passage_tag ='<br>'
  def __init__(self):
    #print 'Element __init()__'
    self.re_prog = re.compile(self.re_blank)
    self.re_p = re.compile(self.re_replace)
    self.re_html=re.compile(u'(<.*?>)')
    self.re_table=re.compile(self.re_tag)
    self.pattern_continue = re.compile(self.re_continue)
    self.pattern_break = re.compile(self.re_break)
    #self.after_break = re.compile(Element.re_af_break)
    self.pattern_class = re.compile(r'<[a-zA-Z0-9]+ (.*?)>')

  #在积累的规则上添加新的过滤规则 
  def add_init(self,re_replace_add='',re_tag_add='',re_continue_add='',re_break_add=''):
    #print '---------------add_init()'
    re_str = u'\s%s' % str(Element.re_blank)
    if len(re_replace_add) > 0:
      self.re_p = re.compile(r'replce:%s|%s' %( self.re_replace , str(re_replace_add)))
      print 'replce:%s|%s' %( self.re_replace , str(re_replace_add))
    if len(re_tag_add) > 0:
      self.re_table = re.compile(r'%s|%s' %( self.re_tag  , str(re_tag_add)))
      print 'tag:%s|%s' %( self.re_tag  , str(re_tag_add))
    if len(re_continue_add) > 0 :
      print 'continue:%s|%s' %( self.re_continue , str(re_continue_add))
      self.pattern_continue = re.compile(r'%s|%s' %( self.re_continue , str(re_continue_add)))
    if len(re_break_add) > 0 :
      print 'break:%s|%s' %( self.re_break , str(re_break_add))
      self.pattern_break = re.compile(r'%s|%s' %( self.re_break , str(re_break_add)))
  
  #节点转字符串
  def node_to_str(self,node,xpath=''):
    node_str=""
    if isinstance(node,list):
      node_str="<div>"
      for n in node:
         if isinstance(n,str):
           node_str=node_str+n.encode('utf-8')
         else:
           node_str=node_str+n.extract().encode('utf-8')
      node_str = node_str+"</div>"
      node = self.str_to_node(node_str)
    if len(xpath)>0:
      node = node.xpath(xpath)
    #print 'xpath:%s len : %d' % (xpath,len(nodes))
    if isinstance(node,list):
      for n in node:
        node_str=node_str+n.extract().encode('utf-8')
      return node_str
    elif isinstance(node,Selector):
      return node.extract().encode('utf-8')
    else:
      return ''

  #节点类型字符串转节点，返回一个节点list
  def str_to_node(self,node_str,xpath=''):
    response = TextResponse('test.html',body=node_str,encoding='utf-8')
    hxs = Selector(response)
    nodelist=hxs.xpath('/html/body/*%s' % str(xpath if len(xpath)>0 else ''))
    return nodelist

  #对节点的处理
  def handle_node(self,node):
    return node
  #对图片处理
  def handle_picpath(self,picpath):
    return picpath
  #文本处理
  def handle_txt(self,txt):
    return txt
  #统一清除所有的html标签，仅仅要纯文本
  def trim_html(self,txt):
    txt = txt.strip()
    if len(txt) < 1: return txt
    if txt[0] == '<' and txt[-1] == '>':
      hxs = Selector(TextResponse('http://www.baidu.com', body=txt, encoding='utf-8'))
      txt = ''.join(hxs.xpath('.//text()').extract())
      return txt.strip()
    else :
      return txt

  #通过content 得到所有段落元素。
  def get_element(self,content):
    content = content.replace('\n','').replace('\r','').replace('\t','')
    #print content
    content = self.re_table.sub('',content)
    content = content.replace('<br>',self.passage_tag)
    #print content
    #re_whitespace = re.compile(r'\\r\\n|\\r|\\n|\s')
    element_list = []
    response = TextResponse('test.html',body=content,encoding='utf-8')
    hxs = Selector(response)
    children=hxs.xpath('/html/body/*')
    if len(children)>1:
      #print '节点个数：%d' % len(children)
      nodes = hxs.xpath('/html/body/*|/html/body/text()|/html/body/img')
    else :
      #print '节点个数：1'
      #获取内容分割后的数组
      nodes = hxs.xpath('/html/body/*/*|/html/body/*/text()|/html/body/*/img')
    #遍历分割内容
    i=0
    for node in nodes:
      is_node = re.search(r'<.*?>',node.extract())
      if is_node:
        node=self.handle_node(node)#节点处理
        #print node.extract() 
        #去除p标签下的a标签
        if node.extract().startswith('<p'):
         strnode=re.compile(r'<a.*?>|</a>|<font.*?>|</font>|<strong.*?>|</strong>|<span.*?>|</span>|<b.*?>|</b>|<!--.*?-->').sub('',node.extract())
         strnode= strnode.replace('\r','').replace('\n','').decode('utf-8','ignore')
         #print strnode
         #exit(0)
         response = TextResponse('test.html',body=strnode,encoding='utf-8')
         hxs = Selector(response)
         newnode = hxs.xpath('/html/body/p')
         if len(newnode)>0:
           node = newnode[0]
        if node.extract()[:4] == '<img':
          if 'src_real' in node.extract():
            imgs = node.xpath('.//@src_real').extract()
          elif 'ps_logo.jpg' in node.extract():
            imgs = node.xpath('.//@original').extract() 
          elif 'data-original-src' in node.extract():
            imgs = node.xpath('.//@data-original-src').extract() 
          elif 'data-original' in node.extract():
            imgs = node.xpath('.//@data-original').extract()
          elif 'data-url' in node.extract():
            imgs = node.xpath('.//@data-url').extract()
          elif 'data-src' in node.extract():
            imgs = node.xpath('.//@data-src').extract()
          else:
            imgs = node.xpath('.//@src').extract()
          for img in imgs:
            img = self.handle_picpath(img)#图片路径处理
            element_list.append(img)
        else:
          if "<img" in node.extract():
            element_son_list = self.get_element(node.extract().encode('utf-8'))
            element_list.extend(element_son_list)
          else:
            text = ' '.join(node.xpath('.//text()').extract())
            #print 'font_num:%s' % self.font_num
            if len(text) < Element.font_num and len(text.strip())>0:
              txtarr = text.split(self.passage_tag)
              for txtitem in txtarr:
                if(len(txtitem.strip())>0):
                  txtitem = self.handle_txt(txtitem)#文本处理
                  element_list.append(txtitem)
                  #element_list.append(text)
            #print '需要继续抽取',node.extract()
            else:
              element_son_list = self.get_element(node.extract().encode('utf-8'))
              element_list.extend(element_son_list)
      else:
        txt = node.extract().encode('utf-8').replace('\r','').replace('\n','')
        txt = self.handle_txt(txt)#文本处理
        txt = txt.encode('utf-8')
        #print txt
        txtarr = txt.split(self.passage_tag)
        #print arr for arr in txtarr
        #try :
        for txtitem in txtarr:
          if(len(txtitem.strip())>0):
             element_list.append(txtitem)
        #except:
        #  print 'txt----i--------------------%s' % txt
        #  if(len(txt.strip())>0):
        #   element_list.append(txt)

    return element_list
  
  #对获取的每个段落元素进行清理和匹配规则。
  def get_clean_list(self,content=''):
    clean_list = []
    element_list = self.get_element(content)
    for element in element_list:
      #element=element.replace('\r','').replace('\n','')
      ''' 
      if  re.compile('声明：此价格为经销商个体行为，不代表全部经销商').search(element.encode('utf-8')):
        print element.encode('utf-8')
        break
      '''
      d = {}
      match_break = self.pattern_break.search(element.encode('utf-8'))
      if match_break:
        print'break:%s' % element.encode('utf-8')
        break
      match_continue = self.pattern_continue.search(element.encode('utf-8'))
      if match_continue:
        print 'continue:%s' % element.encode('utf-8')
        continue
      if self.re_p.search(element.encode('utf-8')):
         print 'replace:%s' % element.encode('utf-8')
         element=self.re_p.sub('',element.encode('utf-8'))
      html_parser = HTMLParser.HTMLParser()
      txt = html_parser.unescape(element.strip())
      d['ct'] = txt
      if len(txt) == 0:
        continue
      #print 'txt-------------------%s' % txt
      # changed by gxc at 2016/12/22
      # 图片路径不一定有http开头
      if element[:5] == 'http:' or element[:5]=='https' or element[:5]=='data:' or self.pic_rule(element):
        d['tp'] = 'img'
      else:
        d['tp'] = 'txt'

      clean_list.append(d)
      #match_af_break = self.after_break.search(element.encode('utf-8'))
      #if match_af_break:
      #  break
      #print d
    return clean_list
  
  def process_content(self,content):
    pass
  
  def pic_rule(self,element):
    return False

