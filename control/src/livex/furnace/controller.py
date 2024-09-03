import logging
import time
import datetime
import socket
from concurrent import futures

from tornado.ioloop import PeriodicCallback
from tornado.concurrent import run_on_executor

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from pymodbus.client import ModbusTcpClient

from livex.furnace.controls.pid import PID
from livex.furnace.controls.gradient import Gradient
from livex.furnace.controls.autoSetPointControl import AutoSetPointControl
from livex.furnace.controls.motor import Motor

from livex.modbusAddresses import modAddr
from livex.filewriter import FileWriter
from livex.util import LiveXError
from livex.util import read_decode_input_reg, read_decode_holding_reg
from livex.packet_decoder import LiveXPacketDecoder

class FurnaceController():
    """FurnaceController - class that communicates with a modbus server on a PLC to drive a furnace."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self, options):
        """Initialise the FurnaceController object.

        This constructor initialises the FurnaceController object, building parameter trees and
        launching the background task to make modbus requests to the PLC.
        """

        # Parse options
        self.bg_read_task_enable = bool(options.get('background_read_task_enable', False))
        self.bg_read_task_interval = float(options.get('background_read_task_interval', 1.0))

        self.bg_stream_task_enable = bool(options.get('background_stream_task_enable', False))
        self.pid_frequency = int(options.get('pid_frequency', 50))

        self.ip = options.get('ip', '192.168.0.159')
        self.port = int(options.get('port', '4444'))

        self.log_directory = options.get('log_directory', 'logs')
        # Filename may instead be generated? Cannot have just one configurable one,
        # subsequent uses would overwrite. generation method TBD. metadata, date/time, etc.
        self.log_filename = options.get('log_filename', 'default.hdf5')

        self.monitor_retention = int(options.get('monitor_retention', 60))

        # Stop modbus from generating excessive logging
        logging.getLogger("pymodbus").setLevel(logging.WARNING)  

        # Buffer will be cleared once per second
        self.buffer_size = self.pid_frequency

        # Interval is smaller than period so that tcp stream can be cleared and not maintained
        self.bg_stream_task_interval = (1/self.pid_frequency)/2

        # Set the background task counters to zero
        self.background_thread_counter = 0

        self.packet_decoder = LiveXPacketDecoder()

        self.file_writer = FileWriter(self.log_directory, self.log_filename, {'timestamps': 'S'})
        
        # File is not open by default in case of multiple acquisitions per software run
        self.file_open_flag = False

        self.tcp_reading = None
        self.stream_buffer = {
            'counter': [],
            'temperature_a': [],
            'temperature_b': []
        }
        self.start_acquisition = False

        self.pid_a = PID(modAddr.addresses_pid_a)
        self.pid_b = PID(modAddr.addresses_pid_b)
        self.gradient = Gradient(modAddr.gradient_addresses)
        self.aspc = AutoSetPointControl(modAddr.aspc_addresses)
        self.motor = Motor(modAddr.motor_addresses)

        self.initialise_clients(value=None)

        # Third thermocouple will get its value from the background task
        self.thermocouple_c = None

        self.lifetime_counter = 0
        self.reconnect = False

        # For monitoring/graphing
        self.monitor_graphs = {
            'timestamp': [],
            'temperature': {
                'temperature_a': [],
                'temperature_b': []
            },
            'output': {
                'output_a': [],
                'output_b': []
            },
            'setpoint': {
                'setpoint_a': [],
                'setpoint_b': []
            }
        }

        bg_task = ParameterTree({
            'thread_count': (lambda: self.background_thread_counter, None),
            'enable': (lambda: self.bg_read_task_enable, self.set_task_enable),
            'interval': (lambda: self.bg_read_task_interval, self.set_task_interval),
        })

        status = ParameterTree({
            'connected': (lambda: self.connected, None),
            'reconnect': (lambda: self.reconnect, self.initialise_clients),
            'full_stop': (lambda: None, self.stop_all_pid)
        })

        tcp = ParameterTree({
            'tcp_reading': (lambda: self.tcp_reading, None),
            'acquire': (lambda: self.start_acquisition, self.set_acquisition)
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'status': status,
            'background_task': bg_task,
            'pid_a': self.pid_a.tree,
            'pid_b': self.pid_b.tree,
            'thermocouples': {
                'centre': (lambda: self.thermocouple_c, None)
            },
            'autosp': self.aspc.tree,
            'gradient': self.gradient.tree,
            'motor': self.motor.tree,
            'tcp': tcp,
            'monitor': (lambda: self.monitor_graphs, None),
            'filewriter': {
                'filepath': (lambda: self.file_writer.filepath, self.set_filepath),
                'filename': (lambda: self.file_writer.filename, self.set_filename)
            }
        })

        # Launch the background task if enabled in options
        if self.bg_read_task_enable:
            self.start_background_tasks()

    def initialize(self, adapters) -> None:
        """Initialize the controller.

        This method initializes the controller with information about the adapters loaded into the
        running application.

        :param adapters: dictionary of adapter instances
        """
        self.adapters = adapters
        if 'sequencer' in self.adapters:
            logging.debug("Furnace controller registering context with sequencer")
            self.adapters['sequencer'].add_context('furnace', self)

    def cleanup(self):
        """Clean up the FurnaceController instance.

        This method stops the background tasks, allowing the adapter state to be cleaned up
        correctly.
        """
        self.mod_client.close()
        self.tcp_client.close()
        self.stop_background_tasks()

    def get(self, path, with_metadata=False):
        """Get parameter data from controller.

        This method gets data from the controller parameter tree.

        :param path: path to retrieve from the tree
        :param with_metadata: flag indicating if parameter metadata should be included
        :return: dictionary of parameters (and optional metadata) for specified path
        """
        try:
            return self.param_tree.get(path, with_metadata)
        except ParameterTreeError as error:
            logging.error(error)
            raise LiveXError(error)

    def set(self, path, data):
        """Set parameters in the controller.

        This method sets parameters in the controller parameter tree. If the parameters to write
        metadata to HDF and/or markdown have been set during the call, the appropriate write
        action is executed.

        :param path: path to set parameters at
        :param data: dictionary of parameters to set
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as error:
            logging.error(error)

    def set_filename(self, value):
        """Set the filewriter's filename and update its path."""
        if not value.endswith('.hdf5'):
            value += '.hdf5'
        self.file_writer.filename = value
        self.file_writer.set_fullpath()

    def set_filepath(self, value):
        """Set the filewriter's filename and update its path."""
        self.file_writer.filepath = value
        self.file_writer.set_fullpath()

    def stop_all_pid(self, value):
        """Disable all/both PIDs, setting their gpio output to 0. Acts as an 'emergency stop'."""
        self.pid_a.set_enable(False)
        self.pid_b.set_enable(False)

    # Data acquiring tasks

    def set_acquisition(self, value):
        """Toggle whether the system is acquiring data."""
        value = bool(value)
        logging.debug("Toggled acquisition")

        if value:
            # Send signal to
            self.mod_client.write_coil(modAddr.acquisition_coil, 1, slave=1)
            self.file_writer.open_file()
            self.file_open_flag = True
        else:
            self.mod_client.write_coil(modAddr.acquisition_coil, 0, slave=1)

            # If ending an acquisition, clear the buffer
            self.file_writer.write_hdf5(
                self.stream_buffer,
                'temperature_readings'
            )
            for key in self.stream_buffer:
                self.stream_buffer[key].clear()

            self.file_writer.close_file()
            self.file_open_flag = False

        self.start_acquisition = value

    def initialise_clients(self, value):
        """Instantiate a ModbusTcpClient and provide it to the PID controllers."""
        logging.debug("Attempting to establish modbus connection")

        try:
            self.mod_client = ModbusTcpClient(self.ip)
            self.mod_client.connect()
            # With connection established, populate trees and provide correct connection
            self.pid_a.register_modbus_client(self.mod_client)
            self.pid_b.register_modbus_client(self.mod_client)
            self.gradient.register_modbus_client(self.mod_client)
            self.aspc.register_modbus_client(self.mod_client)
            self.motor.register_modbus_client(self.mod_client)

            self.connected = True
        except:
            logging.debug("Connection to modbus client did not succeed.")
            self.connected = False

        self.initialise_tcp_client()

    def initialise_tcp_client(self):
        """Initialise the tcp client."""

        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((self.ip, self.port))

        self.tcp_client.settimeout(0.1)
        activate = '1'
        self.tcp_client.send(activate.encode())

    def close_tcp_client(self):
        """Safely end the TCP connection."""
        self.tcp_client.close()

    def _trim_dict_to_retention(self, toTrim):
        """Iterate through a dictionary and trim its lists down to the retention length.
        Purpose-made for the self.monitor_graphs dictionary. Could be edited to use a given target.
        """
        for key, value in toTrim.items():
            if isinstance(value, dict):
                self._trim_dict_to_retention(value)
            elif isinstance(value, list):
                while (len(value) > self.monitor_retention):
                    value.pop(0)

    def background_ioloop_callback(self):
        """Ioloop callback function to populate the monitor graph variables."""

        self._trim_dict_to_retention(self.monitor_graphs)

        # Add data
        cur_time = datetime.datetime.now()
        cur_time = cur_time.strftime("%H:%M:%S")

        self.monitor_graphs['timestamp'].append(cur_time)

        self.monitor_graphs['temperature']['temperature_a'].append(self.pid_a.thermocouple)
        self.monitor_graphs['temperature']['temperature_b'].append(self.pid_b.thermocouple)

        self.monitor_graphs['output']['output_a'].append(self.pid_a.output)
        self.monitor_graphs['output']['output_b'].append(self.pid_b.output)

        self.monitor_graphs['setpoint']['setpoint_a'].append(self.pid_a.setpoint)
        self.monitor_graphs['setpoint']['setpoint_b'].append(self.pid_b.setpoint)

        # self.background_ioloop_counter += 1

    @run_on_executor
    def background_stream_task(self):
        """Instruct the packet decoder to receive an object, then put that object
        in the parameter tree.
        """
        while self.bg_stream_task_enable:
            if self.start_acquisition:
                try:
                    reading = self.tcp_client.recv(self.packet_decoder.size) # fff: 12
                    logging.debug(self.packet_decoder.counter)
                    reading = self.packet_decoder.unpack(reading)

                except socket.timeout:
                    logging.debug("TCP Socket timeout: read no data")
                    continue  # If no data received, do not use the packet_decoding logic
                except Exception as e:
                    logging.debug(f"Other TCP error: {str(e)}")
                    logging.debug("Halting background tasks")
                    self.stop_background_tasks()
                    break

                self.tcp_reading = self.packet_decoder.as_dict()

                self.stream_buffer['counter'].append(self.packet_decoder.counter)
                self.stream_buffer['temperature_a'].append(self.packet_decoder.temperature_a)
                self.stream_buffer['temperature_b'].append(self.packet_decoder.temperature_b)

                if len(self.stream_buffer['counter']) == 50:
                    self.file_writer.write_hdf5(
                        data=self.stream_buffer,
                        groupname="temperature_readings"
                    )
                    # Clear the buffer
                    for key in self.stream_buffer:
                        self.stream_buffer[key].clear()

                    secondary_data = {
                        'counter': [self.packet_decoder.counter],
                        'setpoint_a': [self.pid_a.setpoint],
                        'setpoint_b': [self.pid_b.setpoint],
                        'output_a': [self.pid_a.output],
                        'output_b': [self.pid_b.output]
                    }
                    self.file_writer.write_hdf5(
                        data=secondary_data,
                        groupname="secondary_readings"
                    )

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

                    self.thermocouple_c = read_decode_input_reg(self.mod_client, modAddr.thermocouple_c_inp)

                    self.lifetime_counter = read_decode_input_reg(self.mod_client, modAddr.counter_inp)

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
                    self.tcp_client.close()
                    # Close both for safety and consistency
                    logging.debug("Modbus communication error, pausing reads")
                    self.connected = False

                self.background_thread_counter += 1

            else:
                # logging.debug("Awaiting reconnection")
                pass
            
            time.sleep(self.bg_read_task_interval)

        logging.debug("Background thread task stopping")

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
        self.background_stream_task()
        self.background_read_task()

    def stop_background_tasks(self):
        """Stop the background tasks."""
        if self.file_open_flag:  # Ensure file is closed properly
            self.file_writer.close_file()

        self.bg_read_task_enable = False
        self.bg_stream_task_enable = False
        self.background_ioloop_task.stop()
