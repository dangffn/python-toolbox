
from unittest import TestCase
from toolbox.binary import get_mask
from toolbox.net.ipv4 import Address, Config, is_valid


class TestIPv4(TestCase):
    def setUp(self) -> None:
        pass
    
    def test_ipv4_address(self) -> None:
        # Valid IP addresses.
        self.assertTrue(is_valid('255.255.255.255'))
        self.assertTrue(is_valid('0.0.0.0'))
        self.assertTrue(is_valid('192.168.1.1'))
        self.assertTrue(is_valid('10.0.0.1'))
        self.assertTrue(is_valid('172.16.0.1'))
        
        # Invalid IP addresses.
        self.assertFalse(is_valid('255.255.255.255.255'))
        self.assertFalse(is_valid('255.255.255'))
        self.assertFalse(is_valid('1.1.1.-1'))
        self.assertFalse(is_valid('-1.1.1.1'))
        
    def test_ipv4_address_integer(self) -> None:
        self.assertEqual(Address('0.0.0.0').integer, 0)
        self.assertEqual(Address('255.255.255.255').integer, get_mask(32))
        
    def test_ipv4_address_string(self) -> None:
        self.assertEqual(str(Address('1.1.1.1')), '1.1.1.1')
        
    def test_ipv4_network_config(self) -> None:
        config = Config('192.168.0.1/24')
        self.assertEqual(str(config.network_address), '192.168.0.0')
        self.assertEqual(str(config.broadcast_address), '192.168.0.255')
        self.assertEqual(config.usable_addresses, 254)
        self.assertTrue("192.168.0.123" in config)