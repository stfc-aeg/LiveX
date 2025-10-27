from odin.adapters.parameter_tree import ParameterTree
from livex.util import read_coil, read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil, LiveXError
import logging

class PID():
    """This class provides the ParameterTree for the PID controls for a given PID controller.
    It stores the values, and provides functions to write to the modbus server on the PLC.
    """

    def __init__(self, addresses, pid_defaults, maximum_temperature, maximum_temperature_step):
        """Initialise the PID class with addresses, creating the Parameter Tree and its
        required parameters to be populated when a modbus connection is established via the 
        controller.
        """
        # Addresses are generic via dictionary usage. Particularly important here for two PIDs
        self.addresses = addresses
        self.pid_defaults = pid_defaults

        # Maximum amount setpoint can increase by in one step. Min.1 because SP must be changeable
        self.max_temp_step = maximum_temperature_step if maximum_temperature_step >= 1 else 1

        self.enable = False
        self.setpoint = 0.0
        # PID term default display rounded for readability
        self.kp = 0.1
        self.ki = 0.1
        self.kd = 0.1
        self.output = 0.1
        self.outputsum = 0.1
        self.temperature = 0.1

        self.tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_enable),
            'setpoint': (lambda: self.setpoint, self.set_setpoint, {'max': maximum_temperature}),
            'max_temp_step': (lambda: self.max_temp_step, self.set_max_temp_step, {'min': 1}),
            'proportional': (lambda: self.kp, self.set_proportional),
            'integral': (lambda: self.ki, self.set_integral),
            'derivative': (lambda: self.kd, self.set_derivative),
            'temperature': (lambda: self.temperature, None),
            'output': (lambda: self.output, None),
            'outputsum': (lambda: self.outputsum, None)
        })

    def _register_modbus_client(self, client):
        """Keep internal reference to the Modbus client and attempt to use it to get parameters."""
        self.client = client
        try:
            self._get_parameters()
            self._write_pid_defaults()
        except Exception as e:
            logging.warning(f"Error when attempting to get PID parameters after client connection: {repr(e)}")

    def _get_parameters(self):
        """Get parameters for the parameter tree using a modbus connection."""
        self.enable = bool(read_coil(self.client, self.addresses['enable']))
        self.setpoint = read_decode_holding_reg(self.client, self.addresses['setpoint'])
        # PID term default display rounded for readability
        self.kp = round(read_decode_holding_reg(self.client, self.addresses['kp']), 4)
        self.ki = round(read_decode_holding_reg(self.client, self.addresses['ki']), 4)
        self.kd = round(read_decode_holding_reg(self.client, self.addresses['kd']), 4)
        self.output = read_decode_input_reg(self.client, self.addresses['output'])
        self.outputsum = read_decode_input_reg(self.client, self.addresses['outputsum'])
        self.temperature = read_decode_input_reg(self.client, self.addresses['thermocouple'])

    def _write_pid_defaults(self):
        """Write the setpoint and PID terms of the controller.
        This is called immediately after a client is registered.
        On PID class initialisation, this will be the defaults in the furnace details in livex.cfg.
        """
        logging.debug(f"defaults: {self.pid_defaults}")
        self.set_setpoint(self.pid_defaults['setpoint'])
        self.set_proportional(self.pid_defaults['kp'])
        self.set_integral(self.pid_defaults['ki'])
        self.set_derivative(self.pid_defaults['kd'])

    def set_setpoint(self, value):
        """Set the setpoint of the PID."""
        if abs(value-self.setpoint) > self.max_temp_step:
            raise LiveXError("Temperature step size exceeds limit.")

        self.setpoint = value
        write_modbus_float(
            self.client, value, self.addresses['setpoint']
        )
        write_coil(
            self.client, self.addresses['setpoint_update'], True
        )

    def set_max_temp_step(self, value):
        """Set the maximum allowed step for the setpoint value."""
        self.max_temp_step = value

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
            write_coil(self.client, self.addresses['enable'], 0)
