#!/bin/bash
#author:shiyuming
#每分钟对上一分钟的抓取内容进行压缩，压缩后删除原文件

pages_dir="/data/pages"

function compress_and_clean()
{
  minutes_ago=$1
  if [ "$minutes_ago" == "" ];then
    minutes_ago=1
    echo "default compress minutes:$minutes_ago"
  else
    echo "get compress minutes:$minutes_ago"
  fi
  dt_day=`date "-d ${minutes_ago} minutes ago" "+%Y_%m_%d"`
  dt_hour=`date "-d ${minutes_ago} minutes ago" "+%-H"`
  dt_minute=`date "-d ${minutes_ago} minutes ago" "+%-M"`
  dir_datetime="${pages_dir}/${dt_day}/${dt_hour}"
  echo "dir_datetime:$dir_datetime"

  #do compress
  if [ ! -d $dir_datetime/${dt_minute} ];then
    echo "dir:$dir_datetime/${dt_minute} not exists! exit with 1"
    return 1
  fi
  cd $dir_datetime
  if [ -f ${dt_minute}.tar.bz2 ];then
    echo "tar-file $dir_datetime/${dt_minute}.tar.bz2 is exists. exit with 0"
    return 0
  fi
  echo "begin compress..."
  tar -cjf ${dt_minute}.tar.bz2 ${dt_minute}/
  if [ $? -eq 0 ];then
    size_raw=`du -sh ${dt_minute}/`
    size_tar=`du -sh ${dt_minute}.tar.bz2`
    echo "compress SUC. size_raw[$size_raw] size_tar[$size_tar]. being to delete raw file ..."
    rm -rf ${dir_datetime}/${dt_minute}
    echo "delete ${dir_datetime}/${dt_minute} SUC!"
    return 0
  else
    echo "warning: compress file[$dt_minute] failed!"
    return 1
  fi
}

compress_and_clean 95
