
from acex.configuration.components.base_component import ConfigComponent


class InterfaceConfig(ConfigComponent): 
    def __init__(self):
        self.mtu = None
        self.description = None
        self.enabled = True


class InterfaceBase(ConfigComponent): 
    def __init__(self, *args, **kwargs):
        self.config: InterfaceConfig = InterfaceConfig()


class Physical(InterfaceBase): 
    def __init__(self, *, index: int):
        super().__init__()
        self._key = index
        self.index = index


class VirtualInterface(InterfaceBase):
    def __init__(self, *, name: str):
        super().__init__()
        self.name = name
        self._key = name


class Loopback(VirtualInterface): ...


class Vlan(VirtualInterface): ...



