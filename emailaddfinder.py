#!/usr/bin/python -tt

# add counter for total, success, error requests

import re, urllib, urllib2, sys, time, os

def search(type, url):
  try:
    request = urllib2.Request(url)
    requestor = urllib2.build_opener()
    request.addheaders = [('User-agent', 'Mozilla/5.0')]
    content = requestor.open(request).read()
    if verbose: print '[+] Processed %s[%s]: %s' % (type, len(content), url)
    #if type == 'URL': print content
  except:
    print '[Error] %s' % (url)
    content = ' '
  return content

company = sys.argv[1]
googledepth = '*'
addsearch = ''
verbose = False
tofile = False

for i in range(2,len(sys.argv),1):
  if sys.argv[i] == '-g':
    googledepth = sys.argv[i+1]
  elif sys.argv[i] == '-s':
    addsearch = sys.argv[i+1]
  elif sys.argv[i] == '-v':
    verbose = True
  elif sys.argv[i] == '-o':
    tofile = True
    filename = sys.argv[i+1]

if tofile:
  if os.path.exists(filename):
    file = open(filename, 'a')
  else:
    file = open(filename, 'w')

links = []
index = 0

while True:
  try:
    if googledepth != '*':
      if index >= int(googledepth):
        break
    #import pdb; pdb.set_trace()
    url = 'https://www.google.com/m/search?start=%s&q="%s"%s' % (str(index*10), company, addsearch)
    result = search('URL', url)
    links = re.findall('(?:href|u)="*((?:http|https)://[\w/\.\+=&;%-]+)"*', result)
    links = list(set(links))
    print links
    for link in links:
      if link.find('google.com') == -1:
        content = search('Link', link) + result
        addresses = re.findall('([\.\w-]+(?:@|\[at\])(?:[\w]+\.)+[a-zA-Z]+)', content)
        for item in addresses:
          if item.endswith(company):
            print item
            if tofile:
              file.write(item + '\n')
              file.flush()
    if not 'Next page' in result:
      print ''
      print '[*] End of search results reached.'
      break
    index += 1
    time.sleep(15)
  except KeyboardInterrupt:
    print 'Exiting...'
    if tofile: file.close()
if tofile: file.close()
