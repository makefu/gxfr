#!/usr/bin/python -tt

# linkedin.py queries Google for LinkedIn profiles associated to the given company
# and confirms current employment by scraping and analyzing the profile page. It
# then reports back the users full name, possible email prefix, and job title.
#
# Code is based heavily on the core functionality of userpass.py by Mark Baggett.
# http://pauldotcom.com/userpass.py

import re, urllib, urllib2 

def search(q, start = 0):
  url = 'http://www.google.com/m/search?'
  query = urllib.urlencode({'q':q, 'start':start})
  global verbose
  if verbose: print "[Query]", url + query
  request = urllib2.Request(url + query)
  requestor = urllib2.build_opener()
  request.addheaders = [('User-agent', 'Mozilla/5.0')]
  content = requestor.open(request).read()
  return content

def printhelp():
  print """
Usage:
  ./linkedin.py 'Company Name' [options]
Options:
  -g [#]        - The number of google pages to parse looking for employees of the Company (default is indef)
  -s            - Additional search words
  -v            - Be verbose
  -o [filename] - Output to easily parsable file
Example:
  ./linkedin.py 'Company Name' -g 5 -o report
                 - Querying to a google depth of 5, searching for employees of company, and outputing results to a file.
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

if tofile: file = open(filename, 'w')
query = 'site:linkedin.com/in "' + company+ '" ' + addsearch
names_urls = []
records = []
index = 0
print ''
print '[*] Resolving employees using the following query:', query
print ''
print 'First Name'.ljust(15) + 'Last Name'.ljust(18) + 'Possible Email'.ljust(20) + 'Position'
print '=========='.ljust(15) + '========='.ljust(18) + '=============='.ljust(20) + '========'
while True:
  if googledepth != '*':
    if index >= int(googledepth):
      break
  result = search(query, index*10)
  names_urls = re.findall(';u=http://\www\.linkedin\.com/in/[a-zA-Z0-9/-]+.>[ |a-zA-Z0-9,.-]+', result)
  for token in names_urls:
    token = token.lower()
    names_array = token.split(">")
    url_array = names_array[0].split("=")
    url = url_array[1][:-1]
    name = names_array[1].split(" ")
    fname = name[0]
    lname = name[1]
    content = urllib.urlopen(url).read().split('\n')
    i = 0
    for item in content:
      # if current job exists
      if item.find('headline-title title') != -1:
        job = content[i+3]
        # if current job is named company
        if job.lower().find(company.lower()) != -1:
          record = fname.ljust(15) + lname.ljust(18) + fname[:1] + lname.ljust(19) + job.lstrip(' ')
          if not record in records:
            records.append(record)
            print record
            if tofile:
              file.write(fname + '|' + lname + '|' + fname[:1] + lname + '|' + job.lstrip(' ') + '\n')
              file.flush()
          else:
            if verbose: print '[Duplicate found]', fname, lname
          break
      i += 1
  index += 1
  if not 'Next page' in result:
    print ''
    print '[*] End of Google search results reached.'
    break
if tofile: file.close()
