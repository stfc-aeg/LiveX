"""Basic adapter for LiveX control

This class implements a simple adapter which reads values

Tim Nicholls, STFC Application Engineering
"""
import logging
import tornado
import time
import sys
from concurrent import futures

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

        # Relevant addresses
        self.coilAddress = 0
        self.inputRegAddress = 30001
        self.holdingRegAddress = 40001

        # Value setup
        self.resistor_temp   = 0
        self.ambient_temp   = 0
        self.pid_output = 0
        self.reading_counter = 0
        self.setpoint = 25.0
        self.pid_enable = True
        self.Kp = 25.0
        self.Ki = 5.0
        self.Kd = 0.0

        # csv log
        self.fieldnames = ['resistor','ambient','setpoint','output']
        with open('temps.csv', 'w', newline='') as csvfile:

            temp_writer = csv.DictWriter(csvfile, delimiter=',', fieldnames=self.fieldnames)
            temp_writer.writeheader()

        pid_loop = ParameterTree({
            'setpoint': (lambda: self.setpoint, self.set_setpoint),
            'pid_enable': (lambda: self.pid_enable, self.set_pid_enable),
            'proportional': (lambda: self.Kp, self.set_proportional_term),
            'integral': (lambda: self.Ki, self.set_integral_term),
            'derivative': (lambda: self.Kd, self.set_derivative_term),
            'pid_output': (lambda: self.pid_output, None),
            'resistor_temp': (lambda: self.resistor_temp, None),
            'ambient_temp': (lambda: self.ambient_temp, None),
            'reading_counter': (lambda: self.reading_counter, None)
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
            'pid_loop': pid_loop
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

    def set_setpoint(self, setpoint):
        """Set the setpoint"""
        self.setpoint = setpoint
        payload = self.write_reg_payload_builder(setpoint)
        response = self.client.write_registers(
            self.holdingRegAddress, payload, slave=1, skip_encode=True
        )

    def set_proportional_term(self, value):
        self.Kp = value
        payload = self.write_reg_payload_builder(value)
        response = self.client.write_registers(
            self.holdingRegAddress+2, payload, slave=1, skip_encode=True
        )

    def set_integral_term(self, value):
        self.Ki = value
        payload = self.write_reg_payload_builder(value)
        response = self.client.write_registers(
            self.holdingRegAddress+4, payload, slave=1, skip_encode=True
        )

    def set_derivative_term(self, value):
        self.Kd = value
        payload = self.write_reg_payload_builder(value)
        response = self.client.write_registers(
            self.holdingRegAddress+6, payload, slave=1, skip_encode=True
        )

    def set_pid_enable(self, enable):
        self.pid_enable = bool(enable)
        if self.pid_enable:
            response = self.client.write_register(self.holdingRegAddress+8, 1, slave=1)
        else:
            response = self.client.write_register(self.holdingRegAddress+8, 0, slave=1)

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

    def write_reg_payload_builder(self, value, byteorder=Endian.Big, wordorder=Endian.Little):
        value = float(value)  # No effect but saves checking variable type
        builder = BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)
        builder.add_32bit_float(value)
        payload = builder.build()

        logging.debug(payload)
        return payload
        # return builder.to_registers()

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

            self.resistor_temp   = self.read_decode_input_reg(self.inputRegAddress)
            self.ambient_temp    = self.read_decode_input_reg(self.inputRegAddress+2)
            self.reading_counter = self.read_decode_input_reg(self.inputRegAddress+4)
            self.pid_output      = 4095 - self.read_decode_input_reg(self.inputRegAddress+6)

            with open('temps.csv', 'a', newline='') as csvfile:
                temp_writer = csv.DictWriter(csvfile, delimiter=',',fieldnames=self.fieldnames)
                temp_writer.writerow(
                    {'resistor': str(self.resistor_temp), 'ambient': str(self.ambient_temp),'setpoint': str(self.setpoint), 'output': self.pid_output}
                )

            self.background_thread_counter += 1

        logging.debug("Background thread task stopping")
