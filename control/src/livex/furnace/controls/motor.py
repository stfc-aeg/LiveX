from odin.adapters.parameter_tree import ParameterTree
from livex.util import read_coil, read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil

import logging

class Motor():
    """This class provides the ParameterTree for the motor controls for LiveX.
    It stores relevant values and provides functions to write to the modbus server on the PLC."""

    def __init__(self, addresses):
        self.addresses = addresses

        self.enable = None
        self.direction = None
        self.speed = None
        self.lvdt = None

        self.tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_enable),
            'direction': (lambda: self.direction, self.set_direction),
            'speed': (lambda: self.speed, self.set_speed),
            'lvdt': (lambda: self.lvdt, None)
        })

    def _register_modbus_client(self, client):
        """Keep internal reference to the Modbus client and attempt to use it to get parameters."""
        self.client = client
        try:
            self._get_parameters()
        except:
            logging.debug("Error when attempting to get motor parameters after client connection.")

    def _get_parameters(self):
        """Get parameters for the parameter tree using a modbus connection."""
        self.enable = read_coil(self.client, self.addresses['enable'])
        self.direction = read_coil(self.client, self.addresses['direction'], asInt=True)
        self.speed = read_decode_holding_reg(self.client, self.addresses['speed'])
        self.lvdt = read_decode_input_reg(self.client, self.addresses['lvdt'])

    def set_enable(self, value):
        """Set motor enable boolean."""
        self.enable = value

        if value:  # 1, enabled
            write_coil(self.client, self.addresses['enable'], 1)
        else:
            write_coil(self.client, self.addresses['enable'], 0)

    def set_direction(self, value):
        """Set motor direction boolean."""
        # value = value
        self.direction = value

        if value:  # 1, up
            write_coil(self.addresses['direction'], 1)
        else:  # 0, down
            write_coil(self.addresses['direction'], 0)

    def set_speed(self, value):
        """Set motor speed holding register."""
        self.speed = value

        write_modbus_float(self.client, value, self.addresses['speed'])
