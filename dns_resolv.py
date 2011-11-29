#!/usr/bin/python -tt

import sys, socket, urlparse

if len(sys.argv) < 2:
  print """
Usage:
  dns_resolv.py -[i|h|u] file <domain>
Example:
  ./dns_resolv.py -h hostnames.lst domain.com
  ./dns_resolv.py -h fqdns.lst
  ./dns_resolv.py -i ips.lst
  ./dns_resolv.py -u urls.lst
  """
  sys.exit()

file = open(sys.argv[2], 'r')
mode = sys.argv[1][-1:]

if mode == 'h':
  names = file.read().split()
  for name in names:
    try:
      if len(sys.argv) > 3:
        domain = sys.argv[3]
        fqdn = name + '.' + domain
      else: fqdn = name
      ip = socket.gethostbyname(fqdn)
      print ip, name, fqdn
    except:
      continue

if mode == 'i':
  ips = file.read().split()
  for ip in ips:
    try:
      name = socket.gethostbyaddr(ip)
      print ip, name[0]
    except:
      continue

if mode == 'u':
  urls = file.read().split()
  for url in urls:
    try:
      url = urlparse.urlparse(url)[1]
      ip = socket.gethostbyname(url)
      print ip, url
    except:
      continue
