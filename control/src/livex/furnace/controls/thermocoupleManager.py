from functools import partial
from livex.modbusAddresses import modAddr
import logging
from livex.util import write_modbus_float, read_decode_input_reg, read_decode_holding_reg, write_coil

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


class ThermocoupleManager:
    """Manage the state of thermocouples: their values and the associated hardware index."""

    def __init__(self, indices, types):
        """Initialise the manager, creating """
        # Never more than 8 TCs
        self.init_indices = indices
        self.init_types = types
        self.labels = ['a', 'b', 'c', 'd', 'e', 'f']
        self.num_mcp = 6  # Should get overwritten later

        self.thermocouple_values = {label: None for label in self.labels}
        self.thermocouple_indices = {label: None for label in self.labels}
        self.thermocouple_types = {label: None for label in self.labels}

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


        # Not enough defined, inform user and pad it out
        if len(self.init_indices) < self.num_mcp:
            logging.warning(f"Too few thermocouple indices defined. Undefined TCs will be disabled.")
            self.init_indices = self.init_indices + [-1] * (self.num_mcp-self.init_indices)
        if len(self.init_types) < self.num_mcp:
            logging.warning(f"Too few thermocouple types defined. Additional types defaulted to K.")
            self.init_types = self.init_types + ['K']*(self.num_mcp-self.init_types)

        for i in range(self.num_mcp):
            tc = self.labels[i]
            # Write the configured indices and types to the firmware
            index = self.init_indices[i]
            write_modbus_float(self.client,
                index,
                modAddr.thermocouple_a_idx_hold+i*2
            )
            self.thermocouple_indices[tc] = index
            # i*2 for addresses: relevant registers are adjacent and floats take 2
            tc_type = self.init_types[i]
            write_modbus_float(self.client,
                modAddr.mcp_val_from_type[tc_type],
                modAddr.tcidx_0_type_hold+i*2)
            self.thermocouple_types[tc] = tc_type
        write_coil(self.client, modAddr.tc_type_update_coil, 1)

        # i = 0
        # for key in self.thermocouple_indices.keys():
        #     # Get current thermocouple indices. i*2 as registers are adjacent and floats take 2
        #     read_decode_holding_reg(self.client, (modAddr.thermocouple_a_idx_hold+i*2))
        #     self.thermocouple_indices[key] = i
        #     # Get the thermocouple types
        #     type = read_decode_holding_reg(self.client, modAddr.tcidx_0_type_hold+i*2)
        #     type = modAddr.mcp_type_from_val[type]
        #     self.thermocouple_types[key] = type

        #     i += 1


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
                ),
                'type': (
                    lambda label=label, i=i: self.thermocouple_types[label],
                    partial(self._set_thermocouple_type, thermocouple=label, index=i)
                )
            }

    def set_thermocouple_index(self, index, thermocouple):
        """Set the index of a thermocouple."""
        if thermocouple in self.thermocouple_indices.keys():
            self.thermocouple_indices[thermocouple] = index
            addr = getattr(modAddr, f'thermocouple_{thermocouple}_idx_hold')
            write_modbus_float(self.client, index, addr)

            # With index set, get back the type of thermocouple registered for that index
            # e.g. set to 1, get type from tcidx_1_type_hold
            addr = getattr(modAddr, f'tcidx_{index}_type_hold')
            self.thermocouple_types[thermocouple] = modAddr.mcp_type_from_val[
                read_decode_holding_reg(self.client, addr)
            ]
        else:
            raise KeyError(f"Thermocouple {thermocouple} is not defined.")

    def _set_thermocouple_type(self, type, thermocouple, index):
        """Set the type of the thermocouple at a given index.
        Shouldn't be used unless the hardware has been swapped,
        otherwise values read back may be unreliable.
        :param str type: type of thermocouple matching modAddr.mcp_type enumeration options
        """
        try:
            type=type.upper()
            value = modAddr.mcp_val_from_type[type]
        except KeyError:
            logging.debug(f"Type {type} is not a valid thermocouple type.")
        if thermocouple in self.thermocouple_types.keys():
            self.thermocouple_types[thermocouple] = type
            addr = getattr(modAddr, f'tcidx_{index}_type_hold')
            write_modbus_float(self.client, value, addr)

            # Inform hardware that TC type has been updated
            write_coil(self.client, modAddr.tc_type_update_coil, 1)
