# housemate-hunter
identifies and tracks known mac addresses on your subnet


usage: housemate_hunter.py [-h] [-p] [-n]

Looks over your subnet, informs you of the computers you have interacted with
recently and/or those which have responded to the program's broadcast ping.

optional arguments:

  -h, --help        show this help message and exit

  -p, --pingall     pings all devices on your subnet

  -n, --nmapsubnet  nmaps all ip's with the same last octect of your current
                    ip address
