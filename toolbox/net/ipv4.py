"""IPv4 tools."""

from functools import reduce
from typing import Any, Dict, Optional, Union, List, cast
import re
import numpy as np

from toolbox.binary import get_mask


AddressLike = Union[int, str, np.uint32, "Address"]

private_subnets = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
]


def is_valid(addr: AddressLike) -> bool:
    try:
        Address.parse(addr)
        return True
    except ValueError:
        return False


class Address:
    def __init__(self, addr: AddressLike) -> None:
        self.integer = self.parse(addr)
        
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Address):
            return self.integer == other.integer
        return False
    
    def __or__(self, other: "Address") -> "Address":
        return Address(self.integer | other.integer)
    
    def __and__(self, other: "Address") -> "Address":
        return Address(self.integer & other.integer)

    @classmethod
    def parse(cls, addr: AddressLike) -> np.uint32:
        if type(addr) == Address:
            return addr.integer
        
        elif type(addr) == str:
            match = re.match(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$', addr)
            if not match:
                raise ValueError(f"Invalid IPv4 string '{addr}'")
            
            octets: List[int] = [int(match.group(i + 1)) << shift for i, shift in enumerate([24, 16, 8, 0])]
            return np.uint32(reduce(lambda o1, o2: o1 | o2, octets, 0))
        
        elif type(addr) == int and not 0 <= addr <= get_mask(32):
            raise ValueError(f"Invalid IPv4 integer {addr}")
        
        return np.uint32(cast(int, addr))
        
    @property
    def octets(self) -> List[int]:
        return [int((self.integer >> shift) & 0xFF) for shift in [24, 16, 8, 0]]
    
    @property
    def is_private(self) -> bool:
        for private_subnet in private_subnets:
            if self in Config(private_subnet):
                return True
        return False
        
    def __str__(self) -> str:
        return ".".join(map(str, self.octets))
    
    
class Subnet(Address):
    @classmethod
    def from_cidr(cls, cidr: int) -> "Subnet":
        if not 0 <= cidr <= 32:
            raise ValueError(f"Invalid IPv4 CIDR '{cidr}' must be between 0 and 32")
        
        return Subnet(get_mask(cidr) << (32 - cidr))
    
    def get_network_address(self, addr: AddressLike) -> Address:
        return Address(addr) & self
        
    def get_broadcast_address(self, addr: AddressLike) -> Address:
        return self.get_network_address(addr) | self.wildcard_address
    
    @property
    def wildcard_address(self) -> Address:
        return Address(get_mask(32) - self.integer)
    

class Config:
    def __init__(self, addr: AddressLike, cidr: Optional[int]=None):
        if type(addr) == str and cidr is None:
            if "/" not in addr:
                raise ValueError("Address must be in CIDR notation 0.0.0.0/0")
            addr, cidr = addr.split("/", maxsplit=1)
            cidr = int(cidr)
            
        self.address = Address(addr)
        self.subnet = Subnet.from_cidr(cidr)
    
    def __contains__(self, addr: AddressLike) -> bool:
        return self.subnet.get_network_address(addr) == self.network_address
    
    @property
    def first_address(self) -> Address:
        return Address(self.network_address.integer + 1)
    
    @property
    def last_usable(self) -> Address:
        return Address(self.broadcast_address.integer - 1)
        
    @property
    def network_address(self) -> Address:
        return self.subnet.get_network_address(self.address)
    
    @property
    def broadcast_address(self) -> Address:
        return self.subnet.get_broadcast_address(self.address)
    
    @property
    def usable_addresses(self) -> int:
        return int(self.broadcast_address.integer - self.network_address.integer - 1)
    
    def to_json(self) -> Dict[str, Union[str, int, bool]]:
        return {
            "address": str(self.address),
            "subnet_mask": str(self.subnet),
            "network": str(self.network_address),
            "broadcast": str(self.broadcast_address),
            "usable_addresses": self.usable_addresses,
            "wildcard_mask": str(self.subnet.wildcard_address),
            "first_usable": str(self.first_address),
            "last_usable": str(self.last_usable),
            "private": self.address.is_private,
        }
