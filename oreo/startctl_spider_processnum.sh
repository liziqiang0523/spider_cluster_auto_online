
#启动一个爬虫12
function start_one()
{
  if [ ! $# -eq 1 ];then
    echo "start a spider must input name!"
    return 1
  fi
  spidername=$1
  num=`ps -ef | grep scrapy | grep "crawl ${spidername}" | wc -l`
  if [ $num -lt ${process_num} ];then
    nohup /usr/local/bin/scrapy crawl ${spidername} &
    echo "start up a spider of ${spidername} at[`date`]"
  fi
}




while [ 2 -gt 1 ]
do
  spider_name=$1
  process_num=$2
  start_one $spider_name
  sleep 3 
done
