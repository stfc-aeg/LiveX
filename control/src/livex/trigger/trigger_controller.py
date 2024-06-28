import logging
from pymodbus.client import ModbusTcpClient
from livex.util import read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil
from livex.modbusAddresses import modAddr

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

class TriggerError():
    """Simple exception class to wrap lower-level exceptions."""
    pass

class TriggerController():
    """Class to instantiate and manage a modbus connection to control the triggering device."""

    def __init__(self, ip, frequencies):

        self.ip = ip
        self.mod_client = ModbusTcpClient(self.ip)
        self.mod_client.connect()

        self.freq_furnace = frequencies['furnace']
        self.freq_wideFov = frequencies['wideFov']
        self.freq_narrowFov = frequencies['narrowFov']

        self.all_enabled = False
        self.furnace_enabled = False
        self.widefov_enabled = False
        self.narrowfov_enabled = False

        self.tree = ParameterTree({
            'enable': {
                'all': (lambda: self.all_enabled, None),
                'furnace': (lambda: self.furnace_enabled, self.toggle_furnace_enable),
                'wideFov': (lambda: self.widefov_enabled, self.toggle_widefov_enable),
                'narrowFov': (lambda: self.narrowfov_enabled, self.toggle_narrowfov_enable)
            },
            'frequency': {
                'furnace': (lambda: self.freq_furnace, self.update_furnace_interval),
                'wideFov': (lambda: self.freq_wideFov, self.update_widefov_interval),
                'narrowFov': (lambda: self.freq_narrowFov, self.update_narrowfov_interval)
            }

        })

    def check_all_enabled(self):
        """Check if all timers are enabled."""
        self.all_enabled = (self.furnace_enabled and self.widefov_enabled and self.narrowfov_enabled)
        return self.all_enabled

    def update_interval(self, address, value):
        """Update the given interval address with given value and update the 'new-val' coil."""
        self.mod_client.write_register(address, int(value))
        self.mod_client.write_coil(modAddr.trig_val_updated_coil, 1)
        self.check_all_enabled()

    def update_furnace_interval(self, value):
        """Update the interval of the furnace timer."""
        self.update_interval(modAddr.trig_furnace_intvl_hold, value)

    def toggle_furnace_enable(self, value):
        """Toggle the furnace timer."""
        self.furnace_enabled = not self.furnace_enabled
        write_coil(self.mod_client, modAddr.trig_furnace_enable_coil, bool(self.furnace_enabled))
        self.check_all_enabled()

    def update_widefov_interval(self, value):
        """Update the interval of the WideFov camera timer."""
        self.update_interval(modAddr.trig_widefov_intvl_hold, value)

    def toggle_widefov_enable(self, value):
        """Toggle the widefov timer."""
        self.widefov_enabled = not self.widefov_enabled
        write_coil(self.mod_client, modAddr.trig_widefov_enable_coil, bool(self.widefov_enabled))
        self.check_all_enabled()

    def update_narrowfov_interval(self, value):
        """Update the interval of the NarrowFov camera timer."""
        self.update_interval(modAddr.trig_narrowfov_intvl_hold, value)

    def toggle_narrowfov_enable(self, value):
        """Toggle the narrowfov timer."""
        self.narrowfov_enabled = not self.narrowfov_enabled
        write_coil(self.mod_client, modAddr.trig_narrowfov_enable_coil, bool(self.narrowfov_enabled))
        self.check_all_enabled()

    def get(self, path):
        """Get the parameter tree.
        This method returns the parameter tree for use by clients via the FurnaceController adapter.
        :param path: path to retrieve from tree
        """
        return self.tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree.
        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate LiveXError.
        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.tree.set(path, data)
        except ParameterTreeError as e:
            raise TriggerError(e)

    def cleanup(self):
        """Clean up the FurnaceController instance.

        This method stops the background tasks, allowing the adapter state to be cleaned up
        correctly.
        """
        self.mod_client.close()