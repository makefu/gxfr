#!/usr/bin/python -tt

import time, logging
#logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *

def sniffmgmt(pkt):
  blocked = False
  domain = pkt[DNSQR].qname[:-1]
  reqip = pkt[IP].src
  for blacklist in blacklists.keys():
    if blocked: break
    for item in blacklists[blacklist]:
      if domain.find(item) != -1:
        block(pkt, ip)
        log(request_log, 'DENY', '%s -> %s [%s]' % (reqip, domain, blacklist))
        blocked = True
        break
  if not blocked:
    log(request_log, 'ALLOW', '%s -> %s' % (reqip, domain))

def log(filename, action, desc):
  stamp = time.strftime('%m:%d:%y %H:%M:%S', time.localtime())
  log_file = open(filename, 'a')
  log_file.write('%s (%s) %s\n' % (stamp, action, desc))
  log_file.close()

def block(pkt, ip):
  ethlen = len(Ether())
  iplen = len(IP())
  udplen = len(UDP())
  m = pkt
  t = str(m)
  e = Ether(t[:ethlen])
  i = IP(t[ethlen:])
  u = UDP(t[ethlen + iplen:])
  d = DNS(t[ethlen + iplen + udplen:])
  dpkt = response(d, ip)
  f = IP(src=i.dst, dst=i.src)/UDP(sport=u.dport, dport=u.sport)/dpkt
  #import pdb; pdb.set_trace()
  send(f, verbose=0)

def response(dr, ip):
  timetolive = '\x00\x00\x07\x75'
  alen = '\x00\x04'
  d = DNS()
  d.id = dr.id
  d.qr = 1
  d.opcode = 16
  d.aa = 0
  d.tc = 0
  d.rd = 0
  d.ra = 1
  d.z = 8
  d.rcode = 0
  d.qdcount = 1
  d.ancount = 1
  d.nscount = 0
  d.arcount = 0
  d.qd = str(dr.qd)
  d.an = str(dr.qd) + timetolive + alen + inet_aton(ip)
  return d

if __name__ == '__main__':

  ### set these vars ###
  ip = '127.0.0.1'  # sinkhole ip
  request_log = '/root/log'
  block_files = ['/root/blacklist']
  nameserver = '208.67.222.222'
  ######################

  # create list of blacklisted hosts in memory
  blacklists = {}
  for filename in block_files:
    print 'Processing %s...' % (filename)
    file = open(filename, 'r')
    blacklists[filename] = file.read().split()
    file.close()

  print 'Server started.'

  try:
    sniff(filter='udp dst port 53', prn=sniffmgmt, store=0)
  except KeyboardInterrupt:
    print 'Exiting...'
