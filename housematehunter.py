#!/usr/bin/env python

import os
import subprocess
import re
from friends import friends
from mac_add import mac_addresses
from multiprocessing.dummy import Pool as ThreadPool

'''cleans mac addresses by re-adding zeros'''
def mac_clean(mac):
    parts = mac.split(":")
    mac_final = ""
    for part in parts:
        if len(part) < 2:
            part = "0" + part
        mac_final += part + ":"
    return mac_final[:-1]

'''calls ifconfig and returns the text response'''
def ifconfig_response():
    return subprocess.check_output(['ifconfig'], shell=True)

''' finds the broadcast internet ip and sends out a single broadcast ping 
    (currently silently). Because not a lot of machines respond to broadcast
    pings, there are other slower ways that fewer devices ignore'''
def broadcast_ping(ifconfig_res):
    #starting with a broadcast ping
    [broadcast_ip] = re.findall( r'broadcast [0-9]+(?:\.[0-9]+){3}', ifconfig_res)

    internet_ip = re.findall( r'inet [0-9]+(?:\.[0-9]+){3}', ifconfig_res)
    print broadcast_ip
    
    if len(internet_ip) >= 2:
        internet_ip = internet_ip[1].split()[1]
    elif len(internet_ip) == 1:
        internet_ip = internet_ip[1].split()[1]

    broadcast_ip = broadcast_ip.split()[1]

    ## silent response, calls the ping with no terminal output because #annoying
    response = subprocess.check_output(["ping -c 1 " + broadcast_ip], shell=True)
    
    ## Binary response, prints to the terminal, if it's failing you can enable it
    # response = os.system("ping -c 1 " + broadcast_ip)
    # print response == response1

    # if response != 0:
    #   print "Broadcast ping failed"
    # else:
    return broadcast_ip

''' figure out which class license you're on: netmask inet 10.0.17.185 netmask 
    0xffff0000 four f's means class B, two f's means class A, six f's class C'''
def class_license(ifconfig_res):
    # print ifconfig_res
    internet = re.findall( r'netmask (.*) broadcast', ifconfig_res)
    if len(internet) == 1:
        if 'ffffff' in internet[0] or "255.255.255" in internet[0]: #or 255.255.255?
            return "C"
        elif 'ffff' in internet[0] or "255.255" in internet[0]:
            return "B"
        elif 'ff' or "255." in internet[0]:
            return "A"
    print "Class License not extracted"
    return None

'''find all ip's in your subnet (only works for class B and C because 
    you don't want arp 8 million addresses), arping's them so then they'll 
        be added to your arp table'''
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
    #   ping_thread(i)
    
    pool = ThreadPool(40)
    pool.map(ping_thread, ip_list)
    pool.close()
    pool.join()

''' Calls to the system a single ping directed at a specific ip address '''
def ping_thread(ip):
    ping = os.system("arping -c 1 " + ip)

''' look up arp table, find all mac addresses, put them in a dictionary 
    with the IP addresses as keys '''
def arp_lookup():
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
    return network_dict

''' looks up your known mac addresses and prints out who is home, their mac address
    and their current ip address'''
def friends_home(network_dict):
    #see who's home
    print "~~~~~~~~~Friends who are home~~~~~~~~~~~~"
    for friend in friends:
        friend = mac_clean(friend)
        if friend in network_dict:
            print friend +'\t'+ network_dict[friend] +'\t'+  friends[friend]

''' prints the contents of your arp table and what maker/manufacturer is associated
    with their mac address'''
def device_types(network_dict):
    print "~~~~~~~~~Device types on your network~~~~~~~~~~~~"
    for mac in network_dict:
        if mac[:8] in mac_addresses:
            print mac +'\t'+ network_dict[mac] +'\t'+ mac_addresses[mac[:8]]
        else:
            print "DON'T KNOW", mac

'''nmaps whatever subnet (last octect) you're on so you find all devices on your net'''
def nmap_subnet():
    pass


def main():
    ifconfig_res = ifconfig_response()

    class_lic = class_license(ifconfig_res)

    broadcast_ip = broadcast_ping(ifconfig_res)

    # individual_ping_network(broadcast_ip, class_lic)

    network_dict = arp_lookup()
    
    friends_home(network_dict)
    device_types(network_dict)

    ##Ideas

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
# ip = os.system("ifconfig | grep broadcast")
# response = os.system("arp -a")

# print "got it"
# print response
