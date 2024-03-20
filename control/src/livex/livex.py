import logging
import time
from concurrent import futures

from tornado.ioloop import PeriodicCallback
from tornado.concurrent import run_on_executor

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions

from pymodbus.client import ModbusTcpClient

from livex.modbusAddresses import modAddr
from livex.controls.pid import PID
from livex.controls.gradient import Gradient
from livex.controls.autoSetPointControl import AutoSetPointControl
from livex.controls.motor import Motor

from livex.util import LiveXError
from livex.util import read_decode_input_reg, read_decode_holding_reg
from livex.packet_decoder import LiveXPacketDecoder

class LiveX():
    """LiveX - class that communicates with a modbus server on a PLC to drive a furnace.

    """

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self, bg_read_task_enable, bg_read_task_interval, bg_stream_task_enable, bg_stream_task_interval):
        """Initialise the LiveX object.

        This constructor initlialises the LiveX object, building parameter trees and
        launching the background task to make modbus requests to the device.
        """
        logging.getLogger("pymodbus").setLevel(logging.WARNING)  # Stop modbus from filling console

        # Save arguments
        self.bg_read_task_enable = bg_read_task_enable
        self.bg_read_task_interval = bg_read_task_interval
        self.bg_stream_task_enable = bg_stream_task_enable
        self.bg_stream_task_interval = bg_stream_task_interval

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        # Set the background task counters to zero
        self.background_thread_counter = 0

        # Modbus and tree setup
        logging.debug("Initial modbus connection")
        self.ip = '192.168.0.159'
        self.port = 4444
        self.mod_client = ModbusTcpClient(self.ip)

        self.packet_decoder = LiveXPacketDecoder(self.ip, self.port)
        self.packet_decoder.initialise_tcp_client()

        self.tcp_reading = None
        self.start_acquisition = False

        self.pid_a = PID(self.mod_client, modAddr.addresses_pid_a)
        self.pid_b = PID(self.mod_client, modAddr.addresses_pid_b)
        self.gradient = Gradient(self.mod_client, modAddr.gradient_addresses)
        self.aspc = AutoSetPointControl(self.mod_client, modAddr.aspc_addresses)
        self.motor = Motor(self.mod_client, modAddr.motor_addresses)

        # Other display controls
        self.thermocouple_a = read_decode_input_reg(self.mod_client, modAddr.thermocouple_a_inp)
        self.thermocouple_b = read_decode_input_reg(self.mod_client, modAddr.thermocouple_b_inp)

        self.reading_counter = 0
        self.connected = True
        self.reconnect = False

        bg_task = ParameterTree({
            'thread_count': (lambda: self.background_thread_counter, None),
            'enable': (lambda: self.bg_read_task_enable, self.set_task_enable),
            'interval': (lambda: self.bg_read_task_interval, self.set_task_interval),
        })

        status = ParameterTree({
            'odin_version': version_info['version'],
            'server_uptime': (self.get_server_uptime, None),
            'connected': (lambda: self.connected, None),
            'reconnect': (lambda: self.reconnect, self.initialise_clients)
        })

        tcp = ParameterTree({
            'tcp_reading': (lambda: self.tcp_reading, None),
            'acquire': (lambda: self.start_acquisition, self.toggle_acquisition)
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'status': status,
            'background_task': bg_task,
            'pid_a': self.pid_a.tree,
            'pid_b': self.pid_b.tree,
            'autosp': self.aspc.tree,
            'gradient': self.gradient.tree,
            'motor': self.motor.tree,
            'tcp': tcp
        })

        # Launch the background task if enabled in options
        if self.bg_read_task_enable:
            logging.debug("Starting bg tasks")
            self.start_background_tasks()

    # Data acquiring tasks

    def toggle_acquisition(self, value):
        """Toggle whether the system is acquiring data."""
        value = bool(value)
        self.start_acquisition = value

        logging.debug("Toggled acquisition")

        if value:
            self.mod_client.write_coil(modAddr.acquisition_coil, 1, slave=1)
        else:
            self.mod_client.write_coil(modAddr.acquisition_coil, 0, slave=1)

    def initialise_adapters(self, adapters):
        """Initialise any adapters that this one needs access to.
        :param adapters: dict of adapters from adapter.py
        """
        self.graph_adapter = adapters['graph']

    def initialise_clients(self, value):
        """Instantiate a ModbusTcpClient and provide it to the PID controllers."""
        logging.debug("Attempting to establish modbus connection")
        self.mod_client = ModbusTcpClient(self.ip)
        self.mod_client.connect()

        self.packet_decoder.initialise_tcp_client()

        self.connected = True

        self.pid_a.register_modbus_client(self.mod_client)
        self.pid_b.register_modbus_client(self.mod_client)
        self.gradient.register_modbus_client(self.mod_client)
        self.aspc.register_modbus_client(self.mod_client)
        self.motor.register_modbus_client(self.mod_client)

    def push_data(self, key, data):
        """Push data to the graph adapter dataset(s).
        :param key: key in dataset
        :param data: value to append to list in key
        """
        self.graph_adapter.datasets['thermocouples'].data[key].append(data)

        self.graph_adapter.datasets['thermocouples_long'].data[key].append(data)

    def background_ioloop_callback(self):
        """background task IOLoop callback
        may be swapped to be a thread for the reading"""
        self.push_data('temp_a', self.pid_a.thermocouple)
        self.push_data('temp_b', self.pid_b.thermocouple)

        # self.background_ioloop_counter += 1

    @run_on_executor
    def background_stream_task(self):
        """Instruct the packet decoder to receive an object, then put that object
        in the parameter tree.
        """
        while self.bg_stream_task_enable:
            success = self.packet_decoder.receive()
            if not success:
                logging.debug("Unexpected exception, stopping background tasks.")
                self.stop_background_tasks()
            self.tcp_reading = self.packet_decoder.as_dict()
            time.sleep(self.bg_stream_task_interval)

    @run_on_executor
    def background_read_task(self):
        """The adapter background thread task.

        This method runs in the thread executor pool, sleeping for the specified interval and 
        incrementing its counter once per loop, until the background task enable is set to false.
        """
        while self.bg_read_task_enable:

            if self.connected:
                # Get any value updated by the device
                # Mostly input registers, except for setpoints which can change automatically
                try:
                    self.pid_a.thermocouple = read_decode_input_reg(self.mod_client, modAddr.thermocouple_a_inp)
                    self.pid_b.thermocouple = read_decode_input_reg(self.mod_client, modAddr.thermocouple_b_inp)

                    self.reading_counter = read_decode_input_reg(self.mod_client, modAddr.counter_inp)

                    self.pid_a.output    = read_decode_input_reg(self.mod_client, modAddr.pid_output_a_inp)
                    self.pid_b.output    = read_decode_input_reg(self.mod_client, modAddr.pid_output_b_inp)

                    self.gradient.actual      = read_decode_input_reg(self.mod_client, modAddr.gradient_actual_inp)
                    self.gradient.theoretical = read_decode_input_reg(self.mod_client, modAddr.gradient_theory_inp)

                    self.pid_a.gradient_setpoint = read_decode_input_reg(self.mod_client, modAddr.gradient_setpoint_a_inp)
                    self.pid_b.gradient_setpoint = read_decode_input_reg(self.mod_client, modAddr.gradient_setpoint_b_inp)

                    self.aspc.midpt = read_decode_input_reg(self.mod_client, modAddr.autosp_midpt_inp)

                    self.pid_a.setpoint = read_decode_holding_reg(self.mod_client, modAddr.pid_setpoint_a_hold)
                    self.pid_b.setpoint = read_decode_holding_reg(self.mod_client, modAddr.pid_setpoint_b_hold)

                    self.motor.lvdt = read_decode_input_reg(self.mod_client, modAddr.motor_lvdt_inp)

                except:
                    self.mod_client.close()
                    self.packet_decoder.close_tcp_client()
                    # Close both for safety and consistency
                    logging.debug("Modbus communication error, pausing reads")
                    self.connected = False

                self.background_thread_counter += 1

            else:
                # logging.debug("Awaiting reconnection")
                pass
            
            time.sleep(self.bg_read_task_interval)

        logging.debug("Background thread task stopping")

    # Adapter processes

    def get_server_uptime(self):
        """Get the uptime for the ODIN server.

        This method returns the current uptime for the ODIN server.
        """
        return time.time() - self.init_time

    def get(self, path):
        """Get the parameter tree.

        This method returns the parameter tree for use by clients via the LiveX adapter.

        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree.

        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate LiveXError.

        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise LiveXError(e)

    def cleanup(self):
        """Clean up the LiveX instance.

        This method stops the background tasks, allowing the adapter state to be cleaned up
        correctly.
        """
        self.mod_client.close()
        self.packet_decoder.close_tcp_client()
        self.stop_background_tasks()

    # Background tasks

    def set_task_enable(self, enable):
        """Set the background task enable."""
        enable = bool(enable)

        if enable != self.bg_read_task_enable:
            if enable:
                self.start_background_tasks()
            else:
                self.stop_background_tasks()

    def set_task_interval(self, interval):
        """Set the background task interval."""
        logging.debug("Setting background task interval to %f", interval)
        self.bg_read_task_interval = float(interval)

    def start_background_tasks(self):
        """Start the background tasks."""
        logging.debug(
            "Launching background tasks with interval %.2f secs", self.bg_read_task_interval
        )
        self.bg_read_task_enable = True
        self.bg_stream_task_enable = True

        self.background_ioloop_task = PeriodicCallback(
            self.background_ioloop_callback, 1000
        )  # Hardcode interval for now
        self.background_ioloop_task.start()

        # Run the background thread task in the thread execution pool
        logging.debug("starting them!")
        self.background_stream_task()
        logging.debug("started the stream one")
        self.background_read_task()

    def stop_background_tasks(self):
        """Stop the background tasks."""
        self.bg_read_task_enable = False
        self.bg_stream_task_enable = False
        self.background_ioloop_task.stop()
