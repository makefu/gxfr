#!/usr/bin/python -tt

# linkedin.py queries Google for LinkedIn profiles associated to the given company
# and confirms current employment by scraping and analyzing the profile page. It
# then reports back the users full name, possible email prefix, and job title.
#
# Code is based heavily on the core functionality of userpass.py by Mark Baggett.
# http://pauldotcom.com/userpass.py

import re, urllib, urllib2, time, traceback, htmllib, sqlite3

def search(q, start = 0):
  try:
    content = ''
    url = 'http://www.google.com/m/search?'
    query = urllib.urlencode({'q':q, 'start':start})
    global verbose
    if verbose: print '[Query] %s%s' % (url, query)
    request = urllib2.Request(url + query)
    requestor = urllib2.build_opener()
    request.addheaders = [('User-agent', 'Mozilla/5.0')]
    content = requestor.open(request).read()
  except KeyboardInterrupt:
    pass
  except:
    print '-'*60
    traceback.print_exc(file=sys.stdout)
    print '-'*60
  return content

def unescape(s):
  p = htmllib.HTMLParser(None)
  p.save_bgn()
  p.feed(s)
  return p.save_end()

def printhelp():
  print """
Usage:
  ./linkedin.py 'Company Name' [options]
Options:
  -g [#]        - The number of google pages to parse looking for employees of the Company (default is indef)
  -s            - Additional search words
  -v            - Be verbose
  -o [filename] - Output or append to sqlite3 database
Example:
  ./linkedin.py 'Company Name' -g 5 -o report.db
                 - Querying to a google depth of 5, searching for employees of company, and outputting results to a db.
  """

import os, sys

if '-h' in sys.argv or len(sys.argv)<2:
  printhelp()
  sys.exit(2)

company = sys.argv[1]
googledepth = '*'
addsearch = ''
verbose = False
tofile = False
delay = 10

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
  # initialize the database
  con = sqlite3.connect(filename)
  cur = con.cursor()
  cur.execute('create table if not exists targets (fname text, lname text, title text)')
  con.commit()

query = 'site:linkedin.com "%s" %s' % (company, addsearch)
#query = 'site:linkedin.com/in "%s" %s' % (company, addsearch)
index = 0
print ''
print '[*] Resolving employees using the following query:', query
print ''
print 'First Name'.ljust(15) + 'Last Name'.ljust(18) + 'Title'
print '=========='.ljust(15) + '========='.ljust(18) + '====='
try:
  while True:
    if googledepth != '*':
      if index >= int(googledepth):
        break
    result = search(query, index*10)
    names_urls = re.findall(";u=http://\www\.linkedin\.com/[a-zA-Z0-9/-]+.>[ |a-zA-Z0-9,.-]+", result)
    #names_urls = re.findall(";u=http://\www\.linkedin\.com/in/[a-zA-Z0-9/-]+.>[ |a-zA-Z0-9,.-]+", result)
    for token in names_urls:
      token = token.lower()
      url = token.split(">")[0].split("=")[1][:-1]
      content = urllib.urlopen(url).read().split('\n')
      i = 0
      fname = ''
      lname = ''
      for item in content:
        try:
          # get the first and last names
          if item.find('class="full-name"') != -1:
            #import pdb; pdb.set_trace()
            m = re.search('given-name">(.+?)<.+family-name">(.+?)<', item)
            fname = unescape(m.group(1))
            lname = unescape(m.group(2))
          # get current job title
          elif item.find('headline-title title') != -1:
            job = unescape(content[i+3])
            # if current job is named company
            if job.lower().find(company.lower()) != -1:
              if tofile:
                cur.execute('insert into targets values (?,?,?)', (fname,lname,job))
                con.commit()
              print fname.ljust(15) + lname.ljust(18) + job.lstrip(' ')
            break
          i += 1
        except:
          print '-'*60
          traceback.print_exc(file=sys.stdout)
          print '-'*60
          print '[Notice] Skipping %s. Confirm manually.' % (token)
          continue
    if not 'Next page' in result:
      print '\n[*] End of search results reached.'
      break
    index += 1
    time.sleep(delay)
except KeyboardInterrupt:
  pass
print '\nExiting...'
if tofile:
  cur.close()
  con.close()
