#!/usr/bin/python
#coding=utf-8
#author:shiyuming.shi@gmail.com

from lxml.html import fromstring
from lxml import etree
import re, traceback, datetime

control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
control_char_re = re.compile('[%s]' % re.escape(control_chars))

def doExtract(html,threshold=None):
  threshold = threshold == None and 0.5 or float(threshold)
  title=""
  pdate=""
  mtxt=""
  #t_begin=datetime.datetime.now()
  try:
    html = unicode(html, 'utf8')
    mtHtml = _extMainText(html, threshold)
    # Transfer to plain text:
    mtxt = getText(mtHtml)
    # extract title and postdate, and wash by maintext
    title, pdate = getTitleAndPostdate(html, mtxt)
  except Exception,e:
    print '正文抽取异常: '
    print e
    print traceback.print_exc()
  #t_end=datetie
  print '+++++++++++++++++++++++++++'
  print 'title:[%s]' % title
  print 'pdate:[%s]' % pdate
  print 'mtxt:[%s]' % mtxt
  print '----------------------------'
  return (mtxt,title,pdate)

def getText(html, ptagsIgnore=[], ptagsNewline=[], ptagsSave=[]):
  root = fromstring(html)
  tagsIgnore=["head", "style", "script", "noscript", "<built-in function comment>", "option"]
  tagsNewline=["p","div", "h3", "h4", "h5", "h6", "br", "li"]
  tagsSave = ["img","h1","h2"]
  for p in ptagsIgnore:
    if p not in tagsIgnore:
      print p
      tagsIgnore.append(p)
      print tagsIgnore
  if len(ptagsNewline) > 0:
    tagsNewline = ptagsNewline
  for p in ptagsSave:
    tagsSave.append(p)
  def _getText(tree):
    text = ''
    hasChild = False
    if len(tree) > 0:
      hasChild = True
    tag = str(tree.tag).lower()
    if (tag == '<built-in function comment>' or 
      tag == 'style' or
      tag == 'script' or
      tag == 'noscript' or
      str(tree.tag).lower() in tagsIgnore):
      return ''
    #判断是否是保留标签
    if tag in tagsSave:
      text += "<" + tag + " "
      #读取标签属性
      for k,v in tree.attrib.items():
        text += k + "='" + v + "' "
      if tree.text or hasChild:
        text += ">"
      else:
        text += "/>"
    #添加文本和继续往下遍历
    if tree.text != None:
      text += tree.text
    for child in tree:
      text += _getText(child)
    #判断是否是保留标签,保留则添加关闭标签
    if tag in tagsSave:
      if tree.text or hasChild:
        text += "</" + tag + ">"
    elif str(tree.tag).lower() in tagsNewline:
      text += '\n'
    if tree.tail != None:
      text += tree.tail
    return text
  return _getText(root)

def _extMainText(html, threshold, filterMode=False):
  """
  Parses HTML and keeps only main text parts.

  PARAMETERS:
  html - Input html text, MUST BE UNICODE!
  threshold - The density threshold to distinguish major content & others.
  filterMode - Use normal 'Extract' mode or the other 'Filter' mode.

  RETURN:
  html fragments of main text
  """
  html = _removeControlChars(html)
  root = fromstring(html)
  densDic = _calcDensity(root)
  if filterMode:
    return _filterSpam(densDic, threshold)
  else:
    maxPart, textLen, maxPartChilds, textLenChilds = _getMainText(densDic, threshold)
    if textLenChilds > textLen:
      return ''.join(map(lambda tree: etree.tostring(tree, encoding = unicode) if tree != None else '', maxPartChilds))
    else:
      return etree.tostring(maxPart, encoding = unicode) if maxPart != None else ''

def findDateByReg(input):
  #通过正则找时间
  dateRegs = [r'\d{4}年\d{1,2}月\d{1,2}日',r'\d{4}-\d{1,2}-\d{1,2}',r'发表于: \d{1,2}-\d{1,2}',r'\d{1,2}小时前']
  if input is None or len(input) < 4:
    return ''
  pdate = ''
  for reg in dateRegs:
    matches = re.findall(reg,input)
    if matches is not None and len(matches) > 0:
      pdate = matches[0]
      return pdate
  return pdate

def getTitleAndPostdate(htmlbody, maintxt):
  '''
  抽取title和postdate，并通过maintxt清洗title
  '''
  postdate = ''
  title = ''
  html = _removeControlChars(htmlbody)
  root = fromstring(html)
  #find the date from mainTxt
  postdate = findDateByReg(maintxt)
  isPostdateOk = False
  if len(postdate) >= 4:
    isPostdateOk = True

  def _getTitleAndPostdate(tree,isTitleOk = False,isPdateOk = False):
    title = '' 
    pdate = ''
    if tree is None:
      return title,pdate

    tag = str(tree.tag).lower()
    if tag in ['meta','script','noscript','style','<built-in function comment>']:
      return title,pdate

    if isTitleOk == False and tag == 'title':
      title = tree.text.strip() if tree.text != None else ''
      if len(title) > 1:
        isTitleOk = True
    elif isPdateOk == False:
      txt = tree.text
      #find the pdate by reg
      pdate = findDateByReg(txt)
      if len(pdate) > 4:
        isPdateOk = True
      
    if isTitleOk == False or isPdateOk == False:
      treeOrig = tree[:]
      for subnode in treeOrig:
        titletmp, pdatetmp = _getTitleAndPostdate(subnode,isTitleOk,isPdateOk)
        if isTitleOk == False and len(titletmp) >= 2:
          title = titletmp
          isTitleOk = True
        if isPdateOk == False and len(pdatetmp) >= 4:
          pdate = pdatetmp
          isPdateOk = True
        if isTitleOk and isPdateOk :
          break
    return (title,pdate)

  title, ppdate = _getTitleAndPostdate(root,isTitleOk=False,isPdateOk=isPostdateOk)
  if isPostdateOk == False:
    postdate = ppdate
  #clean the title
  
  return (title,ppdate)

def _calcDensity(tree):
  """
  Calculate the text density for every etree branch. The define of text density is:
  (the length of pure text content under current html tag) / (total length of all content under current html tag)

  Return: {'self': (tag density, length of pure text, total length of html tags and text, etree instance), 
  'child': list of density dics for child entities }
  """
  tag = str(tree.tag).lower()
  if (tag == '<built-in function comment>' or
     tag == 'script' or
     tag == 'noscript' or
     tag == 'style'):
    return {'self': (0.0, 0, 0, tree)}
  text = tree.text if tree.text != None else ''
  tail = tree.tail if tree.tail != None else ''
  countTextLen = len(text.strip()) + len(tail.strip())
  totalLen = len(etree.tostring(tree, encoding = unicode)) if tree != None else 0
  if str(tree.tag).lower() == 'br':
    return {'self': (1.0 / totalLen, 1, totalLen, tree)}
  dicList = []
  treeOrig = tree[:]
  for subtree in treeOrig:
    textNode = None
    if subtree.tail and len(subtree.tail.strip()) > 0:
      index = tree.index(subtree)
      textNode = subtree.tail
      subtree.tail = ''
    dic = _calcDensity(subtree)
    dicList.append(dic)
    textLen = dic['self'][1]
    countTextLen += textLen
    # Treat subtree.tail as an independent etree branch:
    if textNode != None:
      textNodeTotalLen = len(textNode)
      textNodeTextLen = len(textNode.strip())
      textTree = etree.Element('span')
      textTree.text = textNode
      tree.insert(index + 1, textTree)
      dicList.append({'self': (float(textNodeTextLen) / textNodeTotalLen, textNodeTextLen, textNodeTotalLen, textTree)})
      countTextLen += textNodeTextLen
  density = float(countTextLen) / totalLen if totalLen != 0 else 0.0
  return {'self': (density, countTextLen, totalLen, tree), 'child': dicList}

def _removeControlChars(html):
  """
  Replace null bytes in html text with space char to walk around lxml bug in _convert_tree func.

  PARAMETERS:
  html - The original html text (must be unicode).

  RETURN:
  replaced html text.
  """
  assert type(html) == unicode, 'Input html text must be unicode!'
  return control_char_re.sub(' ', html)

def _filterSpam(densDic, threshold):
  """
  Walk through html document, drop off all etree branches that having low text
  density, and return the left parts of fragments.

  Return: html fragments of main text
  """
  dens, textLen, totalLen, tree = densDic['self']
  # If density is larger than threshold, keep and return current tag branch:
  if dens >= threshold:
    return etree.tostring(tree, encoding = unicode)
  if str(tree.tag).lower() == 'br':
    return etree.tostring(tree, encoding = unicode)
  # If density of current tag branch is too small, check its children:
  else:
    frags = []
    if densDic.has_key('child'):
      for childDic in densDic['child']:
        frags.append(_filterSpam(childDic, threshold))
    return ''.join(frags)

def _getMainText(densDic, threshold):
  """
  Get the largest html fragment with text density larger than threshold according 
  to density dictionary.

  And the largest html fragment could be made up of several continuous brother
  html branches.

  Return: (etree instance, text length, list of child etrees, total text length of child etrees)
  """
  dens, textLen, totalLen, tree = densDic['self']
  maxChildTrees = []
  maxChildTreesTextLen = 0
  # If density is bigger than threshold, current tag branch is the largest:
  if dens >= threshold:
    maxTree = tree
    maxTextLen = textLen
  # If density of current tag branch is too small, check its children:
  else:
    maxTree = None
    maxTextLen = 0
    maxChildSubTrees = []
    maxChildSubTreesTextLen = 0
    childTreesTmp = []
    childTreesTmpTextLens = []
    childTreesTmpTotalLens= []
    if densDic.has_key('child'):
      for childDic in densDic['child']:
        childDens, childTextLen, childTotalLen, childTree = childDic['self']
        tree, textLen, childTrees, childTreesTextLen = _getMainText(childDic, threshold)
        # Remember the largest tag branches of children:
        if childTreesTextLen > maxChildSubTreesTextLen:
          maxChildSubTrees, maxChildSubTreesTextLen = childTrees, childTreesTextLen
        childTreesTmp.append(childTree)
        childTreesTmpTextLens.append(childTextLen)
        childTreesTmpTotalLens.append(childTotalLen)
        if textLen > maxTextLen:
          maxTree = tree
          maxTextLen = textLen
      # Find the largest html fragment under current tag branch:
      for j in range(1, len(childTreesTmp) + 1):
        for i in range(j):
          childTreesTmpTotalLen= sum(childTreesTmpTotalLens[i:j])
          childTreesTmpTextLen = sum(childTreesTmpTextLens[i:j])
          childTreesTmpTotalLen = 1 if childTreesTmpTotalLen == 0 else childTreesTmpTotalLen
          if float(childTreesTmpTextLen) / childTreesTmpTotalLen >= threshold:
            if childTreesTmpTextLen > maxChildTreesTextLen:
              maxChildTrees = childTreesTmp[i:j]
              maxChildTreesTextLen = childTreesTmpTextLen
      # Compare html fragment of current tag branch and the ones of children:
      if maxChildSubTreesTextLen > maxChildTreesTextLen:
        maxChildTrees, maxChildTreesTextLen = maxChildSubTrees, maxChildSubTreesTextLen
  return (maxTree, maxTextLen, maxChildTrees, maxChildTreesTextLen)
