#!/usr/bin/python -tt

import sys, socket, time, os
from threading import Thread
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

### set these vars ###
ip = '192.168.1.3'                                    # ip of listening interface
logfile = '/root/tools/dns_fwd/log'                   # full path to log file. over-ride with -l switch
bl_path = '/root/tools/dns_fwd/blacklists/'           # full path to directory containing blacklists
nameserver = '208.67.222.222'                         # ip of upstream dns server
######################

toLog = False
for i in range(1, len(sys.argv), 1):
  if sys.argv[i] == '-l':
    toLog = True
    print 'Logging to file: %s.' % (logfile)
    if len(sys.argv)-1 > i:
      if not sys.argv[i+1].startswith('-'):
        logfile = sys.argv[i+1]

class customHTTPServer(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write('<html><body>Blocked!</body></html>')
    return

  def log_message(self, format, *args):
    return

class DNSQuery:
  def __init__(self, data):
    self.data = data
    self.domain = ''

    type = (ord(data[2]) >> 3) & 15   # Opcode bits
    if type == 0:                     # Standard query
      ini=12
      lon=ord(data[ini])
      while lon != 0:
        self.domain+=data[ini+1:ini+lon+1]+'.'
        ini+=lon+1
        lon=ord(data[ini])

  def response(self, ip):
    packet=''
    packet+=self.data[:2] + "\x81\x80"
    packet+=self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Questions and Answers Counts
    packet+=self.data[12:]                                         # Original Domain Name Question
    packet+='\xc0\x0c'                                             # Pointer to domain name
    packet+='\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'             # Response type, ttl and resource data length -> 4 bytes
    packet+=str.join('',map(lambda x: chr(int(x)), ip.split('.'))) # 4bytes of IP
    return packet

  def forward(self, nameserver):
    fwds = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fwds.settimeout(3)
    fwds.sendto(self.data, (nameserver, 53))
    response, addr = fwds.recvfrom(1024)
    fwds.close()
    return response

def log(action, desc):
  if toLog:
    stamp = time.strftime('%m:%d:%y %H:%M:%S', time.localtime())
    log_file = open(logfile, 'a')
    log_file.write('%s (%s) %s\n' % (stamp, action, desc))
    log_file.close()

def serve():
  try:
    server = HTTPServer((ip,80), customHTTPServer)
    server.serve_forever()
  except KeyboardInterrupt:
    server.socket.close()

## begin ##
#import pdb; pdb.set_trace()

print 'Starting web server on %s...' % (ip)
t = Thread(target=serve, args=())
t.setDaemon(True)
t.start()

print 'Forwarding requests to %s.' % (nameserver)

# create list of blacklisted hosts in memory
blacklists = {}
dirList = os.listdir(bl_path)
for filename in dirList:
  path = bl_path + filename
  print 'Processing %s...' % (path)
  file = open(path, 'r')
  blacklists[filename] = file.read().split()
  file.close()

udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udps.bind((ip,53))
print 'Server started.'
  
try:
  while 1:
    blocked = False
    reqdata, reqaddr = udps.recvfrom(1024)
    p = DNSQuery(reqdata)
    domain = p.domain[:-1]
    for blacklist in blacklists.keys():
      if blocked: break
      for item in blacklists[blacklist]:
        if domain.find(item) != -1:
          udps.sendto(p.response(ip), reqaddr)
          log('DENY', '%s -> %s [%s]' % (reqaddr[0], domain, blacklist))
          blocked = True
          break
    if not blocked:
      try:
        udps.sendto(p.forward(nameserver), reqaddr)
        log('ALLOW', '%s -> %s' % (reqaddr[0], domain))
      except socket.timeout:
        log('ERROR', '%s -> %s [fwd_socket_timeout]' % (reqaddr[0], domain))
        continue
except KeyboardInterrupt:
  print 'Exiting...'
  udps.close()

## end ##
