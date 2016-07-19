#!/usr/bin/env python

import os
import subprocess
import re
from friends import friends
from multiprocessing.dummy import Pool as ThreadPool

def mac_clean(mac):
	parts = mac.split(":")
	mac_final = ""
	for part in parts:
		if len(part) < 2:
			part = "0" + part
		mac_final += part + ":"
	return mac_final[:-1]

def ifconfig_response():
	return subprocess.check_output(['ifconfig'], shell=True)

def broadcast_ping(ifconfig_res):
	#starting with a broadcast ping
	[broadcast_ip] = re.findall( r'broadcast [0-9]+(?:\.[0-9]+){3}', ifconfig_res)

	internet_ip = re.findall( r'inet [0-9]+(?:\.[0-9]+){3}', ifconfig_res)
	
	if len(internet_ip) >= 2:
		internet_ip = internet_ip[1].split()[1]
	elif len(internet_ip) == 1:
		internet_ip = internet_ip[1].split()[1]

	broadcast_ip = broadcast_ip.split()[1]

	response = subprocess.check_output(["ping -c 1 " + broadcast_ip], shell=True)
	# response = os.system("ping -c 1 " + broadcast_ip)
	# print response == response1

	# if response != 0:
	# 	print "Broadcast ping failed"
	# else:
	return broadcast_ip

def class_license(ifconfig_res):
	# print ifconfig_res
	internet = re.findall( r'netmask (.*) broadcast', ifconfig_res)
	if len(internet) == 1:
		if 'ffffff' in internet[0]:
			return "C"
		elif 'ffff' in internet[0]:
			return "B"
		elif 'ff' in internet[0]:
			return "A"
	print "Class License not extracted"
	return None

#individual pings
#find all ip's in your subnet, arp them (so then they'll be added to your arp table)
def individual_ping_network(broadcast_ip, class_lic):
	ip_parts = broadcast_ip.split(".")
	print ip_parts
	ip_list = []
	for i in xrange(0,255):
		if class_lic == "C":
			ip = ip_parts[0]+"."+ip_parts[1]+"."+ip_parts[2]+"."+str(i)
			ip_list.append(ip)
		elif class_lic == "B":
			for j in xrange(0,255):
				ip = ip_parts[0]+"."+ip_parts[1]+"."+str(i)+"."+str(j)
				ip_list.append(ip)
	
	# for i in ip_list:
	# 	ping_thread(i)
	
	pool = ThreadPool(40)
	pool.map(ping_thread, ip_list)
	pool.close()
	pool.join()

def ping_thread(ip):
	ping = os.system("arping -c 1 " + ip)

def arp_lookup():
	#look up arp table, find all mac addresses
	arp_response = subprocess.check_output(['arp -an'], shell=True)
	network_machines = arp_response.split("\n")

	network_dict = {}

	for machine in network_machines:
		machine = machine.strip("? ")
		machine = machine.strip("")
		ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', machine)
		mac = re.findall("at (.*?) on", machine)
		if ip != [] and mac != []:
			[ip] = ip
			[mac] = mac
			mac = mac_clean(mac)		
			# print ip, mac
			network_dict[mac] = ip

	#see who's home
	print "~~~~~~~~~Friends who are home~~~~~~~~~~~~"
	for friend in friends:
		friend = mac_clean(friend)
		if friend in network_dict:
			print friends[friend], network_dict[friend]


def main():
	ifconfig_res = ifconfig_response()

	class_lic = class_license(ifconfig_res)

	broadcast_ip = broadcast_ping(ifconfig_res)
	class_lic = "C"
	# individual_ping_network(broadcast_ip, class_lic)
	arp_lookup()

	#figure out which class license you're on: netmask inet 10.0.17.185 netmask 0xffff0000 four f's means class B, two f's means class A, six f's class C

	#look up netaddr

	#network address translation

	#

if __name__ == '__main__':
	main()

# look inside proc/net/arp (the file that stores MAC addresses in the kernel arp = address resolution protocol)

# extract HW/MAC address as strings

# keep a dictionary of MAC addresses, check MAC addresses against extracted ones

# ping MAC address to see if they are currently connected

# arping works better (have to reply, more reliable)

# if you want to do it remotely, you need to have a device on the network - i.e. a raspberry pi or something similar


# ----------

# ip = re.search('^broadcast:(.*)', ifconfig_response).groups()

# print ip

# hostname = "google.com" #example
# my_ip = "10.0.255.255"
# marielle_mac = "b8:e8:56:38:74:2"
# ip = os.system("ifconfig | grep broadcast")
# response = os.system("arp -a")

# print "got it"
# print response
