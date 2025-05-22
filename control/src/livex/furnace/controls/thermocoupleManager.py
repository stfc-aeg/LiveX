from functools import partial
from livex.modbusAddresses import modAddr
import logging
from livex.util import write_modbus_float, read_decode_input_reg, read_decode_holding_reg

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


class ThermocoupleManager:
    """Manage the state of thermocouples: their values and the associated hardware index."""

    def __init__(self):
        # Never more than 8 TCs
        self.labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.num_mcp = 6  # Should get overwritten later

        self.thermocouple_values = {label: None for label in self.labels}
        self.thermocouple_indices = {label: None for label in self.labels}

        self.tree = {}

    def _register_modbus_client(self, client):
        """Keep internal reference to the Modbus client and attempt to use it to get parameters."""
        self.client = client
        try:
            self._get_parameters()
            self._build_tree()
        except Exception as e:
            logging.warning(f"Error when attempting to get PID parameters after client connection: {repr(e)}")

    def _get_parameters(self):
        """Get the number of mpcs for tree building."""
        self.num_mpc = read_decode_input_reg(self.client, modAddr.number_mcp_inp)

        i = 0
        for key in self.thermocouple_indices.keys():
            # Get current thermocouple indices
            read_decode_holding_reg(self.client, (modAddr.thermocouple_a_idx_hold+i*2))
            self.thermocouple_indices[key] = i
            i += 1

    def _build_tree(self):
        """Build the parameter tree."""
        for i, label in enumerate(self.labels):
            if i >= self.num_mcp:
                break
            self.tree[f'thermocouple_{label}'] = {
                'value': (
                    lambda label=label: self.thermocouple_values[label], None
                ),
                'index': (
                    lambda label=label: self.thermocouple_indices[label],
                        partial(self.set_thermocouple_index, thermocouple=label)
                )
            }
            self.tree['index_key'] = {
                    i: value for i, value in enumerate(modAddr.mcp_type)
            }
            self.tree['index_key'][-1] = 'Disabled'

    def set_thermocouple_index(self, index, thermocouple):
        """Set the index of a thermocouple."""
        if thermocouple in self.thermocouple_indices.keys():
            self.thermocouple_indices[thermocouple] = index
            addr = getattr(modAddr, f'thermocouple_{thermocouple}_idx_hold')
            write_modbus_float(self.client, index, addr)
        else:
            raise KeyError(f"Thermocouple {thermocouple} is not defined.")


