from odin.adapters.parameter_tree import ParameterTree
from livex.util import read_coil, read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil

import logging

class Gradient():
    """This class provides the ParameterTree for the gradient controls for LiveX.
    It stores relevant values and provides functions to write to the modbus server on the PLC.
    """

    def __init__(self, addresses):
        self.addresses = addresses

        self.enable       = False
        self.wanted       = float(0.0)
        self.distance     = float(1.5)
        self.actual       = 0
        self.theoretical  = 0
        self.high         = 'A'

        self.tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_enable),
            'wanted': (lambda: self.wanted, self.set_wanted,
                       {'min': 0}),
            'distance': (lambda: self.distance, self.set_distance,
                         {'min': 0}),
            'actual': (lambda: self.actual, None),
            'theoretical': (lambda: self.theoretical, None),
            'high_heater': (lambda: self.high, self.set_high,
                            {'allowed_values': ['A', 'B']})
        })

    def _register_modbus_client(self, client):
        """Keep internal reference to the Modbus client and attempt to use it to get parameters."""
        self.client = client
        try:
            self._get_parameters()
        except:
            logging.debug("Error when attempting to get gradient parameters after client connection.")

    def _get_parameters(self):
        """Get parameters for the parameter tree using a modbus connection."""
        self.enable       = bool(read_coil(self.client, self.addresses['enable']))
        self.wanted       = read_decode_holding_reg(self.client, self.addresses['wanted'])
        self.distance     = read_decode_holding_reg(self.client, self.addresses['distance'])
        self.actual       = read_decode_input_reg(self.client, self.addresses['actual'])
        self.theoretical  = read_decode_input_reg(self.client, self.addresses['theoretical'])
        self.high         = read_coil(self.client, self.addresses['high'], asInt=True) # used as index for high-heater selection

    def set_enable(self, value):
        """Set the enable value for the thermal gradient."""
        self.enable = value

        if value:
            write_coil(self.client, self.addresses['enable'], 0)
        else:
            write_coil(self.client, self.addresses['enable'], 1)

        write_coil(self.client, self.addresses['update'], 1)

    def set_distance(self, value):
        """Set the distance value for the thermal gradient."""
        self.distance = value
        write_modbus_float(self.client, value, self.addresses['distance'])
        write_coil(self.client, self.addresses['update'], 1)

    def set_wanted(self, value):
        """Set the desired temperature change per mm for the thermal gradient."""
        self.wanted = value
        write_modbus_float(self.client, value, self.addresses['wanted'])
        write_coil(self.client, self.addresses['update'], 1)

    def set_high(self, value):
        """Set the boolean for thermal gradient high heater."""
        self.high = value

        if value =='B':  # 1, heater B
            write_coil(self.client, self.addresses['high'], 1)
        elif value == 'A':  # 0, heater A
            write_coil(self.client, self.addresses['high'], 0)
        write_coil(self.client, self.addresses['update'], 1)
