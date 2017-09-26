#!/bin/bash
#kill 掉1小时前的爬虫进程

cur_h=`date +%-H`
cur_m=`date +%-M`
if [ $cur_h -lt 1 ]
then
  exit 0
fi

echo "now: ${cur_h}:${cur_m}"
pids=`ps -ef | grep scrapy | awk '{print $5"\t"$2}' | awk -F':' -v t_h=$cur_h -v t_m=$cur_m '{ minute=t_m-$2; hour=t_h-$1; minutes=minute+hour*60; if(minutes >50){ print $0; } }' | awk '{print $NF}'`

for pid in $pids
do
  pidinfo=`ps -ef | grep scrapy | grep $pid`
  echo "now need to kill pid:$pidinfo"
  kill -9 $pid
done

exit 0
