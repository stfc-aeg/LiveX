from odin.adapters.parameter_tree import ParameterTree
from livex.util import read_decode_holding_reg, write_modbus_float, write_coil, read_coil
import logging

class Trigger():
    """This class provides the ParameterTree for the trigger controls for LiveX.
    It stores relevant values and provides functions to control a given trigger output via modbus.
    """

    def __init__(self, name, addresses):

        self.name = name  # defined in livex.cfg
        self.addr = addresses # see modbusAddresses.py for address definitions
        self.enable = None
        self.frequency = None
        self.target = None
        self.running = False

        self.client = None

        self.tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_enable),
            'running': (lambda: self.running, None),
            'frequency': (lambda: self.frequency, self.set_frequency),
            'target': (lambda: self.target, self.set_target)
        })


    def register_modbus_client(self, client):
        self.client = client
        try:
            self._get_parameters()
        except Exception as e:
            logging.debug(f"Error {e} when attempting to get trigger parameters after client registry.")

    def _get_parameters(self):
        """Read modbus registers to get the most recent values for the trigger."""
        ret = self.client.read_coils(self.addr['enable_coil'], 1, slave=1)
        self.enable = ret.bits[0]

        self.running = read_coil(self.client, self.addr['running_coil'])
        self.frequency = read_decode_holding_reg(self.client, self.addr['freq_hold'])
        self.target = int(read_decode_holding_reg(self.client, self.addr['target_hold']))

    def update_hold_value(self, address, value):
        """Write a value to a given holding register(s) and mark the 'value updated' coil."""
        write_modbus_float(self.client, float(value), address)

    def set_enable(self, value):
        """Toggle the enable for the timer."""
        self.enable = bool(value)
        # Both writes are True as these are flags handled by hardware
        if self.enable:
            write_coil(self.client, self.addr['enable_coil'], True)
        elif not self.enable:
            write_coil(self.client, self.addr['disable_coil'], True)

    def set_frequency(self, value):
        """Set the frequency of the timer, then calculate the interval and send that value."""
        self.frequency = value
        logging.debug(f"Set trigger {self.name} to frequency {self.frequency}.")
        # interval = (1_000_000 / self.frequency) // 2
        self.update_hold_value(self.addr['freq_hold'], self.frequency)

    def set_target(self, value):
        """Set the target framecount of the timer."""
        self.target = int(value)  # Could be int or float but int is better
        self.update_hold_value(self.addr['target_hold'], self.target)