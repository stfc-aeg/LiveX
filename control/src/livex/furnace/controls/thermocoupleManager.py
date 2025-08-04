from functools import partial
from enum import Enum
from dataclasses import dataclass
from livex.modbusAddresses import modAddr
import logging
from livex.util import write_modbus_float, read_decode_input_reg, read_decode_holding_reg, write_coil, LiveXError

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

class CONNECTIONS(Enum):
    """Enum to associate the physical connection point of a thermocouple to the index in the PLC."""
    a = 0
    b = 1
    c = 2
    d = 3
    e = 4
    f = 5

@dataclass
class Thermocouple:
    label: str  # User-defined 'name' for the thermocouple
    connection: CONNECTIONS
    index: int = None  # Index in the PLC
    value: float = None  # Value read from PLC

class ThermocoupleManager:
    """Manage the state of thermocouples: their values and the associated hardware index."""

    def __init__(self, options):
        """Initialise the manager, creating a tree of thermocouples with types and connection."""
        self.num_mcp = 6  # Default number of thermocouples, should be overwritten by PLC

        upper_heater_tc = options.get('upper_heater_tc', 'a')
        lower_heater_tc = options.get('lower_heater_tc', 'b')
        extra_tcs = options.get('extra_tcs', '').split(',')
        extra_tc_names = options.get('extra_tc_names', '').split(',')

        if len(extra_tcs) != len(extra_tc_names):
            raise LiveXError("Number of extra thermocouples does not match number of names given.")

        # Thermocouple array starts with two mandatory connections
        self.thermocouples = [
            Thermocouple(label='upper_heater', connection=CONNECTIONS[upper_heater_tc]),
            Thermocouple(label='lower_heater', connection=CONNECTIONS[lower_heater_tc])
        ]

        self.thermocouples.extend(
            Thermocouple(label=name.strip(), connection=CONNECTIONS[tc.strip()]) for tc, name in zip(extra_tcs, extra_tc_names) if tc and name
        )

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
        """Get parameters needed for the parameter tree."""
        self.num_mcp = int(read_decode_input_reg(self.client, modAddr.number_mcp_inp))

        # Not all connections are necessarily defined, ones that are not will get -1 written
        used_connections = {tc.connection: tc for tc in self.thermocouples}

        for i, connection in enumerate(CONNECTIONS):
            if i >= self.num_mcp:
                break

            if connection in used_connections:
                index = used_connections[connection].connection.value
            else:
                index = -1

            write_modbus_float(
                self.client, index, getattr(modAddr, f'thermocouple_{connection.name}_idx_hold')
            )
            if connection in used_connections:
                used_connections[connection].index = index

        write_coil(self.client, modAddr.tc_type_update_coil, 1)

    def _build_tree(self):
        """Build the parameter tree."""
        for tc in self.thermocouples[:self.num_mcp]:
            self.tree[f"thermocouple_{tc.connection.name}"] = {
                "label": (lambda label=tc.label: label, None),
                "connection": (lambda conn=tc.connection: conn.name, None),
                "value": (lambda label=tc.label: self._get_value_by_label(label), None)
            }

    def _get_value_by_label(self, label):
        """Get the value of a thermocouple by its name. e.g.: 'a'"""
        for tc in self.thermocouples:
            if tc.label == label:
                return tc.value
        raise KeyError(f"Could not get value: thermocouple with label {label} not found.")