from odin.adapters.parameter_tree import ParameterTree
from livex.util import read_coil, read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil

class AutoSetPointControl():
    """This class provides the ParameterTree for the auto set point control controls for LiveX.
    It stores relevant values and provides functions to write to the modbus server on the PLC."""

    def __init__(self, client, addresses):
        self.register_modbus_client(client)
        self.addresses = addresses

        self.enable = read_coil(self.client, self.addresses['enable'])
        self.heating = read_coil(self.client, self.addresses['heating'], asInt=True)
        self.heating_options = self.addresses['heating_options']
        self.rate = read_decode_holding_reg(self.client, self.addresses['rate'])
        self.midpt = read_decode_input_reg(self.client, self.addresses['midpt'])
        self.imgdegree = read_decode_holding_reg(self.client, self.addresses['imgdegree'])

        self.tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_enable),
            'heating': (lambda: self.heating, self.set_heating),
            'heating_options': (lambda: self.heating_options, None), 
            'rate': (lambda: self.rate, self.set_rate),
            'img_per_degree': (lambda: self.imgdegree, self.set_imgdegree),
            'midpt_temp': (lambda: self.midpt, None)
        })

    def register_modbus_client(self, client):
        """Keep internal reference to modbus client."""
        self.client = client

    def set_enable(self, value):
        """Set the enable boolean for the auto set point control."""
        self.enable = bool(value)

        if value:
            write_coil(self.client, self.addresses['enable'], 1)
        else:
            write_coil(self.client, self.addresses['enable'], 0)

    def set_heating(self, value):
        """Set the boolean for auto set point control heating."""
        self.heating = value

        if value:  # 1, heating
            write_coil(self.client, self.addresses['heating'], 1)
        else:      # 0, cooling
            write_coil(self.client, self.addresses['heating'], 0)

    def set_rate(self, value):
        """Set the rate value for the auto set point control."""
        self.rate = value
        write_modbus_float(self.client, value, self.addresses['rate'])

    def set_imgdegree(self, value):
        """Set the image acquisition per degree for the auto set point control."""
        self.imgdegree = value
        write_modbus_float(self.client, value, self.addresses['imgdegree'])