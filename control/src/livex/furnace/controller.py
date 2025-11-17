import logging
import time
import socket
from concurrent import futures
from functools import partial

from tornado.concurrent import run_on_executor

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from pymodbus.client import ModbusTcpClient

from livex.furnace.controls.pid import PID
from livex.furnace.controls.gradient import Gradient
from livex.furnace.controls.autoSetPointControl import AutoSetPointControl
from livex.furnace.controls.thermocoupleManager import ThermocoupleManager

from livex.modbusAddresses import modAddr
from livex.filewriter import FileWriter
from livex.util import LiveXError
from livex.util import read_decode_input_reg, read_decode_holding_reg, write_modbus_float, write_coil
from livex.packet_decoder import LiveXPacketDecoder

from livex.mockModbusClient import MockModbusClient, MockPLC, MockTCPClient

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
        self.bg_read_task_enable = bool(int(options.get('background_read_task_enable', False)))
        self.bg_read_task_interval = float(options.get('background_read_task_interval', 1.0))

        self.bg_stream_task_enable = bool(int(options.get('background_stream_task_enable', False)))
        self.pid_frequency = int(options.get('pid_frequency', 50))

        self.max_setpoint = int(options.get('max_setpoint', 1500))
        self.max_setpoint_increase = int(options.get('max_setpoint_increase', 150))
        max_autosp_rate = int(options.get('max_autosp_rate', 8))

        self.allow_solo_acquisition = bool(int(options.get('allow_furnace_only_acquisition', 0)))
        self.allow_pid_override = bool(int(options.get('allow_pid_override', 0)))

        self.ip = options.get('ip', '192.168.0.159')
        self.port = int(options.get('port', '4444'))

        self.tc_indices = options.get('thermocouple_indices', '0,1,2,3,4,5')
        self.tc_indices = [int(val) for val in self.tc_indices.strip(" ").split(",")]

        self.mocking = bool(int(options.get('use_mock_client', 0)))
        pid_debug = bool(int(options.get('pid_debug', 0)))

        # File name and directory is a default that is later overwritten by metadata
        self.log_directory = options.get('log_directory', 'logs')
        self.log_filename = options.get('log_filename', 'default.hdf5')

        # Get default values for PIDs
        pid_defaults = {
            'setpoint': float(options.get('setpoint_default', 30.0)),
            'kp': float(options.get('kp_default', 25.5)),
            'ki': float(options.get('ki_default', 5.0)),
            'kd': float(options.get('kd_default', 0.1))
        }

        # Stop modbus from generating excessive logging
        logging.getLogger("pymodbus").setLevel(logging.WARNING)

        # Buffer will be cleared once per second
        self.buffer_size = self.pid_frequency

        # Interval is smaller than period so that tcp stream can be cleared and not maintained
        self.bg_stream_task_interval = (1/self.pid_frequency)/2

        # Set the background task counters to zero
        self.background_thread_counter = 0

        self.file_writer = FileWriter(self.log_directory, self.log_filename, 
            dtypes={'timestamps': 'S', 'key': 'str', 'event_key': 'str', 'event_value': 'str'}
        )
        
        # File is not open by default in case of multiple acquisitions per software run
        self.file_open_flag = False

        self.tcp_reading = None

        # Create packet decoder and stream buffer for TCP values sent by PLC
        # If pid_debug is true (and set in the PLC as well), this is a range of PID behaviour data
        data_groupname = str(options.get('data_groupname', 'fast_data'))

        self.packet_decoder = LiveXPacketDecoder(pid_debug=pid_debug)
        self.stream_buffer= {key: [] for key in self.packet_decoder.data.keys()}  # Same data structure
        self.event_buffer = []
        self.data_groupname = data_groupname

        self.acquiring = False

        self.tc_manager = ThermocoupleManager(options)
        self.pid_upper = PID(modAddr.addresses_pid_upper, pid_defaults, self.max_setpoint, self.max_setpoint_increase, self)
        self.pid_lower = PID(modAddr.addresses_pid_lower, pid_defaults, self.max_setpoint, self.max_setpoint_increase, self)
        self.gradient = Gradient(modAddr.gradient_addresses, self)
        self.aspc = AutoSetPointControl(modAddr.aspc_addresses, max_autosp_rate, self)

        self._initialise_clients(value=None)

        self.lifetime_counter = 0

        self.bg_task_subtree = ParameterTree({
            'thread_count': (lambda: self.background_thread_counter, None),
            'enable': (lambda: self.bg_read_task_enable, self.set_task_enable),
            'interval': (lambda: self.bg_read_task_interval, self.set_task_interval),
        })

        self.status_subtree = ParameterTree({
            'connected': (lambda: self.connected, None),
            'reconnect': (lambda: None, self._initialise_clients),
            'full_stop': (lambda: None, self.stop_all_pid),
            'allow_solo_acquisition': (lambda: self.allow_solo_acquisition, None),
            'allow_pid_override': (lambda: self.allow_pid_override, None)
        })

        self.tcp_subtree = ParameterTree({
            'tcp_reading': (lambda: self.tcp_reading, None),
            'acquire': (lambda: self.acquiring, self.solo_acquisition)
        })

        self.param_tree = {}

        # Launch the background task if enabled in options
        if self.bg_read_task_enable:
            self._start_background_tasks()

    def initialize(self, adapters) -> None:
        """Initialize the controller.

        This method initializes the controller with information about the adapters loaded into the
        running application.

        :param adapters: dictionary of adapter instances
        """
        self.adapters = adapters
        if 'metadata' in self.adapters:
            self.metadata = self.adapters['metadata']
        if 'sequencer' in self.adapters:
            logging.debug("Furnace controller registering context with sequencer")
            self.adapters['sequencer'].add_context('furnace', self)
        if 'livex' in self.adapters:
            self.livex = self.adapters['livex'].controller

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'status': self.status_subtree,
            'background_task': self.bg_task_subtree,
            'pid_upper': self.pid_upper.tree,
            'pid_lower': self.pid_lower.tree,
            'max_setpoint_increase': (lambda:
                self.max_setpoint_increase, self.set_max_setpoint_increase, {'min':1}),
            'autosp': self.aspc.tree,
            'gradient': self.gradient.tree,
            'tcp': self.tcp_subtree,
            'filewriter': {
                'filepath': (lambda: self.file_writer.filepath, self._set_filepath),
                'filename': (lambda: self.file_writer.filename, self._set_filename)
            },
            'thermocouples': self.tc_manager.tree
        })

    def set_max_setpoint_increase(self, value):
        """Set the maximum setpoint increase for both PID objects.

        This method sets the max_setpoint_increase attribute for both PID objects,
        which is why it is in the furnace instead of PID controller class.
        :param value: value to set the max_setpoint_increase to
        """
        self.max_setpoint_increase = value
        self.pid_upper.max_setpoint_increase = self.max_setpoint_increase
        self.pid_lower.max_setpoint_increase = self.max_setpoint_increase

    def cleanup(self):
        """Clean up the FurnaceController instance.

        This method stops the background tasks, allowing the adapter state to be cleaned up
        correctly.
        """
        self.mod_client.close()
        self.tcp_client.close()
        self._stop_background_tasks()

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

    def _set_filename(self, value):
        """Set the filewriter's filename and update its path."""
        if not value.endswith('.h5'):
            value += '.h5'
        self.file_writer.filename = value
        self.file_writer.set_fullpath()

    def _set_filepath(self, value):
        """Set the filewriter's filename and update its path."""
        self.file_writer.filepath = value
        self.file_writer.set_fullpath()

    def stop_all_pid(self, value=None):
        """Disable all/both PIDs, setting their gpio output to 0. Acts as an 'emergency stop'."""
        self.pid_upper.set_enable(False)
        self.pid_lower.set_enable(False)

    # Data acquiring tasks

    def solo_acquisition(self, value):
        """Call up to the livex adapter to start or stop a furnace-only acquisition"""
        """Toggle whether the system is acquiring data.
        :param value: boolean, setting acquisition to stop or start.
        """
        if not self.allow_solo_acquisition:
            logging.warning("Furnace-only acquisition is disabled in the configuration.")
            return
        value = bool(value)
        logging.debug(f"Toggled furnace acquisition to {value}.")

        if value:
            self.livex.start_acquisition(acquisitions={'furnace':True})
        else:
            self.livex.stop_acquisition()

    def _start_acquisition(self):
        """Start the acquisition process for the furnace control."""
        # Send signal to modbus to start writing data
        self.mod_client.write_coil(modAddr.acquisition_coil, 1, slave=1)
        self.file_writer.open_file()
        self.file_open_flag = True

        self.acquiring = True

    def _stop_acquisition(self):
        """End the acquisition process for the furnace control, writing out any remaining data."""
        # Tell PLC to stop sending data
        self.mod_client.write_coil(modAddr.acquisition_coil, 0, slave=1)

        # Clear the buffer
        self.file_writer.write_hdf5(
            self.stream_buffer,
            self.data_groupname
        )
        for key in self.stream_buffer:
            self.stream_buffer[key].clear()

        self.file_writer.close_file()
        self.file_open_flag = False

        self.acquiring = False

    def _initialise_clients(self, value):
        """Instantiate a ModbusTcpClient and provide it to the PID controllers."""
        logging.debug("Attempting to establish modbus connection")

        try:
            if self.mocking:
                self.mod_client = MockModbusClient(self.ip, self.port, registers=MockModbusClient.furnace_registers)
                self.mockClient = MockPLC(self.mod_client)
            else:
                self.mod_client = ModbusTcpClient(self.ip)
            self.mod_client.connect()
            # With connection established, populate trees and provide correct connection
            self.pid_upper._register_modbus_client(self.mod_client)
            self.pid_lower._register_modbus_client(self.mod_client)
            self.gradient._register_modbus_client(self.mod_client)
            self.aspc._register_modbus_client(self.mod_client)
            self.tc_manager._register_modbus_client(self.mod_client)

            write_modbus_float(self.mod_client, self.max_setpoint_increase, modAddr.setpoint_step_hold)
            write_modbus_float(self.mod_client, self.max_setpoint, modAddr.setpoint_limit_hold)
            write_coil(self.mod_client, modAddr.setpoint_update_coil, True)

            self.connected = True
        except Exception as e:
            logging.error(f"Connection to modbus client did not succeed: {e}")
            self.connected = False

        self._initialise_tcp_client()

    def _initialise_tcp_client(self):
        """Initialise the tcp client."""

        if self.mocking:
            # This class does almost nothing but does return some fake data without writing it
            self.tcp_client = MockTCPClient(self.mockClient)
        else:
            self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_client.connect((self.ip, self.port))

            self.tcp_client.settimeout(0.2)
            activate = '1'
            self.tcp_client.send(activate.encode())

    def _close_tcp_client(self):
        """Safely end the TCP connection."""
        self.tcp_client.close()

    def update_furnace_frequency(self, freq):
        """Update the PID's frequency, including adapter references to it.
        This should only be called if the trigger is also being updated to fire at that frequency.
        Otherwise, results may be inconsistent.
        :param freq: new frequency as integer
        """
        if freq <= 0:
            logging.warning("""Cannot set furnace frequency to a non-positive value.
            Defaulting to 1 for data buffer and task interval.""")
            freq = 1
        self.pid_frequency = freq

        # Update buffer size to remain 1/s
        self.buffer_size = self.pid_frequency
        # Update task period
        self.bg_stream_task_interval = (1/self.pid_frequency)/2

        write_modbus_float(self.mod_client, freq, modAddr.furnace_freq_hold)
        write_coil(self.mod_client, modAddr.freq_aspc_update_coil, True)
    
    def add_event(self, key, value):
        """Add an event to the event data buffer to be written out later.
        :param key: key of the new value
        :param value: the new value
        """
        if not self.acquiring:
            return
        frame = self.packet_decoder.data['frame']
        # Values are strings as you cannot have multiple data types in one field
        self.event_buffer.append({'event_frame': frame, 'event_key': key, 'event_value': str(value)})

    @run_on_executor
    def background_stream_task(self):
        """Instruct the packet decoder to receive an object, then put that object
        in the parameter tree.
        """
        while self.bg_stream_task_enable:
            if self.mocking:
                if self.acquiring:
                    try:
                        frame, temp = self.tcp_client.recv(self.packet_decoder.size)

                        logging.debug(f"Mock acquisition data: temperature {temp} at reading {frame}")
                    except Exception as e:
                        logging.debug(f"Mock acquisition error: {e}")

                    # Do not need to go as fast for a fake acquisition, there is no timeout
                time.sleep(1/self.pid_frequency)

            else:
                if self.acquiring:
                    try:
                        reading = self.tcp_client.recv(self.packet_decoder.size)
                        logging.debug(self.packet_decoder.data['frame'])
                        self.tcp_reading = self.packet_decoder.unpack(reading)

                    except socket.timeout:
                        logging.debug("TCP Socket timeout: read no data")
                        continue  # If no data received, do not use the packet_decoding logic
                    except Exception as e:
                        logging.debug(f"Other TCP error: {str(e)}")
                        logging.debug("Halting background tasks")
                        self._stop_background_tasks()
                        break

                    self.tcp_reading = self.packet_decoder.data

                    # Add decoded data to the stream buffer
                    for attr in self.packet_decoder.data.keys():
                        self.stream_buffer[attr].append(self.packet_decoder.data[attr])

                    # After a certain number of data reads, write data to the file
                    if len(self.stream_buffer['frame']) >= self.pid_frequency:
                        self.file_writer.write_hdf5(
                            data=self.stream_buffer,
                            groupname=self.data_groupname
                        )
                        # Then clear the stream buffer
                        for key in self.stream_buffer:
                            self.stream_buffer[key].clear()

                        # Additional information written at a lower frequency
                        secondary_data = {
                            'frame': [self.packet_decoder.data['frame']],
                            'setpoint_upper': [self.pid_upper.setpoint],
                            'setpoint_lower': [self.pid_lower.setpoint],
                            'output_upper': [self.pid_upper.output],
                            'output_lower': [self.pid_lower.output]
                        }
                        # Include additional thermocouples if enabled, not including a or b (0,1)
                        for tc in self.tc_manager.thermocouples[2:self.tc_manager.num_mcp]:
                            if tc.index is not None and tc.index >= 0:
                                data_label = f'thermocouple_{tc.label}'
                                secondary_data[data_label] = [tc.value]

                        self.file_writer.write_hdf5(
                            data=secondary_data,
                            groupname="slow_data"
                        )

                        # Write out the event buffer once per second too
                        # List-of-dicts format won't work, so convert it to dict-of-lists
                        if self.event_buffer:
                            batch = {
                                "event_frame": [e["event_frame"] for e in self.event_buffer],
                                "event_key":   [e["event_key"]   for e in self.event_buffer],
                                "event_value": [e["event_value"] for e in self.event_buffer]
                            }
                            self.file_writer.write_hdf5(
                                data=batch,
                                groupname="event_data"
                            )
                            self.event_buffer.clear()

                time.sleep(self.bg_stream_task_interval)

    @run_on_executor
    def background_read_task(self):
        """The adapter background thread task.

        This method runs in the thread executor pool, sleeping for the specified interval and 
        incrementing its counter once per loop, until the background task enable is set to false.
        """
        while self.bg_read_task_enable:

            if self.connected:
                if self.mocking:
                    self.mockClient.bg_temp_task()
                # Get any value updated by the device
                # Mostly input registers, except for setpoints which can change automatically
                try:
                    for tc in self.tc_manager.thermocouples[:self.tc_manager.num_mcp]:
                        if tc.index is not None and tc.index>=0:
                            value = read_decode_input_reg(
                                self.mod_client, tc.val_addr
                            )
                            tc.value = value

                    self.pid_upper.temperature = self.tc_manager._get_value_by_label('upper_heater')
                    self.pid_lower.temperature = self.tc_manager._get_value_by_label('lower_heater')

                    self.lifetime_counter = read_decode_input_reg(self.mod_client, modAddr.counter_inp)

                    self.pid_upper.output    = read_decode_input_reg(self.mod_client, modAddr.pid_upper_output_inp)
                    self.pid_lower.output    = read_decode_input_reg(self.mod_client, modAddr.pid_lower_output_inp)

                    self.pid_upper.outputsum = read_decode_input_reg(self.mod_client, modAddr.pid_upper_outputsum_inp)
                    self.pid_lower.outputsum = read_decode_input_reg(self.mod_client, modAddr.pid_lower_outputsum_inp)

                    self.gradient.actual      = read_decode_input_reg(self.mod_client, modAddr.gradient_actual_inp)
                    self.gradient.theoretical = read_decode_input_reg(self.mod_client, modAddr.gradient_theory_inp)

                    self.aspc.midpt = read_decode_input_reg(self.mod_client, modAddr.autosp_midpt_inp)

                    self.pid_upper.setpoint = read_decode_holding_reg(self.mod_client, modAddr.pid_setpoint_upper_hold)
                    self.pid_lower.setpoint = read_decode_holding_reg(self.mod_client, modAddr.pid_lower_setpoint_hold)

                except Exception as e:
                    logging.error(f"error in reading: {e}")
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
                self._start_background_tasks()
            else:
                self._stop_background_tasks()

    def set_task_interval(self, interval):
        """Set the background task interval."""
        logging.debug("Setting background task interval to %f", interval)
        self.bg_read_task_interval = float(interval)

    def _start_background_tasks(self):
        """Start the background tasks."""
        logging.debug(
            "Launching background tasks with interval %.2f secs", self.bg_read_task_interval
        )
        self.bg_read_task_enable = True
        self.bg_stream_task_enable = True

        # Run the background thread task in the thread execution pool
        self.background_stream_task()
        self.background_read_task()

    def _stop_background_tasks(self):
        """Stop the background tasks."""
        if self.file_open_flag:  # Ensure file is closed properly
            self.file_writer.close_file()

        self.bg_read_task_enable = False
        self.bg_stream_task_enable = False
