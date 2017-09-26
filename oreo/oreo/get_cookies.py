#!/usr/bin/python
#coding=utf-8
'''
通过运营提供的微博帐号，获取登录后的cookie ，写入到数据库中。 供爬虫使用不同cookie进行访问。
'''
import time
import base64
import rsa
import binascii
import requests
import re,sys
import random
import settings
from pymongo import MongoClient
from pymongo.collection import Collection

try:
    from PIL import Image
except:
    pass
try:
    from urllib.parse import quote_plus
except:
    from urllib import quote_plus

reload(sys)
sys.setdefaultencoding('utf8')

accounts=[
    #{'username':'15811417306','pwd':'gengxiaochan'},
    {'username':'18255087821','pwd':'ppjnelv2'},
    
    #{'username':'18252448943','pwd':'xkexbta8'},
    #{'username':'lcg19880126@sina.com','pwd':'liuchenggang1988'},
]

agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
headers = {
    'User-Agent': agent
}

session = requests.session()
mongo_client = MongoClient(host = '172.16.40.12', port = 27017)
mongo_oreo = mongo_client.get_database('oreo')
mongo_cookies_col = Collection(mongo_oreo,'cookies')
#mongo_oreo = mongo_client.get_database(settings.MONGO_DB_NAME)

def getCookies(accounts,mongo_cookies_col):
    cookies=[]
    loginURL=""
    for e in accounts:
        account=e['username']
        password=e['pwd']
        cookie=login(account,password)
        cookie['userID'] = account
        cookies.append(cookie)
        mongo_cookies_col.update({'userID':cookie['userID']} , cookie , True)
        print cookie
    return cookies

def get_su(username):
    """
    对 email 地址和手机号码 先 javascript 中 encodeURIComponent
    对应 Python 3 中的是 urllib.parse.quote_plus
    然后在 base64 加密后decode
    """
    username_quote = quote_plus(username)
    username_base64 = base64.b64encode(username_quote.encode("utf-8"))
    print username_base64
    return username_base64.decode("utf-8")

# 预登陆获得 servertime, nonce, pubkey, rsakv
def get_server_data(su):
    pre_url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su="
    pre_url = pre_url + su + "&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)&_="
    pre_url = pre_url + str(int(time.time() * 1000))
    pre_data_res = session.get(pre_url, headers=headers)
    sever_data = eval(pre_data_res.content.decode("utf-8").replace("sinaSSOController.preloginCallBack", ''))
    print pre_data_res.content.decode("utf-8").replace("sinaSSOController.preloginCallBack", '')
    return sever_data


def get_password(password, servertime, nonce, pubkey):
    rsaPublickey = int(pubkey, 16)
    print 'ab'+str(rsaPublickey)
    key = rsa.PublicKey(rsaPublickey, 65537)  # 创建公钥
    print key
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)  # 拼接明文js加密文件中得到
    message = message.encode("utf-8")
    print message
    passwd = rsa.encrypt(message, key)  # 加密
    print passwd
    passwd = binascii.b2a_hex(passwd)  # 将加密信息转换为16进制。
    print passwd
    return passwd


def get_cha(pcid):
    cha_url = "http://login.sina.com.cn/cgi/pin.php?r="
    cha_url = cha_url + str(int(random.random() * 100000000)) + "&s=0&p="
    cha_url = cha_url + pcid
    cha_page = session.get(cha_url, headers=headers)
    with open("cha.jpg", 'wb') as f:
        f.write(cha_page.content)
        f.close()
    try:
        im = Image.open("cha.jpg")
        im.show()
        im.close()
    except:
        print(u"请到当前目录下，找到验证码后输入")


def login(username, password):
    # su 是加密后的用户名
    su = get_su(username)
    print su
    sever_data = get_server_data(su)
    servertime = sever_data["servertime"]
    nonce = sever_data['nonce']
    rsakv = sever_data["rsakv"]
    pubkey = sever_data["pubkey"]
    showpin = sever_data["showpin"]
    password_secret = get_password(password, servertime, nonce, pubkey)

    postdata = {
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'useticket': '1',
        'pagerefer': "http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl",
        'vsnf': '1',
        'su': su,
        'service': 'miniblog',
        'servertime': servertime,
        'nonce': nonce,
        'pwencode': 'rsa2',
        'rsakv': rsakv,
        'sp': password_secret,
        'sr': '1366*768',
        'encoding': 'UTF-8',
        'prelt': '115',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'returntype': 'META'
    }
    print postdata
    login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
    if showpin == 0:
        # print session.content
        print session
        login_page = session.post(login_url, data=postdata, headers=headers)
        print login_page.content
    else:
        pcid = sever_data["pcid"]
        get_cha(pcid)
        postdata['door'] = input('code')
        login_page = session.post(login_url, data=postdata, headers=headers)
    login_loop = (login_page.content.decode("GBK"))
    # print(login_loop)
    pa = r'location\.replace\([\'"](.*?)[\'"]\)'
    loop_url = re.findall(pa, login_loop)[0]
    print(loop_url)
    # 此出还可以加上一个是否登录成功的判断，下次改进的时候写上
    login_index = session.get(loop_url, headers=headers)
    # print session.cookies.get_dict()
    uuid = login_index.text
    print uuid
    uuid_pa = r'"uniqueid":"(.*?)"'
    uuid_res = re.findall(uuid_pa, uuid, re.S)[0]
    #uuid_res = 'ggbond1988'
    web_weibo_url = "http://weibo.com/%s/profile?topnav=1&wvr=6&is_all=1" % uuid_res
    print web_weibo_url
    weibo_page = session.get(web_weibo_url, headers=headers)
    cookie = session.cookies.get_dict()

    weibo_pa = r'<title>(.*?)</title>'
    # print(weibo_page.content.decode("utf-8"))
    userID = re.findall(weibo_pa, weibo_page.content.decode("utf-8", 'ignore'), re.S)[0]
    cookie['username'] = userID
    print(u"欢迎你 %s, 你在正在使用 xchaoinfo 写的模拟登录微博" % userID)
    return cookie


cookies=getCookies(accounts,mongo_cookies_col)

