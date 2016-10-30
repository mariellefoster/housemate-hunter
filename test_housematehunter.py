import housematehunter 
from mac_add import mac_addresses


def test_mac_clean():
    assert housematehunter.mac_clean("4:3:45:34") == "04:03:45:34"

# things to test:
# running in normal mode
# running with -p and -n
# ifconfig_query should return a valid response
# determine_class_license should return correct class license

