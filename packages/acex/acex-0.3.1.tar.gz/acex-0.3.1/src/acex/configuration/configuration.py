
from acex.configuration.components import ConfigComponent
from acex.configuration.components.interfaces import (
    Loopback,
    Vlan,
    Physical
)


class Configuration:
    def __init__(self):
        self.loopback_interfaces = {}
        self.vlan_interfaces = {}
        self.physical_interfaces = {}

    def add(self, component: ConfigComponent):

        if isinstance(component, Loopback):
            if component._key in self.loopback_interfaces:
                print(f"Loopback interface {component._key} already exists, ignoring.")
            self.loopback_interfaces[component._key] = component

        elif isinstance(component, Vlan):
            if component._key in self.vlan_interfaces:
                print(f"Vlan interface {component._key} already exists, ignoring.")
            self.vlan_interfaces[component._key] = component

        elif isinstance(component, Physical):
            if component._key in self.physical_interfaces:
                print(f"Physical interface {component._key} already exists, ignoring.")
            self.physical_interfaces[component._key] = component

        else:
            print("Unsupported config component added to configuration, ignored!")

    def to_json(self):
        cfg = {"interfaces": {}}
        if self.loopback_interfaces != {}:
            cfg["interfaces"]["loopback"] = [iface.to_json() for iface in self.loopback_interfaces.values()]
        if self.vlan_interfaces != {}:
            cfg["interfaces"]["vlan"] = [iface.to_json() for iface in self.vlan_interfaces.values()]
        if self.physical_interfaces != {}:
            cfg["interfaces"]["physical"] = [iface.to_json() for iface in self.physical_interfaces.values()]

        return cfg