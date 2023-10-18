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
from src.livex.util import read_coil, read_decode_input_reg, read_decode_holding_reg, write_modbus_float

class PID():

    def __init__(self, client, addresses):
        self.initialise_modbus_client(client)  # Client required for __init__, client function used for reset

        # logging.debug(addresses)

        self.addresses = addresses
        # Addresses are generic via dictionary usage

        # PID (pid) variables for PID controllers A and B
        self.enable            = bool(read_coil(self.client, self.addresses['pid_enable']))
        self.setpoint          = read_decode_holding_reg(self.client, self.addresses['pid_setpoint'])
        self.kp                = read_decode_holding_reg(self.client, self.addresses['pid_kp'])
        self.ki                = read_decode_holding_reg(self.client, self.addresses['pid_ki'])
        self.kd                = read_decode_holding_reg(self.client, self.addresses['pid_kd'])
        self.output            = read_decode_input_reg(self.client, self.addresses['pid_output'])
        self.gradient_setpoint = read_decode_input_reg(self.client, self.addresses['pid_gradient_setpoint'])

        self.thermocouple = read_decode_input_reg(self.client, self.addresses['thermocouple'])

        self.pid_tree = ParameterTree({
            'enable': (lambda: self.enable, self.set_pid_enable),
            'setpoint': (lambda: self.setpoint, self.set_pid_setpoint),
            'gradient_setpoint': (lambda: self.gradient_setpoint, self.set_pid_gradient_setpoint),
            'proportional': (lambda: self.kp, self.set_pid_proportional),
            'integral': (lambda: self.ki, self.set_pid_integral),
            'derivative': (lambda: self.kd, self.set_pid_derivative),
            'temperature': (lambda: self.thermocouple, None),
            'output': (lambda: self.output, None)
        })

    def initialise_modbus_client(self, client):
        """Keep internal reference to the Modbus client."""
        self.client = client

    def set_pid_setpoint(self, value):
        """Set the setpoint of PID A or B.
        :param setpoint: "pid_setpoint" or "pid_setpoint"
        :param address: address to write setpoint to
        """
        self.setpoint = value
        response = write_modbus_float(
            self.client, value, self.addresses['pid_setpoint']
        )

    def set_pid_gradient_setpoint(self, value):
        """
        """
        self.gradient_setpoint = value
        response = write_modbus_float(
            self.client, value, self.addresses['pid_gradient_setpoint']
        )

    def set_pid_proportional(self, value):
        """Set the proportional term of PID A or B.
        :param Kp: "pid_ki_a" or "pid_ki_b". self.<attribute> to edit
        :param address: address to write value to
        """
        self.kp = value
        response = write_modbus_float(
            self.client, value, self.addresses['pid_kp']
        )

    def set_pid_integral(self, value):
        """Set the integral term of PID A or B.
        :param Ki: "pid_ki_a" or "pid_ki_b". self.<attribute> to edit
        :param address: address to write value to
        """
        self.ki = value
        response = write_modbus_float(
            self.client, value, self.addresses['pid_ki']
        )
    
    def set_pid_derivative(self, value):
        """Set the derivative term of PID A or B.
        :param Kd: "pid_kd_b" or "pid_kd_b". self.<attribute> to edit
        :param address: address to write value to
        """
        self.kd = value
        response = write_modbus_float(
            self.client, value, self.addresses['pid_kd']
        )

    def set_pid_enable(self, value):
        """Set the enable boolean for PID A or B.
        :param pid_enable: "pid_enable_a" or "pid_enable_b". self.<attribute> to edit
        :param address: address to write value to (pid_enable_a/b_coil)
        """
        self.enable = bool(value)

        if value:
            response = self.client.write_coil(self.addresses['pid_enable'], 1, slave=1)
        else:
            response = self.client.write_coil(self.addresses['pid_enable'], 0, slave=1)
