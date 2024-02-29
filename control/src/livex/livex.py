import logging
import tornado
import time
import sys
import socket
import struct
from concurrent import futures
from functools import partial

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

import numpy as np

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions

from pymodbus.client import ModbusTcpClient

from livex.modbusAddresses import modAddr
from livex.pid import PID
from livex.util import LiveXError
from livex.util import read_coil, read_decode_input_reg, read_decode_holding_reg, write_modbus_float

class LiveX():
    """LiveX - class that ..."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self, bg_read_task_enable, bg_read_task_interval, bg_stream_task_enable, bg_stream_task_interval):
        """Initialise the LiveX object.

        This constructor initlialises the LiveX object, building two parameter trees and
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

        # PID controller initialisation
        self.addresses_a = {
            'pid_enable': modAddr.pid_enable_a_coil,
            'pid_setpoint': modAddr.pid_setpoint_a_hold,
            'pid_kp': modAddr.pid_kp_a_hold,
            'pid_ki': modAddr.pid_ki_a_hold,
            'pid_kd': modAddr.pid_kd_a_hold,
            'pid_output': modAddr.pid_output_a_inp,
            'pid_gradient_setpoint': modAddr.gradient_setpoint_a_inp,
            'thermocouple': modAddr.thermocouple_a_inp
        }

        self.addresses_b = {
            'pid_enable': modAddr.pid_enable_b_coil,
            'pid_setpoint': modAddr.pid_setpoint_b_hold,
            'pid_kp': modAddr.pid_kp_b_hold,
            'pid_ki': modAddr.pid_ki_b_hold,
            'pid_kd': modAddr.pid_kd_b_hold,
            'pid_output': modAddr.pid_output_b_inp,
            'pid_gradient_setpoint': modAddr.gradient_setpoint_b_inp,
            'thermocouple': modAddr.thermocouple_b_inp
        }

        # Set up modbus-agnostic stuff to instantiate adapter
        # Adapter does not and should not do anything without modbus
        # it relies on it completely
        # so init cannot progress without modbus connection -- it repeats

        # Modbus and tree setup
        # Wait for connection before proceeding?
        logging.debug("Initial modbus connection")
        self.ip = '192.168.0.159'
        self.port = 4444
        self.mod_client = ModbusTcpClient(self.ip)
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((self.ip, self.port))

        activate = '111' # to ensure connection and allow reading
        self.tcp_client.send(activate.encode())
        self.tcp_client.settimeout(1)
        self.tcp_reading = None

        self.start_acquisition = False

        self.struct = struct.Struct('fff')  # Better than calling the function for every message

        self.pid_a = PID(self.mod_client, self.addresses_a)
        self.pid_b = PID(self.mod_client, self.addresses_b)

        # Gradient (gradient) and Auto set point (autosp) variables
        self.gradient_enable       = bool(read_coil(self.mod_client, modAddr.gradient_enable_coil))
        self.gradient_wanted       = read_decode_holding_reg(self.mod_client, modAddr.gradient_wanted_hold)
        self.gradient_distance     = read_decode_holding_reg(self.mod_client, modAddr.gradient_distance_hold)
        self.gradient_actual       = read_decode_input_reg(self.mod_client, modAddr.gradient_actual_inp)
        self.gradient_theoretical  = read_decode_input_reg(self.mod_client, modAddr.gradient_theory_inp)
        self.gradient_high         = read_coil(self.mod_client, modAddr.gradient_high_coil, asInt=True)  # Not bool, used as index
        self.gradient_high_options = ["A", "B"]

        self.autosp_enable    = read_coil(self.mod_client, modAddr.autosp_enable_coil)
        self.autosp_heating   = read_coil(self.mod_client, modAddr.autosp_heating_coil, asInt=True)  # Not bool, used as index
        self.heating_options  = ["Cooling", "Heating"]
        self.autosp_rate      = read_decode_holding_reg(self.mod_client, modAddr.autosp_rate_hold)
        self.autosp_midpt     = read_decode_input_reg(self.mod_client, modAddr.autosp_midpt_inp)
        self.autosp_imgdegree = read_decode_holding_reg(self.mod_client, modAddr.autosp_imgdegree_hold)

        # Other display controls
        self.thermocouple_a = read_decode_input_reg(self.mod_client, modAddr.thermocouple_a_inp)
        self.thermocouple_b = read_decode_input_reg(self.mod_client, modAddr.thermocouple_b_inp)
        self.thermocouple_c = 0  # nothing to read, no thermocouple
        self.thermocouple_d = 0  # nothing to read, no thermocouple

        self.reading_counter = 0
        self.counter_history = []

        self.connected = True
        self.reconnect = False
        self.connected_uptime = 0

        # Motor controls
        self.motor_direction = 1
        self.motor_speed = 1.0
        self.motor_enable = 1
        self.motor_lvdt = 5.0  # not using yet

        motor = ParameterTree({
            'enable': (lambda: self.motor_enable, self.set_motor_enable),
            'direction': (lambda: self.motor_direction, self.set_motor_direction),
            'speed': (lambda: self.motor_speed, self.set_motor_speed),
            'lvdt': (lambda: self.motor_lvdt, None)
        })

        thermal_gradient = ParameterTree({
            'enable': (lambda: self.gradient_enable, self.set_gradient_enable),
            'wanted': (lambda: self.gradient_wanted, self.set_gradient_wanted),
            'distance': (lambda: self.gradient_distance, self.set_gradient_distance),
            'actual': (lambda: self.gradient_actual, None),
            'theoretical': (lambda: self.gradient_theoretical, None),
            'high_heater': (lambda: self.gradient_high, self.set_gradient_high),
            'high_heater_options': (lambda: self.gradient_high_options, None)
        })

        autosp = ParameterTree({
            'enable': (lambda: self.autosp_enable, self.set_autosp_enable),
            'heating': (lambda: self.autosp_heating, self.set_autosp_heating),
            'heating_options': (lambda: self.heating_options, None), 
            'rate': (lambda: self.autosp_rate, self.set_autosp_rate),
            'img_per_degree': (lambda: self.autosp_imgdegree, self.set_autosp_imgdegree),
            'midpt_temp': (lambda: self.autosp_midpt, None)
        })

        # Build a parameter tree for the background task
        bg_task = ParameterTree({
            'thread_count': (lambda: self.background_thread_counter, None),
            'enable': (lambda: self.bg_read_task_enable, self.set_task_enable),
            'interval': (lambda: self.bg_read_task_interval, self.set_task_interval),
        })

        status = ParameterTree({
            'odin_version': version_info['version'],
            'server_uptime': (self.get_server_uptime, None),
            'counter_history': (self.counter_history, None),
            'connected_uptime': (lambda: self.connected_uptime, None),
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
            'pid_a': self.pid_a.pid_tree,
            'pid_b': self.pid_b.pid_tree,
            'autosp': autosp,
            'gradient': thermal_gradient,
            'motor': motor,
            'tcp': tcp
        })

        # Launch the background task if enabled in options
        if self.bg_read_task_enable:
            logging.debug("going to start bg tasks")
            self.start_background_tasks()

    # Adapter processes

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

        self.tcp_client.connect((self.ip, self.port))
        activate = '111'
        self.tcp_client.send(activate.encode())

        self.mod_client.connect()
        self.connected = True

        self.pid_a.initialise_modbus_client(self.mod_client)
        self.pid_b.initialise_modbus_client(self.mod_client)

    def push_data(self, key, data):
        """Push data to the graph adapter dataset(s).
        :param key: key in dataset
        :param data: value to append to list in key
        """
        self.graph_adapter.datasets['thermocouples'].data[key].append(data)

        self.graph_adapter.datasets['thermocouples_long'].data[key].append(data)

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
        self.stop_background_tasks()

    # Auto set point control

    def set_autosp_enable(self, value):
        """Set the enable boolean for the auto set point control."""
        self.autosp_enable = bool(value)

        if value:
            ret = self.mod_client.write_coil(modAddr.autosp_enable_coil, 1, slave=1)
        else:
            ret = self.mod_client.write_coil(modAddr.autosp_enable_coil, 0, slave=1)

    def set_autosp_heating(self, value):
        """Set the boolean for auto set point control heating."""
        self.autosp_heating = value

        if value:  # 1, heating
            self.mod_client.write_coil(modAddr.autosp_heating_coil, 1, slave=1)
        else:      # 0, cooling
            self.mod_client.write_coil(modAddr.autosp_heating_coil, 0, slave=1)

    def set_autosp_rate(self, value):
        """Set the rate value for the auto set point control."""
        self.autosp_rate = value
        response = write_modbus_float(self.mod_client, value, modAddr.autosp_rate_hold)

    def set_autosp_imgdegree(self, value):
        """Set the image acquisition per degree for the auto set point control."""
        self.autosp_imgdegree = value
        response = write_modbus_float(self.mod_client, value, modAddr.autosp_imgdegree_hold)

    # Thermal gradient

    def set_gradient_enable(self, value):
        """Set the enable boolean for the thermal gradient."""
        self.gradient_enable = bool(value)

        if value:
            self.mod_client.write_coil(modAddr.gradient_enable_coil, 1, slave=1)
        else:
            self.mod_client.write_coil(modAddr.gradient_enable_coil, 0, slave=1)

    def set_gradient_distance(self, value):
        """Set the distance value for the thermal gradient."""
        self.gradient_distance = value
        response = write_modbus_float(self.mod_client, value, modAddr.gradient_distance_hold)

    def set_gradient_wanted(self, value):
        """Set the desired temperature change per mm for the thermal gradient."""
        self.gradient_wanted = value
        response = write_modbus_float(self.mod_client, value, modAddr.gradient_wanted_hold)

    def set_gradient_high(self, value):
        """Set the boolean for thermal gradient high heater."""
        self.gradient_high = value

        if value:  # 1, heater B
            self.mod_client.write_coil(modAddr.gradient_high_coil, 1, slave=1)
        else:
            self.mod_client.write_coil(modAddr.gradient_high_coil, 0, slave=1)

    # Motor Controls

    def set_motor_enable(self, value):
        """Set motor enable boolean."""
        self.motor_enable = value

        if value:  # 1, enabled
            self.mod_client.write_coil(modAddr.motor_enable_coil, 1, slave=1)
        else:
            self.mod_client.write_coil(modAddr.motor_enable_coil, 0, slave=1)

    def set_motor_direction(self, value):
        """Set motor direction boolean."""
        self.motor_direction = value

        if value:  # 1, up
            self.mod_client.write_coil(modAddr.motor_direction_coil, 1, slave=1)
        else:  # 0, down
            self.mod_client.write_coil(modAddr.motor_direction_coil, 0, slave=1)

    def set_motor_speed(self, value):
        """Set motor speed holding register."""
        self.motor_speed = value

        write_modbus_float(self.mod_client, value, modAddr.motor_speed_hold)

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
        self.tcp_client.close()
        self.bg_read_task_enable = False
        self.bg_stream_task_enable = False
        self.background_ioloop_callback.stop()

    def background_ioloop_callback(self):
        """background task IOLoop callback
        may be swapped to be a thread for the reading"""
        self.push_data('temp_a', self.pid_a.thermocouple)
        self.push_data('temp_b', self.pid_b.thermocouple)

        # self.background_ioloop_counter += 1

    @run_on_executor
    def background_stream_task(self):
        """task to, if connected, receive a specific object through a buffer"""
        while self.bg_stream_task_enable:
            try:
                reading = self.tcp_client.recv(12)
                obj = self.struct.unpack(reading)
                logging.debug(obj[0])
                self.tcp_reading = obj
            except:
                logging.debug("read no data")

            time.sleep(self.bg_stream_task_interval)

    @run_on_executor
    def background_read_task(self):
        """The adapter background thread task.

        This method runs in the thread executor pool, sleeping for the specified interval and 
        incrementing its counter once per loop, until the background task enable is set to false.
        """
        prev_time = time.time()  # start time

        while self.bg_read_task_enable:

            cur_time = time.time()

            if self.connected:
                # Get any value updated by the device
                # Almost all input registers, except for setpoints which can change automatically
                try:
                    # logging.debug("coil valid")
                    self.pid_a.thermocouple = read_decode_input_reg(self.mod_client, modAddr.thermocouple_a_inp)
                    self.pid_b.thermocouple = read_decode_input_reg(self.mod_client, modAddr.thermocouple_b_inp)

                    self.reading_counter = read_decode_input_reg(self.mod_client, modAddr.counter_inp)

                    self.pid_a.output    = read_decode_input_reg(self.mod_client, modAddr.pid_output_a_inp)
                    self.pid_b.output    = read_decode_input_reg(self.mod_client, modAddr.pid_output_b_inp)

                    self.gradient_actual      = read_decode_input_reg(self.mod_client, modAddr.gradient_actual_inp)
                    self.gradient_theoretical = read_decode_input_reg(self.mod_client, modAddr.gradient_theory_inp)

                    self.pid_a.gradient_setpoint = read_decode_input_reg(self.mod_client, modAddr.gradient_setpoint_a_inp)
                    self.pid_b.gradient_setpoint = read_decode_input_reg(self.mod_client, modAddr.gradient_setpoint_b_inp)

                    self.autosp_midpt = read_decode_input_reg(self.mod_client, modAddr.autosp_midpt_inp)

                    self.pid_a.setpoint = read_decode_holding_reg(self.mod_client, modAddr.pid_setpoint_a_hold)
                    self.pid_b.setpoint = read_decode_holding_reg(self.mod_client, modAddr.pid_setpoint_b_hold)

                    self.motor_lvdt = read_decode_input_reg(self.mod_client, modAddr.motor_lvdt_inp)

                except:
                    self.mod_client.close()
                    logging.debug("Modbus communication error, pausing reads")
                    self.connected = False
                    self.connected_uptime = 0
                    # self.reconnect = False
                    # time.sleep(sleep_interval)

                self.background_thread_counter += 1

            else:
                # logging.debug("Awaiting reconnection")
                pass
            
            time.sleep(self.bg_read_task_interval)

        logging.debug("Background thread task stopping")
