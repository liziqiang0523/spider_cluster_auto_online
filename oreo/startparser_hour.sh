#!/usr/bin/bash
#author:shiyuming
#启动解析器 对指定爬虫的指定日期下载的网页 进行解析；对指定日期的网页全部解析完成后，打个tar包，然后删除原始网页文件夹；
#所以在解析的时候，需要对这一天的网页启动所有的爬虫解析器来解析；在解析之前，要判断一下是否存在文件夹，如果不存在则要试试看是否存在文件夹的tar包并解压该tar包；
#同样的，打tar包前应该看看目录下是否tar包已经存在了，如果存在了，先mv换个名字，这样是为了避免开发时不小心删除了原始文件

hours_ago=$1
if [ $# -ne 1 ];then
  #默认解析1小时前的
  hours_ago=1
fi
datetime_dir=`date "-d ${hours_ago} hours ago" "+%Y_%m_%d"`
datetime_where=`date "-d ${hours_ago} hours ago" "+%Y-%m-%dT%H"`
hours_dir=`date "-d ${hours_ago} hours ago" +%-H`
echo "begin process pages of [$datetime_where]"

#在解析之前，要判断一下是否存在文件夹，如果不存在则要试试看是否存在文件夹的tar包并解压该tar包
pages_dir="/data/pages"
if [ ! -d ${pages_dir}/${datetime_dir}/$hours_dir/ ];then
  echo "pages文件夹[${pages_dir}/${datetime_dir}/$hours_dir/]不存在，尝试从tar包解压..."
  exit 0 #暂时取消解压功能
  if [ -f ${pages_dir}/${datetime_dir}/${hours_dir}.tar.bz2 ];then
    echo "tar包【${pages_dir}/${datetime_dir}/${hours_dir}.tar.bz2】存在，将从tar包解压..."
    cd $pages_dir/${datetime_dir}/
    tar -xjf ${hours_dir}.tar.bz2
    echo "tar包完成解压，解压数据："
    du -sh ${hours_dir} ${hours_dir}.tar.bz2
    cd -
  else
    echo "warning: tar包【${pages_dir}/${datetime_dir}/${hours_dir}.tar.bz2】也不存在，放弃对【$datetime_where】的解析"
    exit 1
  fi
else
  echo "pages文件夹[${pages_dir}/${datetime_dir}/${hours_dir}]存在. 开始解析..."
fi
#执行解析
echo "开始解析medicalaskse ..."
#/usr/local/bin/python2.7 oreo/parser/search4medical.py $datetime_where
echo "开始解析jd ..."
/usr/local/bin/python2.7 oreo/parser/jd.py $datetime_where
echo "开始解析ask120 ..."
/usr/local/bin/python2.7 oreo/parser/ask120.py $datetime_where
echo "开始解析one shop ..."
/usr/local/bin/python2.7 oreo/parser/one.py $datetime_where
echo "开始解析39ask ..."
/usr/local/bin/python2.7 oreo/parser/ask39.py $datetime_where
echo "开始解析douban ..."
/usr/local/bin/python2.7 oreo/parser/douban.py $datetime_where
echo "完成解析!"

exit 0

#压缩清理
cd $pages_dir/${datetime_dir}
if [ -f ${pages_dir}/${datetime_dir}/${hours_dir}.tar.bz2 ];then
  echo "tar包【${pages_dir}/${datetime_dir}/${hours_dir}.tar.bz2】已经存在，将给他改名为_bak"
  mv ${pages_dir}/${datetime_dir}/${hours_dir}.tar.bz2 ${pages_dir}/${datetime_dir}/${hours_dir}.tar.bz2_bak
fi
echo "开始压缩文件夹..."
tar -cjf ${hours_dir}.tar.bz2 ${hours_dir}
if [ $? -eq 0 ];then
  size_raw=`du -sh ${pages_dir}/${datetime_dir}/${hours_dir} | awk '{print $1}'`
  size_tar=`du -sh ${pages_dir}/${datetime_dir}/${hours_dir}.tar.bz2 | awk '{print $1}'`
  echo "完成对【${pages_dir}/${datetime_dir}/${hours_dir}】的网页的压缩存储 压缩前size[${size_raw}] 压缩后tar包size[${size_tar}]，6秒后开始执行删除..."
  sleep 6
  rm -rf ${pages_dir}/${datetime_dir}/${hours_dir}
  echo "完成删除【${pages_dir}/${datetime_dir}/${hours_dir}】"
else
  echo "warning: 压缩文件夹/${page_dir}/${datetime_dir}/{hours_dir}失败!"
  exit 1
fi

echo "process Done!"
