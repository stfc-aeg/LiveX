import logging
from pymodbus.client import ModbusTcpClient
from livex.util import read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil
from livex.modbusAddresses import modAddr

from tornado.ioloop import PeriodicCallback

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

class TriggerError():
    """Simple exception class to wrap lower-level exceptions."""
    pass

class TriggerController():
    """Class to instantiate and manage a modbus connection to control the triggering device."""

    def __init__(self, ip, frequencies, status_bg_task_enable, status_bg_task_interval):

        self.ip = ip
        self.status_bg_task_enable = status_bg_task_enable
        self.status_bg_task_interval = status_bg_task_interval

        self.furnace_freq = frequencies['furnace']
        self.widefov_freq = frequencies['wideFov']
        self.narrowfov_freq = frequencies['narrowFov']

        # Intervals in microseconds
        self.intvl_furnace = (1_000_000/self.furnace_freq) // 2
        self.intvl_wideFov = (1_000_000/self.widefov_freq) // 2
        self.intvl_narrowFov = (1_000_000/self.narrowfov_freq) // 2

        self.all_enabled = False
        self.furnace_enabled = False
        self.widefov_enabled = False
        self.narrowfov_enabled = False

        self.furnace_target = 0
        self.widefov_target = 0
        self.narrowfov_target = 0

        self.initialise_client()
        self.get_all_registers()

        self.previewing = False

        if self.status_bg_task_enable:
            self.start_background_tasks()

        self.tree = ParameterTree({
            'furnace': {
                'enable': (lambda: self.furnace_enabled, self.toggle_furnace_enable),
                'frequency': (lambda: self.furnace_freq, self.set_furnace_interval),
                'target': (lambda: self.furnace_target, self.set_furnace_target)
            },
            'widefov': {
                'enable': (lambda: self.widefov_enabled, self.toggle_widefov_enable),
                'frequency': (lambda: self.widefov_freq, self.set_widefov_interval),
                'target': (lambda: self.widefov_target, self.set_widefov_target)
            },
            'narrowfov': {
                'enable': (lambda: self.narrowfov_enabled, self.toggle_narrowfov_enable),
                'frequency': (lambda: self.narrowfov_freq, self.set_narrowfov_interval),
                'target': (lambda: self.narrowfov_target, self.set_narrowfov_target)
            },
            'background': {
                'interval': (lambda: self.status_bg_task_interval, self.set_task_interval),
                'enable': (lambda: self.status_bg_task_enable, self.set_task_enable)
            },
            'preview': (lambda: self.previewing, self.set_preview),
            'all_timers_enable': (lambda: self.all_enabled, self.set_all_timers)
        })

    def initialise_client(self):
        """Initialise the modbus client."""
        self.mod_client = ModbusTcpClient(self.ip)
        self.mod_client.connect()

    def get_all_registers(self):
        """Read the value of all registers to update the tree."""
        ret = self.mod_client.read_coils(modAddr.trig_furnace_enable_coil, 3, slave=1)
        # See modbusAddresses.py: these coils are sequential
        self.furnace_enabled = ret.bits[0]  # Coil 2
        self.widefov_enabled = ret.bits[1]  # Coil 3
        self.narrowfov_enabled = ret.bits[2]  # Coil 4

        # Frequencies = 1_000_000 / intvl*2
        # Interval = (1_000_000 / freq) // 2
        self.furnace_freq = 1_000_000 / (
            read_decode_holding_reg(self.mod_client, modAddr.trig_furnace_intvl_hold) * 2
        )
        self.widefov_freq = 1_000_000 / (
            read_decode_holding_reg(self.mod_client, modAddr.trig_widefov_intvl_hold) * 2
        )
        self.narrowfov_freq = 1_000_000 / (
            read_decode_holding_reg(self.mod_client, modAddr.trig_narrowfov_intvl_hold) * 2
        )

        # Frame targets
        self.furnace_target = read_decode_holding_reg(self.mod_client, modAddr.trig_furnace_target_hold)
        self.widefov_target = read_decode_holding_reg(self.mod_client, modAddr.trig_widefov_target_hold)
        self.narrowfov_target = read_decode_holding_reg(self.mod_client, modAddr.trig_narrowfov_target_hold)

    def set_all_timers(self, value):
        """Enable or disable all timers."""
        self.all_triggers_enable = bool(value)
        self.furnace_enabled = True
        self.widefov_enabled = True
        self.narrowfov_enabled = True
        toWrite = [value, value, value]
        self.mod_client.write_coils(modAddr.trig_furnace_enable_coil, toWrite, slave=1)
        write_coil(self.mod_client, modAddr.trig_val_updated_coil, 1)

    def set_preview(self, value):
        """Enable or disable the preview mode (timers do not increment frame counters)."""
        value = bool(value)
        write_coil(self.mod_client, modAddr.trig_preview_coil, value)

    def check_all_enable(self):
        """Check if all timers are enabled."""
        if self.furnace_enabled and self.widefov_enabled and self.narrowfov_enabled:
            self.all_enabled = True
        else:
            self.all_enabled = False

    def update_hold_value(self, address, value):
        """Write a value to a given holding register(s) and mark the 'value updated' coil."""
        write_modbus_float(self.mod_client, float(value), address)
        write_coil(self.mod_client, modAddr.trig_val_updated_coil, 1)

        self.check_all_enable()  # Not relevant for the intervals but still best fit here

    def set_furnace_interval(self, value):
        """Update the interval of the furnace timer."""
        self.intvl_furnace = (1_000_000 / value) //2
        self.update_hold_value(modAddr.trig_furnace_intvl_hold, self.intvl_furnace)

    def toggle_furnace_enable(self, value):
        """Toggle the furnace timer."""
        self.furnace_enabled = not self.furnace_enabled
        write_coil(self.mod_client, modAddr.trig_furnace_enable_coil, bool(self.furnace_enabled))

    def set_furnace_target(self, value):
        """Update the target framecount of the furnace timer."""
        self.furnace_target = int(value)  # Target could be int or float. Int is safer
        self.update_hold_value(modAddr.trig_furnace_target_hold, self.furnace_target)

    def set_widefov_interval(self, value):
        """Update the interval of the WideFov camera timer."""
        self.intvl_wideFov = (1_000_000 / value) // 2
        self.update_hold_value(modAddr.trig_widefov_intvl_hold, self.intvl_wideFov)

    def toggle_widefov_enable(self, value):
        """Toggle the widefov timer."""
        self.widefov_enabled = not self.widefov_enabled
        write_coil(self.mod_client, modAddr.trig_widefov_enable_coil, bool(self.widefov_enabled))

    def set_widefov_target(self, value):
        """Set the target of the widefov timer."""
        self.widefov_target = int(value)
        self.update_hold_value(modAddr.trig_widefov_target_hold, self.widefov_target)
        # write_modbus_float(self.mod_client, float(self.widefov_target), modAddr.trig_widefov_target_hold)

    def set_narrowfov_interval(self, value):
        """Update the interval of the NarrowFov camera timer."""
        self.intvl_narrowFov = (1_000_000 / value)//2
        self.update_hold_value(modAddr.trig_narrowfov_intvl_hold, self.intvl_narrowFov)

    def toggle_narrowfov_enable(self, value):
        """Toggle the narrowfov timer."""
        self.narrowfov_enabled = not self.narrowfov_enabled
        write_coil(self.mod_client, modAddr.trig_narrowfov_enable_coil, bool(self.narrowfov_enabled))

    def set_narrowfov_target(self, value):
        """"Set the target value of the narrowfov timer."""
        logging.debug(f"SETTING NARROWFOV TARGET TO {value}")
        self.narrowfov_target = int(value)
        self.update_hold_value(modAddr.trig_narrowfov_target_hold, self.narrowfov_target)

    # Background task functions

    def start_background_tasks(self):
        """Start the background tasks and reset the continuous error counter."""
        self.error_consecutive = 0

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