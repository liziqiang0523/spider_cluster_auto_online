#对从09-17之后的所有item进行重新解析

datetime_wheres=()
minutes_all=6200
for ((minutes_ago=1000;minutes_ago<=${minutes_all};minutes_ago++))
do
  datetime_where=`date "-d ${minutes_ago} minutes ago" "+%Y-%m-%dT%H:%M"`
  datetime_wheres[$minutes_ago]=$datetime_where
done

for ((minutes_ago=${minutes_all};minutes_ago>=1000;minutes_ago--))
do
  while [ 2 -gt 1 ]
  do
    num=`ps -ef | grep startparser_datewhere.sh | wc -l`
    if [ $num -lt 60 ];then
      sh startparser_datewhere.sh ${datetime_wheres[$minutes_ago]} > log/startparse_$minutes_ago &
      echo "process concurrency..."
      sleep 1
      break
    else
      echo "sleep for a while"
      sleep 10
    fi
  done
done


