


class ConfigComponent: 


    def to_json(self):
        response = {}

        # add attributes that do not start with _
        for key, value in self.__dict__.items():
            if key.startswith('_') or value is None:
                continue

            if isinstance(value, ConfigComponent):
                response[key] = value.to_json()
            elif isinstance(value, list):
                response[key] = [v.to_json() if isinstance(v, ConfigComponent) else v for v in value]
            else:
                response[key] = value

        return response