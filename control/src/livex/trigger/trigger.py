from odin.adapters.parameter_tree import ParameterTree
from livex.util import read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil
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

        self.client = None

        self.tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_enable),
            'frequency': (lambda: self.frequency, self.set_frequency),
            'target': (lambda: self.target, self.set_target)
        })


    def register_modbus_client(self, client):
        self.client = client
        try:
            self._get_parameters()
        except:
            logging.debug("Error when attempting to get trigger parameters after client registry.")

    def _get_parameters(self):
        """Read modbus registers to get the most recent values for the trigger."""
        ret = self.client.read_coils(self.addr['enable_coil'], 1, slave=1)
        self.enable = ret.bits[0]

        # Frequencies = 1_000_000 / intvl*2
        # Interval = (1_000_000 / freq) // 2
        self.frequency = 1_000_000 / (
            read_decode_holding_reg(self.client, self.addr['interval_hold']) * 2
        )

        self.target = read_decode_holding_reg(self.client, self.addr['target_hold'])

    def update_hold_value(self, address, value):
        """Write a value to a given holding register(s) and mark the 'value updated' coil."""
        write_modbus_float(self.client, float(value), address)
        write_coil(self.client, self.addr['val_updated_coil'])

    def set_enable(self, value):
        """Toggle the enable for the timer."""
        self.enable = bool(value)
        write_coil(self.client, self.addr['enable_coil'], bool(self.enable))

    def set_frequency(self, value):
        """Set the frequency of the timer, then calculate the interval and send that value."""
        self.frequency = value
        logging.debug(f"trigger {self.name} with frequency {self.frequency}")
        interval = (1_000_000 / self.frequency) // 2
        self.update_hold_value(self.addr['interval_hold'], interval)
        logging.debug("updated hold value")

    def set_target(self, value):
        """Set the target framecount of the timer."""
        self.target = int(value)  # Could be int or float but int is better
        self.update_hold_value(self.addr['target_hold'], self.target)