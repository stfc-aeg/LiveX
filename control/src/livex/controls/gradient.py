from odin.adapters.parameter_tree import ParameterTree
from livex.util import read_coil, read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil

class Gradient():
    """This class provides the ParameterTree for the gradient controls for LiveX.
    It stores relevant values and provides functions to write to the modbus server on the PLC.
    """

    def __init__(self, client, addresses):
        self.register_modbus_client(client)
        self.addresses = addresses

        self.enable       = bool(read_coil(self.client, self.addresses['enable']))
        self.wanted       = read_decode_holding_reg(self.client, self.addresses['wanted'])
        self.distance     = read_decode_holding_reg(self.client, self.addresses['distance'])
        self.actual       = read_decode_input_reg(self.client, self.addresses['actual'])
        self.theoretical  = read_decode_input_reg(self.client, self.addresses['theoretical'])
        self.high         = read_coil(self.client, self.addresses['high']) # used as index for high-heater selection
        self.high_options = self.addresses['high_options']

        self.tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_enable),
            'wanted': (lambda: self.wanted, self.set_wanted),
            'distance': (lambda: self.distance, self.set_distance),
            'actual': (lambda: self.actual, None),
            'theoretical': (lambda: self.theoretical, None),
            'high_heater': (lambda: self.high, self.set_high),
            'high_heater_options': (lambda: self.high_options, None)
        })

    def register_modbus_client(self, client):
        """Keep internal reference to modbus client."""
        self.client = client

    def set_enable(self, value):
        """Set the enable boolean for the thermal gradient."""
        self.enable = bool(value)

        if value:
            write_coil(self.client, self.addresses['enable'], 1)
        else:
            write_coil(self.client, self.addresses['enable'], 0)

    def set_distance(self, value):
        """Set the distance value for the thermal gradient."""
        self.distance = value
        write_modbus_float(self.client, value, self.addresses['distance'])

    def set_wanted(self, value):
        """Set the desired temperature change per mm for the thermal gradient."""
        self.wanted = value
        write_modbus_float(self.client, value, self.addresses['wanted'])

    def set_high(self, value):
        """Set the boolean for thermal gradient high heater."""
        self.high = value

        if value:  # 1, heater B
            write_coil(self.client, self.addresses['high'], 1)
        else:
            write_coil(self.client, self.addresses['high'], 0)
