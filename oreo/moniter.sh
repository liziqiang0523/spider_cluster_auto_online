#!/bin/shell
#author:shiyuming
#监控scrapy任务 对不同的爬虫设置不同的实例数量，每隔10分钟检查一下是否需要补充启动实例

#while [ 2 -gt 1 ]
#do
  #xywy爬虫 实例数为50
  num_ask=`ps -ef | grep scrapy | grep "crawl xywy" | wc -l`
  if [ $num_ask -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl xywy &
    echo "start up a spider of xywy at[`date`]"
    sleep 1
  fi

  #ask120爬虫 实例数为2
  num_ask=`ps -ef | grep scrapy | grep -v "ask120_"| grep "crawl ask120" | wc -l`
  if [ $num_ask -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl ask120 &
    echo "start up a spider of ask120 at[`date`]"
    sleep 1
  fi

  #one爬虫 实例数为2
  num_one=`ps -ef | grep scrapy | grep "crawl one" | wc -l`
  if [ $num_one -lt 0 ];then
    #nohup /usr/bin/python2.7 /usr/bin/scrapy crawl one &
    #echo "start up a spider of one at[`date`]"
    echo ""
    sleep 1
  fi
  
  #jd爬虫 实例数为20
  num_jd=`ps -ef | grep scrapy | grep "crawl jd" | wc -l`
  if [ $num_jd -lt 0 ]; then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl jd &
    echo "start up a spider of jd at[`date`]"
    sleep 1
  fi

  #ask39爬虫 实例数为6
  num_ask39=`ps -ef | grep scrapy | grep "crawl ask39" | wc -l`
  if [ $num_ask39 -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl ask39 &
    echo "start up a spider of ask39 at[`date`]"
    sleep 1
  fi

  #baidu-medical爬虫 实例数为20
  num_baidu=`ps -ef | grep scrapy | grep "baidu" | wc -l`
  if [ $num_baidu -lt 60 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl baidu & 
    echo "start up a spider of- baidu at[`date`]"
    sleep 1
  fi

  #douban
  num_douban=`ps -ef | grep scrapy | grep "douban" | wc -l`
  if [ $num_douban -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl douban & 
    echo "start up a spider of douban at[`date`]"
    sleep 1
  fi

  #suning
  num_suning=`ps -ef | grep scrapy | grep "suning" | wc -l`
  if [ $num_suning -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl suning & 
    echo "start up a spider of suning at[`date`]"
    sleep 1
  fi

  #vip
  num_vip=`ps -ef | grep scrapy | grep "vip" | wc -l`
  if [ $num_vip -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl vip & 
    echo "start up a spider of vip at[`date`]"
    sleep 1
  fi

  #dangdang
  num_dangdang=`ps -ef | grep scrapy | grep "dangdang" | wc -l`
  if [ $num_dangdang -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl dangdang & 
    echo "start up a spider of dangdang at[`date`]"
    sleep 1
  fi

  #yhd
  num_yhd=`ps -ef | grep scrapy | grep "yhd" | wc -l`
  if [ $num_yhd -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl yhd & 
    echo "start up a spider of yhd at[`date`]"
    sleep 1
  fi

  #guomei
  num_guomei=`ps -ef | grep scrapy | grep "guomei" | wc -l`
  if [ $num_guomei -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl guomei & 
    echo "start up a spider of guomei at[`date`]"
    sleep 1
  fi

  #yamaxun
  num_yamaxun=`ps -ef | grep scrapy | grep "yamaxun" | wc -l`
  if [ $num_yamaxun -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl yamaxun & 
    echo "start up a spider of yamaxun at[`date`]"
    sleep 1
  fi

  #suning price
  num_pricesuning=`ps -ef | grep scrapy | grep "pricesuning" | wc -l`
  if [ $num_pricesuning -lt 0 ];then
    nohup /usr/bin/python2.7 /usr/bin/scrapy crawl pricesuning & 
    echo "start up a spider of pricesuning at[`date`]"
    sleep 1
  fi
  echo "monitor excute a scan at [`date`]"
  #sleep 60
#done


