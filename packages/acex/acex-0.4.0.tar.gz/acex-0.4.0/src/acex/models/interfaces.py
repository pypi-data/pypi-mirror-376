from typing import Optional, Dict, List
from sqlmodel import SQLModel, Field
from ipaddress import IPv4Interface

class Interface(SQLModel):
    name: str = Field(default="")

class PhysicalInterface(Interface):
    type: str = Field(default="")
    index: int = Field(default=0)
    enabled: bool = Field(default=True)
    description: Optional[str] = None
    mac_address: Optional[str] = None
    ipv4_address: Optional[IPv4Interface] = None
    speed: Optional[int] = None  # Speed in KBps
    switchport: Optional[bool] = None
    switchport_mode: Optional[str] = "access"  # e.g., 'access', 'trunk'
    switchport_untagged_vlan: Optional[int] = 1
    switchport_trunk_vlans: Optional[List[int]] = None

class VirtualInterface(Interface):
    pass


