import logging

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from pymodbus.client import ModbusTcpClient
from tornado.ioloop import PeriodicCallback

from livex.base_controller import BaseController
from livex.modbusAddresses import modAddr
from livex.util import (
    LiveXError,
    read_decode_holding_reg,
    read_decode_input_reg,
    write_coil,
    write_modbus_float,
)

from .trigger import Trigger


class TriggerController(BaseController):
    """Class to instantiate and manage a modbus connection to control the triggering device."""

    def __init__(self, options):

        # Parse options and build trigger objects
        self.ip = options.get('ip', None)
        self.status_bg_task_enable = int(options.get('status_bg_task_enable', 1))
        self.status_bg_task_interval = int(options.get('status_bg_task_interval', 10))

        self.triggers = {}
        names = options.get('triggers', None).split(",")

        for i in range(len(names)):
            name = names[i].strip()
            addr = "trigger_" + str(i)
            addresses = getattr(modAddr, addr)
            logging.debug(f"addresses for trigger {name}: {addresses}")
            self.triggers[name] = Trigger(name, addresses)

        self.frequencies = [
            item.strip() for item in options.get('frequencies', None).split(",")
        ]

        # Initialise the modbus client and get all register values
        self.initialise_client(value=None)
        self.get_all_registers()

        if self.status_bg_task_enable:
            self.start_background_tasks()

        subtrees = {}
        for trig_name, trigger in self.triggers.items():
            subtrees[trig_name] = trigger.tree

        self.tree = ParameterTree({
           'triggers': subtrees,
           'background': {
                'interval': (lambda: self.status_bg_task_interval, self.set_task_interval),
                'enable': (lambda: self.status_bg_task_enable, self.set_task_enable)
            },
            'all_timers_enable': (lambda: None, self.set_all_timers),
            'modbus': {
                'ip': (lambda: self.ip, self.set_ip),
                'connected': (lambda: self.connected, None),
                'reconnect': (lambda: None, self.initialise_client)
            }
        })

    def initialize(self, adapters) -> None:
        """Initialize the controller.

        This method initializes the controller with information about the adapters loaded into the
        running application.

        :param adapters: dictionary of adapter instances
        """
        self.adapters = adapters
        if 'sequencer' in self.adapters:
            logging.debug("Trigger controller registering context with sequencer")
            self.adapters['sequencer'].add_context('trigger', self)

    def cleanup(self):
        """Clean up the TriggerController instance.

        This method closes the modbus client, allowing the adapter state to be cleaned up
        correctly.
        """
        self.mod_client.close()

    def get(self, path: str, with_metadata: bool = False):
        """Get the parameter tree.
        This method returns the parameter tree for use by clients via the FurnaceController adapter.
        :param path: path to retrieve from tree
        """
        try:
            return self.tree.get(path, with_metadata)
        except ParameterTreeError as error:
            logging.error(error)
            raise LiveXError(error)

    def set(self, path, data):
        """Set parameters in the parameter tree.
        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate LiveXError.
        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.tree.set(path, data)
        except ParameterTreeError as error:
            logging.error(error)
            raise LiveXError(error)

    def set_ip(self, value):
        """Set the ModbusTCPClient IP to the provided value."""
        self.ip = value

    def initialise_client(self, value):
        """Initialise the modbus client."""
        try:
            log = logging.getLogger('pymodbus')
            log.setLevel(logging.ERROR)
            self.mod_client = ModbusTcpClient(self.ip)
            self.mod_client.connect()
            self.connected = True
            # With connection established, update any registers
            for name, trigger in self.triggers.items():
                trigger.register_modbus_client(self.mod_client)
            self.get_all_registers()
        except:
            logging.debug("Connection to trigger modbus client did not succeed.")
            self.connected = False

    def get_all_registers(self):
        """Read the value of all registers to update the tree."""
        if self.connected:
            for name, trigger in self.triggers.items():
                trigger._get_parameters()

    def set_all_timers(self, values):
        """Enable or disable all timers.
        :param values: dict/obj of needed values. (bool) enable, (bool) freerun
        """
        enable = values['enable']
        freerun = values['freerun']
        self.all_triggers_enable = bool(enable)

        # If freerun, write the target as 0 to the trigger without setting the target count.
        # This is to avoid users needing to re-enter the value if the change their mind.
        # The acquisition start still overrides the target if freerun is enabled.
        if freerun:
            for trigger in self.triggers.values():
                write_modbus_float(self.mod_client, 0, trigger.addr['target_hold'])
        else:
            for trigger in self.triggers.values():
                write_modbus_float(self.mod_client, trigger.target, trigger.addr['target_hold'])

        if self.all_triggers_enable:
            logging.debug("Enabling all timers.")
            write_coil(self.mod_client, modAddr.trig_enable_coil, True)
        else:
            logging.debug("Disabling all timers.")
            write_coil(self.mod_client, modAddr.trig_disable_coil, True)  # Coil needs True val

    # Background task functions

    def start_background_tasks(self):
        """Start the background tasks and reset the continuous error counter."""
        logging.debug(f"Launching trigger status update task with interval {self.status_bg_task_interval}.")
        self.status_ioloop_task = PeriodicCallback(
            self.get_all_registers, (self.status_bg_task_interval * 1000)
        )
        self.status_ioloop_task.start()

    def stop_background_tasks(self):
        """Stop the background tasks."""
        self.status_bg_task_enable = False
        self.status_ioloop_task.stop()

    def set_task_enable(self, enable):
        """Set the background task enable - accordingly enable or disable the task."""
        enable = bool(enable)

        if enable != self.status_bg_task_enable:
            if enable:
                self.start_background_tasks()
            else:
                self.stop_background_tasks()

    def set_task_interval(self, interval):
        """Set the background task interval."""
        logging.debug("Setting background task interval to %f", interval)
        self.status_bg_task_interval = float(interval)

