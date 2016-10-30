#!/usr/bin/env python

"""
By Marielle Foster, July 2016
Inspiration from Paul Fenwick

If you want to use it remotely, you need to have a device on the network
- i.e. a raspberry pi or something similar
"""


import os
import subprocess
import re
import argparse
from multiprocessing.dummy import Pool as ThreadPool
from __future__ import print_function

from friends import friends
from mac_add import mac_addresses


def mac_clean(mac):
    '''Cleans mac addresses by re-adding zeros.'''
    parts = mac.split(":")
    mac_final = ""
    for part in parts:
        if len(part) < 2:
            part = "0" + part
        mac_final += (part + ":")
    return mac_final[:-1]


def ifconfig_query():
    '''Calls ifconfig and returns the text response.'''
    route = subprocess.check_output(['route get 0.0.0.0'], shell=True)
    if "interface: en0" in route:
        return subprocess.check_output(['ifconfig en0'], shell=True)
    if "interface: en1" in route:
        return subprocess.check_output(['ifconfig en1'], shell=True)
    return "OH SNAP"


def broadcast_ping(ifconfig_res):
    '''Finds the broadcast internet ip and sends out a single broadcast ping
    (currently silently). Because not a lot of machines respond to broadcast
    pings, there are other slower ways that fewer devices ignore.'''
    # starting with a broadcast ping
    broadcast_re = r'broadcast [0-9]+(?:\.[0-9]+){3}'
    internet_re = r'inet [0-9]+(?:\.[0-9]+){3}'
    broadcast_ip = re.findall(broadcast_re, ifconfig_res)
    broadcast_ip = broadcast_ip[0]

    internet_ip = re.findall(internet_re, ifconfig_res)
    if len(internet_ip) >= 2:
        internet_ip = internet_ip[1].split()[1]
    elif len(internet_ip) == 1:
        internet_ip = internet_ip[0].split()[1]
    broadcast_ip = broadcast_ip.split()[1]

    ## silent response, calls the ping with no terminal output because #annoying
    response = subprocess.check_output(["ping -c 1 " + broadcast_ip], shell=True)
    
    ## Binary response, prints to the terminal, if it's failing you can enable it
    # response = os.system("ping -c 1 " + broadcast_ip)
    # print(response == response1)

    # if response != 0:
    #   print("Broadcast ping failed")
    # else:
    return broadcast_ip, internet_ip


def determine_class_license(ifconfig_res):
    '''Figure out which class license you're on: netmask inet 10.0.17.185 netmask
    0xffff0000 four f's means class B, two f's means class A, six f's class C.'''
    internet = re.findall(r'netmask (.*) broadcast', ifconfig_res)
    if len(internet) == 1:
        if 'ffffff' in internet[0] or "255.255.255" in internet[0]: #or 255.255.255?
            return "C"
        elif 'ffff' in internet[0] or "255.255" in internet[0]:
            return "B"
        elif 'ff' or "255." in internet[0]:
            return "A"
    print("Class License not extracted")
    return None


def individual_ping_network(broadcast_ip, class_lic):
    '''Find all ip's in your subnet (only works for class B and C because 
    you don't want arp 8 million addresses), arping's them so then they'll 
    be added to your arp table.'''
    ip_parts = broadcast_ip.split(".")
    print(ip_parts)
    ip_list = []
    for i in xrange(0,255):
        if class_lic == "C":
            ip = ip_parts[0]+"."+ip_parts[1]+"."+ip_parts[2]+"."+str(i)
            ip_list.append(ip)
        elif class_lic == "B":
            for j in xrange(0,255):
                ip = ip_parts[0]+"."+ip_parts[1]+"."+str(i)+"."+str(j)
                ip_list.append(ip)
    
    pool = ThreadPool(40)
    pool.map(ping_thread, ip_list)
    pool.close()
    pool.join()


def ping_thread(ip):
    '''Calls to the system a single ping directed at a specific ip address.'''
    ping = os.system("arping -c 1 " + ip)


def arp_lookup():
    '''Look up arp table, find all mac addresses, put them in a dictionary 
    with the IP addresses as keys.'''
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
            network_dict[mac] = ip
    return network_dict


def friends_home(network_dict):
    '''Looks up your known mac addresses and prints out who is home, 
    their mac address and their current ip address.'''
    print("~~~~~~~~~Friends who are home~~~~~~~~~~~~")
    for friend in friends:
        friend = mac_clean(friend)
        if friend in network_dict:
            print(friend +'\t'+ network_dict[friend] +'\t'+  friends[friend])


def device_types(network_dict):
    '''Prints the contents of your arp table and what maker/manufacturer 
    is associated with their mac address.'''
    print("~~~~~~~~~Device types on your network~~~~~~~~~~~~")
    for mac in network_dict:
        if mac[:8] in mac_addresses:
            print(mac +'\t'+ network_dict[mac] +'\t'+ mac_addresses[mac[:8]])
        else:
            print("DON'T KNOW", mac)


def nmap_subnet(internet_ip):
    '''Nmaps whatever subnet (last octect) you're on 
    so you find all devices on your net.'''
    internet_ip = internet_ip.split(".")
    broad_ip = internet_ip[0]+"."+internet_ip[1]+"."+internet_ip[2]+".*"
    os.system("nmap -F " + broad_ip)


def arg_parser():
    parser = argparse.ArgumentParser(description="""Looks over your subnet, 
        informs you of the computers you have interacted with recently 
        and/or those which have responded to the program's broadcast ping.""")
    parser.add_argument('-p', '--pingall', action='store_true', 
                            help="pings all devices on your subnet")
    parser.add_argument('-n', '--nmapsubnet', action='store_true', 
                            help="""nmaps all ip's with the same last octet 
                            of your current ip address""")
    return parser.parse_args()


def main():
    args = arg_parser()
    ifconfig_response = ifconfig_query()
    class_license = determine_class_license(ifconfig_response)
    broadcast_ip, internet_ip = broadcast_ping(ifconfig_response)
    if args.pingall:    # if -p arg given on the command line
        individual_ping_network(broadcast_ip, class_license)
    if args.nmapsubnet:     # if -n arg given on the command line
        nmap_subnet(internet_ip)
    network_dict = arp_lookup()
    friends_home(network_dict)
    device_types(network_dict)


if __name__ == '__main__':
    main()
