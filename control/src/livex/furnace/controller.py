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

    def __init__(self,
                 bg_read_task_enable, bg_read_task_interval, bg_stream_task_enable, pid_frequency,
                 ip, port,
                 log_directory, log_filename,
                 temp_monitor_retention
        ):
        """Initialise the FurnaceController object.

        This constructor initialises the FurnaceController object, building parameter trees and
        launching the background task to make modbus requests to the PLC.
        """
        logging.getLogger("pymodbus").setLevel(logging.WARNING)  # Stop modbus from filling console

        # Save arguments
        self.bg_read_task_enable = bg_read_task_enable
        self.bg_read_task_interval = bg_read_task_interval
        self.bg_stream_task_enable = bg_stream_task_enable

        # Buffer will be cleared once per second
        self.buffer_size = pid_frequency
        # Interval is smaller than period so that tcp stream can be cleared and not maintained
        self.bg_stream_task_interval = (1/pid_frequency)/2

        self.log_directory = log_directory
        self.log_filename = log_filename

        # Set the background task counters to zero
        self.background_thread_counter = 0

        # Modbus and tree setup
        logging.debug("Initial modbus connection")
        self.ip = ip
        self.port = port
        self.mod_client = ModbusTcpClient(self.ip)
        self.initialise_tcp_client()

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

        self.pid_a = PID(self.mod_client, modAddr.addresses_pid_a)
        self.pid_b = PID(self.mod_client, modAddr.addresses_pid_b)
        self.gradient = Gradient(self.mod_client, modAddr.gradient_addresses)
        self.aspc = AutoSetPointControl(self.mod_client, modAddr.aspc_addresses)
        self.motor = Motor(self.mod_client, modAddr.motor_addresses)

        # Other display controls
        self.thermocouple_a = read_decode_input_reg(self.mod_client, modAddr.thermocouple_a_inp)
        self.thermocouple_b = read_decode_input_reg(self.mod_client, modAddr.thermocouple_b_inp)

        self.lifetime_counter = 0
        self.connected = True
        self.reconnect = False

        # For the temperature monitor
        self.temp_monitor_graph = {
            'timestamp': [],
            'temperature_a': [],
            'temperature_b': []
        }
        self.temp_monitor_retention = temp_monitor_retention

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
            'autosp': self.aspc.tree,
            'gradient': self.gradient.tree,
            'motor': self.motor.tree,
            'tcp': tcp,
            'temp_monitor': (lambda: self.temp_monitor_graph, None),
            'filewriter': {
                'filepath': (lambda: self.file_writer.filepath, self.set_filepath),
                'filename': (lambda: self.file_writer.filename, self.set_filename)
            }
        })

        # Launch the background task if enabled in options
        if self.bg_read_task_enable:
            self.start_background_tasks()

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
        self.connected = True

        self.mod_client = ModbusTcpClient(self.ip)
        self.mod_client.connect()

        self.pid_a.register_modbus_client(self.mod_client)
        self.pid_b.register_modbus_client(self.mod_client)
        self.gradient.register_modbus_client(self.mod_client)
        self.aspc.register_modbus_client(self.mod_client)
        self.motor.register_modbus_client(self.mod_client)

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

    def background_ioloop_callback(self):
        """background task IOLoop callback
        may be swapped to be a thread for the reading"""

        # Check retention
        for key in self.temp_monitor_graph.keys():
            if len(self.temp_monitor_graph[key]) >= self.temp_monitor_retention:
                self.temp_monitor_graph[key].pop(0)

        # Add data
        cur_time = datetime.datetime.now()
        cur_time = cur_time.strftime("%H:%M:%S")
        self.temp_monitor_graph['timestamp'].append(cur_time)
        self.temp_monitor_graph['temperature_a'].append(self.pid_a.thermocouple)
        self.temp_monitor_graph['temperature_b'].append(self.pid_b.thermocouple)

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

    # Adapter processes

    def get(self, path):
        """Get the parameter tree.
        This method returns the parameter tree for use by clients via the FurnaceController adapter.
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
        """Clean up the FurnaceController instance.

        This method stops the background tasks, allowing the adapter state to be cleaned up
        correctly.
        """
        self.mod_client.close()
        self.tcp_client.close()
        self.stop_background_tasks()