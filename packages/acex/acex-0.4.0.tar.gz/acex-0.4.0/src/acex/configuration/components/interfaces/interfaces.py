
from acex.configuration.components.base_component import ConfigComponent
from acex.models.interfaces import PhysicalInterface, VirtualInterface


class InterfaceBase(ConfigComponent): ...


class Physical(InterfaceBase): 
    KEY = "index"
    MODEL = PhysicalInterface


class Virtual(InterfaceBase):
    KEY = "index"
    MODEL = VirtualInterface


class Loopback(Virtual): ...
class Vlan(Virtual):  ...




