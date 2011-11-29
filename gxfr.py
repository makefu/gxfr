#!/usr/bin/python -tt

# gxfr replicates dns zone transfers by enumerating subdomains using advanced search engine queries and conducting dns lookups.
# By Tim Tomes (LaNMaSteR53)
# Available for download at http://LaNMaSteR53.com or http://code.google.com/p/gxfr/

import sys, os.path, urllib2, re, time, socket, random, socket

def help():
  print """  Syntax: ./gxfr.py domain [options]
  
  -h, --help               this screen
  -v                       enable verbose mode
  -t [num of seconds]      set number of seconds to wait between queries (default=5)
  -q [max num of queries]  restrict to maximum number of queries (default=0, indefinite)
  --no-encrypt             disable SSL encrypted search engine queries
  --dns-lookup             enable dns lookups of all subdomains
  --proxy [file|ip:port|-] use a proxy or list of open proxies to send queries (@random w/list)
                             - [file] must consist of 1 or more ip:port pairs
                             - replace filename with '-' (dash) to accept stdin
  --user-agent ['string']  set custom user-agent string
  --timeout [seconds]      set socket timeout (default=system default)
  
  Examples: 
  $ ./gxfr.py foxnews.com --no-encrypt --dns-lookup -t 5 -q 5 -v --proxy open_proxies.txt --timeout 10
  $ ./gxfr.py foxnews.com --no-encrypt --dns-lookup -t 5 -q 5 -v --proxy 127.0.0.1:8080
  $ curl http://rmccurdy.com/scripts/proxy/good.txt | ./gxfrpy foxnews.com -v --dns-lookup -t 5 -q 5 --proxy -
  """
  sys.exit(2)

if len(sys.argv) < 2:
  help()

if '-h' in sys.argv or '--help' in sys.argv:
  help()

# declare vars and process arguments
query_cnt = 0
domain = sys.argv[1]
sys.argv = sys.argv[2:]
lookup = False
encrypt = True
proto = 'https'
url = 'https://encrypted.google.com/search?q=inurl%3A' + domain + '+site%3A' + domain
proxy = False
user_agent = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
verbose = False
secs = 5
max_queries = 0 # infinite
# process command line arguments
if len(sys.argv) > 0:
  if '--dns-lookup' in sys.argv:
    lookup = True
  if '--no-encrypt' in sys.argv:
    encrypt = False
    proto = 'http'
    url = 'http://www.google.com/search?q=inurl%3A' + domain + '+site%3A' + domain
  if '--proxy' in sys.argv:
    proxy = True
    filename = sys.argv[sys.argv.index('--proxy') + 1]
    if filename == '-':
      proxies = sys.stdin.read().split()     
    elif os.path.exists(filename):
      content = open(filename).read()
      proxies = re.findall('\d+\.\d+\.\d+\.\d+:\d+', content)
    elif re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', filename):
      proxies = [filename]
    else:
      help()
  if '--timeout' in sys.argv:
    timeout = int(sys.argv[sys.argv.index('--timeout') + 1])
    socket.setdefaulttimeout(timeout)
  if '--user-agent' in sys.argv:
    user_agent = sys.argv[sys.argv.index('--user-agent') + 1]  
  if '-v' in sys.argv:
    verbose = True
  if '-t' in sys.argv:
    secs = int(sys.argv[sys.argv.index('-t') + 1])
  if '-q' in sys.argv:
    max_queries = int(sys.argv[sys.argv.index('-q') + 1])
pattern = '<cite>[\w://]*?([\w\.-]+?)<b>' + domain + '</b>'
subs = []
new = True

# --begin--
print '[-] domain:', domain
print '[-] user-agent:', user_agent
# execute search engine queries and scrape results storing subdomains in a list
print '[-] querying search engine, please wait...'
# loop until no new subdomains are found
while new == True:
  query = ''
  # build query based on results of previous results
  for sub in subs:
    query += '+-site:' + sub + domain
  new_url = url + query
  new_url = new_url[:2074]
  # build web request and submit query
  request = urllib2.Request(new_url)
  # spoof user-agent string
  request.add_header('User-Agent', user_agent)
  # if proxy is enabled, use the correct handler
  if proxy == True:
    # validate proxies at runtime
    while True:
      try:
        # select a proxy from list at random
        num = random.randint(0,len(proxies)-1)
        host = proxies[num]
        opener = urllib2.build_opener(urllib2.ProxyHandler({proto: host}))
        if verbose: print '[+] sending query to', host
        # send query to proxy server
        result = opener.open(request).read()
        # exit while loop if successful
        break
      except Exception as inst:
        print '[!] {0} failed: {1}'.format(host, inst)
        if len(proxies) == 1:
          # exit of no proxy servers from list are valid
          print '[-] valid proxy server not found'
          sys.exit(2)
        else:
          # remove host from list of proxies and try again
          del proxies[num]
  else:
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
    if verbose: print '[+] sending query...'
    # send query to search engine
    try:
      result = opener.open(request).read()
    except Exception as inst:
        print '[!] {0}'.format(inst)
        if str(inst).index('503') != -1: print '[!] possible shun: use --proxy or find something else to do for 24 hours :)'
        sys.exit(2)
  # iterate query count
  query_cnt += 1
  sites = re.findall(pattern, result)
  # create a uniq list
  sites = list(set(sites))
  new = False
  # add subdomain to list if not already exists
  for site in sites:
    if site not in subs:
      if verbose: print '[!] subdomain found:', site
      subs.append(site)
      new = True
  # exit if all subdomains have been found
  if new == False:
    print '[-] all available subdomains found...'
    break
  # exit if maximum number of queries has been made
  if query_cnt == max_queries:
    print '[-] maximum number of queries made...'
    break
  # sleep script to avoid lock-out
  if verbose: print '[+] sleeping to avoid lock-out...'
  time.sleep(secs)

# print list of subdomains
print '[-] successful queries made:', str(query_cnt)
if verbose:
  # rebuild and display final query if in verbose mode
  final_query = ''
  for sub in subs:
    final_query += '+-site:' + sub + domain
  print '[+] final query string:', url + final_query
print ' '
print '[subdomains] -', str(len(subs))
for sub in subs: print sub + domain

# conduct dns lookup if argument is present
if lookup == True:
  print ' '
  print '[-] querying dns, please wait...'
  dict = {}
  # create a dictionary where the subdomain is the key and a list of all associated ips is the value
  for sub in subs:
    sub = sub + domain
    if verbose: print '[+] querying dns for', sub + '...'
    # dns query and dictionary assignment
    try:
      dict[sub] = list(set([item[4][0] for item in socket.getaddrinfo(sub, 80)]))
    except socket.gaierror:
      # dns lookup failure
      dict[sub] = list(set(['no entry']))
  # print table of subdomains and ips
  print ' '
  print '[ip]'.ljust(16, ' ') + '[subdomain]'
  for key in dict.keys():
    for ip in dict[key]:
      print ip.ljust(16, ' ') + key
# --end--
