#!/bin/bash

# set variables
SWINT=eth3
BRINT=br0
COMPINT=eth2
ARPS=50 # if needed
TCP=88 # if needed

echo [*] Building interface bridge...
brctl addbr $BRINT
brctl addif $BRINT $COMPINT
brctl addif $BRINT $SWINT

echo [*] Bringing up interfaces...
ifconfig $COMPINT 0.0.0.0 up promisc
ifconfig $SWINT 0.0.0.0 up promisc
ifconfig $BRINT 0.0.0.0 up promisc

# sleeping to let things settle a tad
sleep 5

mii-tool -r $COMPINT
mii-tool -r $SWINT

echo [*] Getting info from traffic...
# get variables using arp
tcpdump -i $COMPINT -s0 -w boot.pcap -c$ARPS arp
echo [*] Done receiving traffic. Processing...
GWMAC=`tcpdump -r boot.pcap -nne | grep 'is-at' | awk '{ print $2 "," $4  $11 "," $13}' | sort | uniq -c | sort -rn | head -1 | awk -F ',' '{print $4}'`
GWIP=`tcpdump -r boot.pcap -nne | grep 'is-at' | awk '{ print $2 "," $4  $11 "," $13}' | sort | uniq -c | sort -rn | head -1 | awk -F ',' '{print $3}'`
COMPMAC=`tcpdump -r boot.pcap -nne | grep 'is-at' | awk '{ print $2 "," $4  $11 "," $13}' | sort | uniq -c | sort -rn | head -1 | awk -F ',' '{print $2}'`
COMPIP=`tcpdump -r boot.pcap -nne | grep $COMPMAC | grep -w "$GWIP tell"| head -1 | awk '{print $14}' | cut -d, -f 1`

# grab a single tcp port 88, 135, 445 packet destined for the DC (kerberos)
#tcpdump -i $COMPINT -s0 -w boot.pcap -c1 tcp dst port $TCP
#echo [*] Done receiving traffic. Processing...
#COMPMAC=`tcpdump -r boot.pcap -nne -c 1 tcp dst port $TCP | awk '{print $2}'`
#COMPIP=`tcpdump -r boot.pcap -nne -c 1 tcp dst port $TCP | awk '{print $10}' | cut -d. -f 1-4`
#GWMAC=`tcpdump -r boot.pcap -nne -c 1 tcp dst port $TCP | awk '{print $4}' | cut -d, -f 1`
#GWIP=`tcpdump -r boot.pcap -nne -c 1 tcp dst port $TCP | awk '{print $12}' | cut -d. -f 1-4`

echo [*] Bringing down bridge...
ifconfig $BRINT down
brctl delif $BRINT $COMPINT
brctl delif $BRINT $SWINT

echo =============================
echo Marvin Settings
echo =============================
echo BRIF1.INTERFACE: $COMPINT
echo BRIF1.SMAC:      $GWMAC
echo BRIF1.SADDR:     $GWIP
echo =============================
echo BRIF2.INTERFACE: $SWINT
echo BRIF2.SMAC:      $COMPMAC
echo BRIF2.SADDR:     $COMPIP
echo =============================
echo BR.GATEWAY:      $GWIP
echo =============================
echo TAPIF.INTERFACE: $BRINT
echo =============================

# building marvin.conf file to use with './marvin.sh -f marvin.conf'

rm marvin.conf
echo brif1.interface=$COMPINT >> marvin.conf
echo brif1.smac=$GWMAC >> marvin.conf
echo brif1.saddr=$GWIP >> marvin.conf
echo brif2.interface=$SWINT >> marvin.conf
echo brif2.smac=$COMPMAC >> marvin.conf
echo brif2.saddr=$COMPIP >> marvin.conf
echo br.netmask=255.255.255.0 >> marvin.conf
echo br.gateway=$GWIP >> marvin.conf
echo tapif.interface=$BRINT >> marvin.conf
echo tapif.MACr=aa:bb:cc:dd:ee:ff >> marvin.conf
echo tapif.IPr=10.0.0.1 >> marvin.conf

echo 1. Validate br.netmask
echo 2. Configure tap client with:
echo    address: 10.0.0.2
echo    netmask: 255.255.255.0
echo    gateway: 10.0.0.1
echo 3. Run marvin with './marvin.sh -f marvin.conf'
