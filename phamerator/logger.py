#!/usr/bin/env python

import time

class logger:
  def __init__(self, shouldLog):
    self.shouldLog = shouldLog
  def log(self, string):
    if self.shouldLog:
      now = time.localtime(time.time())
      print time.strftime("%m/%d/%y %H:%M:%S:", now), string

