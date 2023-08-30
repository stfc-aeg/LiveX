"""Basic adapter for LiveX control

This class implements a simple adapter which reads values

Tim Nicholls, STFC Application Engineering
"""
import logging
import tornado
import time
import sys
from concurrent import futures
from functools import partial

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions

from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian

from src.livex.modbusAddresses import modAddr

import csv


class LiveXAdapter(ApiAdapter):
    """System info adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server and the system that it is
    running on.
    """

    def __init__(self, **kwargs):
        """Initialize the LiveXAdapter object.

        This constructor initializes the LiveXAdapter object.

        :param kwargs: keyword arguments specifying options
        """

        # Intialise superclass
        super(LiveXAdapter, self).__init__(**kwargs)

        # Parse options
        background_task_enable = bool(self.options.get('background_task_enable', False))
        background_task_interval = float(self.options.get('background_task_interval', 1.0))

        self.livex = LiveX(background_task_enable, background_task_interval)

        logging.debug('LiveXAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.livex.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """

        content_type = 'application/json'

        try:
            data = json_decode(request.body)
            self.livex.set(path, data)
            response = self.livex.get(path)
            status_code = 200
        except LiveXError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'LiveXAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def cleanup(self):
        """Clean up adapter state at shutdown.

        This method cleans up the adapter state when called by the server at e.g. shutdown.
        It simplied calls the cleanup function of the LiveX instance.
        """
        self.livex.cleanup()

class LiveXError(Exception):
    """Simple exception class to wrap lower-level exceptions."""

    pass


class LiveX():
    """LiveX - class that ..."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, background_task_enable, background_task_interval):
        """Initialise the LiveX object.

        This constructor initlialises the LiveX object, building two parameter trees and
        launching the background task to make modbus requests to the device.
        """
        self.client = ModbusTcpClient('192.168.0.159')

        logging.getLogger("pymodbus").setLevel(logging.WARNING)  # Stop modbus from filling console

        # Save arguments
        self.background_task_enable = background_task_enable
        self.background_task_interval = background_task_interval

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        # Set the background task counters to zero
        self.background_ioloop_counter = 0
        self.background_thread_counter = 0

        # PID (pid) variables for PID controllers A and B
        self.pid_enable_a   = bool(self.read_coil(modAddr.pid_enable_a_coil))
        self.pid_setpoint_a = self.read_decode_holding_reg(modAddr.pid_setpoint_a_hold)
        self.pid_kp_a       = self.read_decode_holding_reg(modAddr.pid_kp_a_hold)
        self.pid_ki_a       = self.read_decode_holding_reg(modAddr.pid_ki_a_hold)
        self.pid_kd_a       = self.read_decode_holding_reg(modAddr.pid_kd_a_hold)
        self.pid_output_a   = self.read_decode_input_reg(modAddr.pid_output_a_inp)

        self.pid_enable_b   = bool(self.read_coil(modAddr.pid_enable_b_coil))
        self.pid_setpoint_b = self.read_decode_holding_reg(modAddr.pid_setpoint_b_hold)
        self.pid_kp_b       = self.read_decode_holding_reg(modAddr.pid_kp_b_hold)
        self.pid_ki_b       = self.read_decode_holding_reg(modAddr.pid_ki_b_hold)
        self.pid_kd_b       = self.read_decode_holding_reg(modAddr.pid_kd_b_hold)
        self.pid_output_b   = self.read_decode_input_reg(modAddr.pid_output_b_inp)

        # Gradient (gradient) and Auto set point (autosp) variables
        self.gradient_enable      = bool(self.read_coil(modAddr.gradient_enable_coil))
        self.gradient_wanted      = self.read_decode_holding_reg(modAddr.gradient_wanted_hold)
        self.gradient_distance    = self.read_decode_holding_reg(modAddr.gradient_distance_hold)
        self.gradient_actual      = self.read_decode_input_reg(modAddr.gradient_actual_inp)
        self.gradient_theoretical = self.read_decode_input_reg(modAddr.gradient_theory_inp)
        self.gradient_modifier = self.read_decode_input_reg(modAddr.gradient_modifier_inp)

        self.autosp_enable    = self.read_coil(modAddr.autosp_enable_coil)
        self.autosp_heating   = self.read_coil(modAddr.autosp_heating_coil, asInt=True)  # Not bool, used as index
        self.heating_options  = ["Cooling", "Heating"]
        self.autosp_rate      = self.read_decode_holding_reg(modAddr.autosp_rate_hold)
        self.autosp_midpt     = self.read_decode_input_reg(modAddr.autosp_midpt_inp)
        self.autosp_imgdegree = self.read_decode_holding_reg(modAddr.autosp_imgdegree_hold)

        # Other display controls
        self.thermocouple_a = self.read_decode_input_reg(modAddr.thermocouple_a_inp)
        self.thermocouple_b = self.read_decode_input_reg(modAddr.thermocouple_b_inp)
        self.thermocouple_c = 0  # nothing to read, no thermocouple
        self.thermocouple_d = 0  # nothing to read, no thermocouple

        self.reading_counter = 0

        # csv log
        self.fieldnames = ['resistor','ambient','setpoint','output']
        with open('temps.csv', 'w', newline='') as csvfile:

            temp_writer = csv.DictWriter(csvfile, delimiter=',', fieldnames=self.fieldnames)
            temp_writer.writeheader()

        pid_a = ParameterTree({
            'enable': (lambda: self.pid_enable_a, partial(
                self.set_pid_enable, pid_enable="pid_enable_a", address=modAddr.pid_enable_a_coil
            )),
            'setpoint': (lambda: self.pid_setpoint_a, partial(
                self.set_pid_setpoint, setpoint="pid_setpoint_a", address=modAddr.pid_setpoint_a_hold
            )),
            'proportional': (lambda: self.pid_kp_a, partial(
                self.set_pid_proportional, Kp="pid_kp_a", address=modAddr.pid_kp_a_hold
            )),
            'integral': (lambda: self.pid_ki_a, partial(
                self.set_pid_integral, Ki="pid_ki_a", address=modAddr.pid_ki_a_hold
            )),
            'derivative': (lambda: self.pid_kd_a, partial(
                self.set_pid_derivative, Kd="pid_kd_a", address=modAddr.pid_kd_a_hold
            )),
            'temperature': (lambda: self.thermocouple_a, None),
            'output': (lambda: self.pid_output_a, None)
        })

        pid_b = ParameterTree({
            'enable': (lambda: self.pid_enable_b, partial(
                self.set_pid_enable, pid_enable="pid_enable_b", address=modAddr.pid_enable_b_coil
            )),
            'setpoint': (lambda: self.pid_setpoint_b, partial(
                self.set_pid_setpoint, setpoint="pid_setpoint_b", address=modAddr.pid_setpoint_b_hold
            )),
            'proportional': (lambda: self.pid_kp_b, partial(
                self.set_pid_proportional, Kp="pid_kp_b", address=modAddr.pid_kp_b_hold)
            ),
            'integral': (lambda: self.pid_ki_b, partial(
                self.set_pid_integral, Ki="pid_ki_b", address=modAddr.pid_ki_b_hold
            )),
            'derivative': (lambda: self.pid_kd_b, partial(
                self.set_pid_derivative, Kd="pid_kd_b", address=modAddr.pid_kd_b_hold
            )),
            'temperature': (lambda: self.thermocouple_b, None),
            'output': (lambda: self.pid_output_b, None)
        })

        thermal_gradient = ParameterTree({
            'enable': (lambda: self.gradient_enable, self.set_gradient_enable),
            'wanted': (lambda: self.gradient_wanted, self.set_gradient_wanted),
            'distance': (lambda: self.gradient_distance, self.set_gradient_distance),
            'actual': (lambda: self.gradient_actual, None),
            'theoretical': (lambda: self.gradient_theoretical, None),
            'modifier': (lambda: self.gradient_modifier, None)
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
            'ioloop_count': (lambda: self.background_ioloop_counter, None),
            'thread_count': (lambda: self.background_thread_counter, None),
            'enable': (lambda: self.background_task_enable, self.set_task_enable),
            'interval': (lambda: self.background_task_interval, self.set_task_interval),
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'tornado_version': tornado.version,
            'server_uptime': (self.get_server_uptime, None),
            'background_task': bg_task,
            'pid_a': pid_a,
            'pid_b': pid_b,
            'autosp': autosp,
            'gradient': thermal_gradient
        })

        # Launch the background task if enabled in options
        if self.background_task_enable:
            self.start_background_tasks()

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
        self.client.close()
        self.stop_background_tasks()

    def set_task_interval(self, interval):
        """Set the background task interval."""
        logging.debug("Setting background task interval to %f", interval)
        self.background_task_interval = float(interval)
        
    def set_task_enable(self, enable):
        """Set the background task enable."""
        enable = bool(enable)

        if enable != self.background_task_enable:
            if enable:
                self.start_background_tasks()
            else:
                self.stop_background_tasks()

    def set_pid_setpoint(self, value, setpoint, address):
        """Set the setpoint of PID A or B.
        :param setpoint: "pid_setpoint_a" or "pid_setpoint_b"
        :param address: address to write setpoint to
        """
        setattr(self, setpoint, value)
        response = self.write_modbus_float(value, address)

    def set_pid_proportional(self, value, Kp, address):
        """Set the proportional term of PID A or B.
        :param Kp: "pid_ki_a" or "pid_ki_b". self.<attribute> to edit
        :param address: address to write value to
        """
        setattr(self, Kp, value)
        response = self.write_modbus_float(value, address)

    def set_pid_integral(self, value, Ki, address):
        """Set the integral term of PID A or B.
        :param Ki: "pid_ki_a" or "pid_ki_b". self.<attribute> to edit
        :param address: address to write value to
        """
        setattr(self, Ki, value)
        response = self.write_modbus_float(value, address)
    
    def set_pid_derivative(self, value, Kd, address):
        """Set the derivative term of PID A or B.
        :param Kd: "pid_kd_b" or "pid_kd_b". self.<attribute> to edit
        :param address: address to write value to
        """
        setattr(self, Kd, value)
        response = self.write_modbus_float(value, address)

    def set_pid_enable(self, value, pid_enable, address):
        """Set the enable boolean for PID A or B.
        :param pid_enable: "pid_enable_a" or "pid_enable_b". self.<attribute> to edit
        :param address: address to write value to (pid_enable_a/b_coil)
        """
        setattr(self, pid_enable, bool(value))

        if getattr(self, pid_enable):
            response = self.client.write_coil(address, 1, slave=1)
        else:
            response = self.client.write_coil(address, 0, slave=1)

    def set_autosp_enable(self, value):
        self.autosp_enable = bool(value)

        if value:
            ret = self.client.write_coil(modAddr.autosp_enable_coil, 1, slave=1)
        else:
            ret = self.client.write_coil(modAddr.autosp_enable_coil, 0, slave=1)

    def set_autosp_heating(self, value):
        logging.debug("VALUE: %s", value)
        self.autosp_heating = value

        if value:  # 1, heating
            self.client.write_coil(modAddr.autosp_heating_coil, 1, slave=1)
        else:      # 0, cooling
            self.client.write_coil(modAddr.autosp_heating_coil, 0, slave=1)

    def set_autosp_rate(self, value):
        self.autosp_rate = value

        response = self.write_modbus_float(value, modAddr.autosp_rate_hold)
        logging.debug("rate write status: %s", response)

    def set_autosp_imgdegree(self, value):
        self.autosp_imgdegree = value

        response = self.write_modbus_float(value, modAddr.autosp_imgdegree_hold)

    def set_gradient_distance(self, value):
        self.gradient_distance = value

        response = self.write_modbus_float(value, modAddr.gradient_distance_hold)

    def set_gradient_enable(self, value):
        self.gradient_enable = bool(value)

        if value:
            self.client.write_coil(modAddr.gradient_enable_coil, 1, slave=1)
        else:
            self.client.write_coil(modAddr.gradient_enable_coil, 0, slave=1)

    def set_gradient_wanted(self, value):
        self.gradient_wanted = value

        response = self.write_modbus_float(value, modAddr.gradient_wanted_hold)

    def start_background_tasks(self):
        """Start the background tasks."""
        logging.debug(
            "Launching background tasks with interval %.2f secs", self.background_task_interval
        )

        self.background_task_enable = True

        # Register a periodic callback for the ioloop task and start it
        self.background_ioloop_task = PeriodicCallback(
            self.background_ioloop_callback, self.background_task_interval * 1000
        )
        # self.background_ioloop_task.start()

        # Run the background thread task in the thread execution pool
        self.background_thread_task()

    def stop_background_tasks(self):
        """Stop the background tasks."""
        self.background_task_enable = False
        self.background_ioloop_task.stop()

    def background_ioloop_callback(self):
        """Run the adapter background IOLoop callback.

        This simply increments the background counter before returning. It is called repeatedly
        by the periodic callback on the IOLoop.
        """

        if self.background_ioloop_counter < 10 or self.background_ioloop_counter % 20 == 0:
            logging.debug(
                "Background IOLoop task running, count = %d", self.background_ioloop_counter
            )

        self.background_ioloop_counter += 1

    def read_coil(self, address, asInt=False):
        """Read and return the value from the coil at the specified address, optionally as an int."""
        response = self.client.read_coils(address, count=1, slave=1)

        if asInt:
            return (1 if response.bits[0] else 0)  # 1 if true, 0 if not
        else:
            return response.bits[0]  # read_coils pads to eight with zeroes.

    def read_decode_input_reg(self, address):
        """Read and decode a float value from a given address (two registers).
        Return the decoded value.
        """
        response = self.client.read_input_registers(address, count=2, slave=1)
        decoder = BinaryPayloadDecoder.fromRegisters(
            response.registers, wordorder=Endian.Little, byteorder=Endian.Big
        )
        value = decoder.decode_32bit_float()
        return value

    def read_decode_holding_reg(self, address):
        """Read and decode a float value from a given address (two registers).
        Return the decoded value.
        """
        response = self.client.read_holding_registers(address, count=2, slave=1)
        decoder = BinaryPayloadDecoder.fromRegisters(
            response.registers, wordorder=Endian.Little, byteorder=Endian.Big
        )
        value = decoder.decode_32bit_float()
        return value

    def write_reg_payload_builder(self, value, byteorder=Endian.Big, wordorder=Endian.Little):
        value = float(value)  # No effect but saves checking variable type
        builder = BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)
        builder.add_32bit_float(value)
        payload = builder.build()

        logging.debug(payload)
        return payload

    def write_modbus_float(self, value, address):
        payload = self.write_reg_payload_builder(value)
        response = self.client.write_registers(
            address, payload, slave=1, skip_encode=True
        )
        return response

    @run_on_executor
    def background_thread_task(self):
        """The the adapter background thread task.

        This method runs in the thread executor pool, sleeping for the specified interval and 
        incrementing its counter once per loop, until the background task enable is set to false.
        """
        # sleep_interval = self.background_task_interval

        while self.background_task_enable:
            sleep_interval = self.background_task_interval
            time.sleep(sleep_interval)

            # Need to get any value that can be updated by the device.
            # This is almost exclusively the contents of input registers, with the exception of
            # setpoints, which can be modified with the gradient and autosp controls.

            self.thermocouple_a  = self.read_decode_input_reg(modAddr.thermocouple_a_inp)
            self.thermocouple_b  = self.read_decode_input_reg(modAddr.thermocouple_b_inp)
            self.reading_counter = self.read_decode_input_reg(modAddr.counter_inp)
            self.pid_output_a    = 4095 - self.read_decode_input_reg(modAddr.pid_output_a_inp)
            self.pid_output_b    = 4095 - self.read_decode_input_reg(modAddr.pid_output_b_inp)

            self.gradient_actual      = self.read_decode_input_reg(modAddr.gradient_actual_inp)
            self.gradient_theoretical = self.read_decode_input_reg(modAddr.gradient_theory_inp)
            self.gradient_modifier    = self.read_decode_input_reg(modAddr.gradient_modifier_inp)

            self.autosp_midpt = self.read_decode_input_reg(modAddr.autosp_midpt_inp)

            self.pid_setpoint_a = self.read_decode_holding_reg(modAddr.pid_setpoint_a_hold)
            self.pid_setpoint_b = self.read_decode_holding_reg(modAddr.pid_setpoint_b_hold)

            self.background_thread_counter += 1

        logging.debug("Background thread task stopping")
