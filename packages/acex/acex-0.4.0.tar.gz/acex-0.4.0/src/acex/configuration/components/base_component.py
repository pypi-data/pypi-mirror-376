
from ipaddress import IPv4Interface, IPv6Interface

class ConfigComponent: 

    def __init__(self, *args, **kwargs): 
        
        # Getting the primary sort key based on cls var
        # from child class definition. 
        # _key attribute is used for sorting components in configuration
        self._key_name = self.__class__.KEY
        self._model = self.__class__.MODEL

        if self._key_name in kwargs:
            self._key = kwargs.get(self._key_name)
        else:
            raise ValueError(f"Missing required key attribute '{self._key_name}' for {self.__class__.__name__}")

    def validate(self):
        """
        Validaes the component's attributes against its model.
        Check all typing and constraints.
        """
        try:
            self._model(**self.__dict__)
        except Exception as e:
            raise ValueError(f"Validation error in {self.__class__.__name__}: {e}")


    def process(self):
        """
        Process body, for instance compute derived attributes 
        such as ip address/subnetmask/prefixlen from ip interface.
        """
        model_representation = self._model(**self.__dict__)

        for k, v in model_representation.__dict__.items():
            if isinstance(v, (IPv4Interface, IPv6Interface)):
                new_value = {
                    "ip_address": str(v.ip),
                    "subnet_mask": str(v.network.netmask),
                    "prefix_len": v.network.prefixlen
                }
                setattr(self, k, new_value)


    def to_json(self):
        self.validate()
        self.process()
        response = {}

        # Based on the model injected in child component definition
        valid_attributes = self._model.model_fields.keys()

        # Insert sorting key first
        response[self._key_name] = self._key

        for key in valid_attributes:
            value = getattr(self, key, None)

            if key.startswith('_') or value is None:
                continue

            if isinstance(value, ConfigComponent):
                response[key] = value.to_json()
            elif isinstance(value, list):
                response[key] = [v.to_json() if isinstance(v, ConfigComponent) else v for v in value]
            elif isinstance(value, IPv4Interface):
                response[key] = f"IP ADDRESS: {str(value)}"
            else:
                response[key] = value

        # if attribute is not in the model, add it to custom_attributes
        for key, value in self.__dict__.items():
            if key in valid_attributes:
                continue
            if key.startswith('_') or value is None:
                continue

            response["custom_attributes"] = {}

            if isinstance(value, ConfigComponent):
                response["custom_attributes"][key] = value.to_json()
            elif isinstance(value, list):
                response["custom_attributes"][key] = [v.to_json() if isinstance(v, ConfigComponent) else v for v in value]
            else:
                response["custom_attributes"][key] = value

        return response