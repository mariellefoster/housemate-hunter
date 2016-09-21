import housematehunter 
from mac_add import mac_addresses


def test_mac_clean():
    assert housematehunter.mac_clean("4:3:45:34") == "04:03:45:34"


