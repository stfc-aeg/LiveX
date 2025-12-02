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
    addr: int = 0  # modbus address in modAddr attribute
    val_addr: int = 0  # address that thermocouple value should be read from
    index: int = 0  # Index in the PLC
    value: float = 0  # Value read from PLC

class ThermocoupleManager:
    """Manage the state of thermocouples: their values and the associated hardware index."""

    def __init__(self, options):
        """Initialise the manager, creating a tree of thermocouples with types and connection."""
        self.num_mcp = 6  # Default number of thermocouples, should be overwritten by PLC

        upper_heater_tc = options.get('upper_heater_tc', 'a')
        lower_heater_tc = options.get('lower_heater_tc', 'b')
        extra_tcs = [tc.lower() for tc in options.get('extra_tcs', '').split(',')]
        extra_tc_names = options.get('extra_tc_names', '').split(',')

        if len(extra_tcs) != len(extra_tc_names):
            raise LiveXError("Number of extra thermocouples does not match number of names given.")

        # Thermocouple array starts with two mandatory connections
        self.thermocouples = [
            Thermocouple(label='upper_heater', connection=CONNECTIONS[upper_heater_tc], addr=modAddr.thermocouple_a_idx_hold, val_addr=modAddr.thermocouple_a_inp),
            Thermocouple(label='lower_heater', connection=CONNECTIONS[lower_heater_tc], addr=modAddr.thermocouple_b_idx_hold, val_addr=modAddr.thermocouple_b_inp)
        ]

        for i, (tc, name) in enumerate(zip(extra_tcs, extra_tc_names)):
            if tc and name:
                self.thermocouples.append(
                    Thermocouple(label=name.strip(), connection=CONNECTIONS[tc.strip()],
                    addr=(modAddr.thermocouple_c_idx_hold+i*2), val_addr=(modAddr.thermocouple_c_inp+i*2))
                )

        self.tree = {}

    def _register_modbus_client(self, client):
        """Keep internal reference to the Modbus client and attempt to use it to get parameters."""
        self.client = client
        try:
            # 'Zero out' thermocouple range before setting with _get_parameters()
            for i in range(self.num_mcp):
                write_modbus_float(self.client, -1, modAddr.thermocouple_a_idx_hold+i*2)

            self._get_parameters()
            self._build_tree()
        except Exception as e:
            logging.warning(f"Error when attempting to get PID parameters after client connection: {repr(e)}")

    def _get_parameters(self):
        """Get parameters needed for the parameter tree and send thermocouple info to modbus."""
        self.num_mcp = int(read_decode_input_reg(self.client, modAddr.number_mcp_inp))

        for tc in self.thermocouples:
            index = tc.connection.value
            write_modbus_float(self.client, index, tc.addr)
            tc.index = index
            # logging.warning(f"written {index} to address {tc.addr} for tc {tc.label}")

        # write_coil(self.client, modAddr.tc_type_update_coil, 1)

    def _build_tree(self):
        """Build the parameter tree."""
        # The names for the tree are fixed, but the user won't see these
        tree_names = ['upper_heater', 'lower_heater'] + [f'extra_{i+1}' for i in range(self.num_mcp-2)]
        for i, tc in enumerate(self.thermocouples[:self.num_mcp]):
            key = f"thermocouple_{tree_names[i]}"
            self.tree[key] = {
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