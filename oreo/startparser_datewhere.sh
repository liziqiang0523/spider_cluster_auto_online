#!/usr/bin/bash
#author:shiyuming
#启动解析器 对指定爬虫的指定日期下载的网页 进行解析；对指定日期的网页全部解析完成后，打个tar包，然后删除原始网页文件夹；
#所以在解析的时候，需要对这一天的网页启动所有的爬虫解析器来解析；在解析之前，要判断一下是否存在文件夹，如果不存在则要试试看是否存在文件夹的tar包并解压该tar包；
#同样的，打tar包前应该看看目录下是否tar包已经存在了，如果存在了，先mv换个名字，这样是为了避免开发时不小心删除了原始文件

pages_dir="/data/pages"
function parse()
{
  datetime_where=$1
  dt_day=`echo $datetime_where | awk -F'T' '{print $1}' | sed s/-/_/g`
  dt_hour=`echo $datetime_where | awk -F'T' '{print $2}' | awk -F':' '{print $1}' | sed s/^0//g`
  dt_minute=`echo $datetime_where | awk -F'T' '{print $2}' | awk -F':' '{print $2}' | sed s/^0//g`
  dir_datetime="${pages_dir}/${dt_day}/${dt_hour}"
  echo "input:$datetime_where dt_day:$dt_day dt_hour:$dt_hour dt_minute:$dt_minute dir_datetime:$dir_datetime"

  #do parse
  cd $dir_datetime
  if [ ! -d $dir_datetime/${dt_minute} ];then
    echo "dir:$dir_datetime/${dt_minute} not exists. tend to decompress."
    if [ ! -f ${dt_minute}.tar.bz2 ];then
      echo "tar-file $dir_datetime/${dt_minute}.tar.bz2 is not exists. exit with 1"
      return 1
    else
      echo "begin to decompress tar-file ${dt_minute}.tar.bz2..."
      tar -xjf ${dt_minute}.tar.bz2
      if [ $? -ne 0 ];then
        echo "tar -xjf ${dt_minute}.tar.bz2 failed!"
        return 1
      fi
    fi
  fi
  cd -
  file_num=`ls $dir_datetime/${dt_minute} | wc -l`
  echo "begin parse $dir_datetime/${dt_minute} file_num:${file_num}..."
  #执行解析
  #echo "开始解析ask120 ..."
  #/usr/bin/python2.7 oreo/parser/ask120.py $datetime_where
  #echo "开始解析jd ..."
  #/usr/bin/python2.7 oreo/parser/jd.py $datetime_where
  #echo "开始解析39ask ..."
  #/usr/bin/python2.7 oreo/parser/ask39.py $datetime_where
  echo "开始解析dangdang ..."
  /usr/bin/python2.7 oreo/parser/dangdang.py $datetime_where
  echo "开始解析 dangdang..."
  /usr/bin/python2.7 oreo/parser/dangdang.py $datetime_where
  echo "开始解析 douban..."
  /usr/bin/python2.7 oreo/parser/douban.py $datetime_where
  echo "开始解析 guomei..."
  /usr/bin/python2.7 oreo/parser/guomei.py $datetime_where
  echo "开始解析 suning..."
  /usr/bin/python2.7 oreo/parser/suning.py $datetime_where
  echo "开始解析 vip..."
  /usr/bin/python2.7 oreo/parser/vip.py $datetime_where
  echo "开始解析 yamaxun..."
  /usr/bin/python2.7 oreo/parser/yamaxun.py $datetime_where
  echo "开始解析 yhd..."
  /usr/bin/python2.7 oreo/parser/yhd.py $datetime_where
  echo "完成解析!"

  echo "完成解析 删除raw文件$dir_datetime/${dt_minute}..." 
  sleep 6
  rm -rf $dir_datetime/${dt_minute}
}

#dt_where=`date "-d 1850 minutes ago" "+%Y-%m-%dT%H:%M"`
parse $1
