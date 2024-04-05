from odin.adapters.parameter_tree import ParameterTree
from livex.util import read_coil, read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil

class PID():
    """This class provides the ParameterTree for the PID controls for a given PID controller.
    It stores the values, and provides functions to write to the modbus server on the PLC.
    """

    def __init__(self, client, addresses):
        self.register_modbus_client(client)  # Client required for __init__, client function used for reset

        # Addresses are generic via dictionary usage. Particularly important here for two PIDs
        self.addresses = addresses

        self.enable = bool(read_coil(self.client, self.addresses['enable']))
        self.setpoint = read_decode_holding_reg(self.client, self.addresses['setpoint'])
        # PID term default display rounded for readability
        self.kp = round(read_decode_holding_reg(self.client, self.addresses['kp']), 4)
        self.ki = round(read_decode_holding_reg(self.client, self.addresses['ki']), 4)
        self.kd = round(read_decode_holding_reg(self.client, self.addresses['kd']), 4)
        self.output = read_decode_input_reg(self.client, self.addresses['output'])
        self.gradient_setpoint = read_decode_input_reg(self.client, self.addresses['gradient_setpoint'])
        self.thermocouple = read_decode_input_reg(self.client, self.addresses['thermocouple'])

        self.tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_enable),
            'setpoint': (lambda: self.setpoint, self.set_setpoint),
            'gradient_setpoint': (lambda: self.gradient_setpoint, None),
            'proportional': (lambda: self.kp, self.set_proportional),
            'integral': (lambda: self.ki, self.set_integral),
            'derivative': (lambda: self.kd, self.set_derivative),
            'temperature': (lambda: self.thermocouple, None),
            'output': (lambda: self.output, None)
        })

    def register_modbus_client(self, client):
        """Keep internal reference to the Modbus client."""
        self.client = client

    def set_setpoint(self, value):
        """Set the setpoint of the PID."""
        self.setpoint = value
        write_modbus_float(
            self.client, value, self.addresses['setpoint']
        )

    def set_proportional(self, value):
        """Set the proportional term of the PID."""
        self.kp = value
        write_modbus_float(
            self.client, value, self.addresses['kp']
        )

    def set_integral(self, value):
        """Set the integral term of the PID."""
        self.ki = value
        write_modbus_float(
            self.client, value, self.addresses['ki']
        )
    
    def set_derivative(self, value):
        """Set the derivative term of the PID."""
        self.kd = value
        write_modbus_float(
            self.client, value, self.addresses['kd']
        )

    def set_enable(self, value):
        """Set the enable boolean for the PID."""
        self.enable = bool(value)

        if value:
            write_coil(self.client, self.addresses['enable'], 1)
        else:
            write_coil(self.client, self.addresses['enable'], 0,)
