#!/usr/bin/python -tt

# List all followers for a given twitter user via twitter api
# 150 max queries per hour

import urllib2, re, sys, Queue, threading

url = 'http://api.twitter.com:80/1/followers/ids.json?screen_name=' + sys.argv[1]
resp = urllib2.urlopen(url)
content = resp.read()
if resp.code == 200:
  ids = content.split(']')
  ids = ids[0].split('[')
  ids = ids[1].split(',')
else:
  print resp.code
  sys.exit(2)
resp.close()

screen_names = []
q = Queue.Queue()

def doWork():
  while True:
    try:
      id = q.get()
      url = 'http://api.twitter.com/1/users/lookup.json?user_id=' + id
      resp = urllib2.urlopen(url)
      content = resp.read()
      screen_name = re.findall('"screen_name.+?"(\S+?)",', content)
      screen_names.append(screen_name[0])
      q.task_done()
    except:
      print 'ERROR:', id

for i in range(10):
  t = threading.Thread(target=doWork)
  t.daemon = True
  t.start()

try:
  for id in ids:
    q.put(id)
  q.join()
  for name in screen_names:
    print name
except KeyboardInterrupt:
  sys.exit(2)
