#coding=utf-8
#author:shiyuming

import sys
import numpy

class Viewer:
  def __init__(self):
    self.last_runtime = ''
    self.speed = {self.last_runtime:0}

  def process(self, line):
    runtime = line[:16]
    self.speed.setdefault(runtime, 0)
    self.speed[runtime] += 1
    if self.last_runtime != runtime:
      print 'speed of [%s] is : [%d/minute]' % (self.last_runtime, self.speed[self.last_runtime])
    self.last_runtime = runtime
    self.speed[runtime] += 1

  def statistic(self):
    speeds = [v for k,v in self.speed.items()]
    print '均速：%s/每分钟 中位数:%s/每分钟 最大值:%s/每分钟' % (numpy.average(speeds), numpy.median(speeds), numpy.max(speeds))

if __name__ == "__main__":
  viewer = Viewer()
  for line in sys.stdin:
    viewer.process(line)
  viewer.statistic()
      
