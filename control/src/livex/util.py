"""
Utilities for the LiveX adapters.

Mika Shearwood, STFC Detector Systems Software Group
"""
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
from odin_control.adapters.adapter import ApiAdapterRequest
from odin_control.adapters.base_controller import BaseController, BaseError

import logging
import math

from typing import Any, TypeVar

AnyController = TypeVar("AnyController", bound=BaseController)

class LiveXError(BaseError):
    """Simple exception class to wrap lower-level exceptions."""
    pass

class ICCError(BaseError):
    """Simple exception class to wrap inter-controller communication exceptions."""

def read_coil(client, address, asInt=False):
    """Read and return the value from the coil at the specified address, optionally as an int."""
    response = client.read_coils(address, count=1, slave=1)

    if asInt:
        return (1 if response.bits[0] else 0)  # 1 if true, 0 if not
    else:
        return response.bits[0]  # read_coils pads to eight with zeroes.

def write_coil(client, address, value=0):
    """Write a boolean value to a coil at the specified address."""
    response = client.write_coil(address, value, slave=1)
    return response

def read_decode_input_reg(client, address):
    """Read and decode a float value from a given input register address (two registers).
    Return the decoded value.
    """
    response = client.read_input_registers(address, count=2, slave=1)
    decoder = BinaryPayloadDecoder.fromRegisters(
        response.registers, wordorder=Endian.LITTLE, byteorder=Endian.BIG
    )
    value = decoder.decode_32bit_float()

    if math.isnan(value):  # Error is hard to reproduce but good to account for
        logging.debug(f"ISNAN when reading from address {address}")
        return -1.0
    return value

def read_decode_holding_reg(client, address):
    """Read and decode a float value from a given holding register address (two registers).
    Return the decoded value.
    """
    response = client.read_holding_registers(address, count=2, slave=1)
    decoder = BinaryPayloadDecoder.fromRegisters(
        response.registers, wordorder=Endian.LITTLE, byteorder=Endian.BIG
    )
    value = decoder.decode_32bit_float()

    if math.isnan(value):
        logging.debug(f"ISNAN when reading from address {address}")
        return -1.0
    return value

def write_modbus_float(client, value, address, byteorder=Endian.BIG, wordorder=Endian.LITTLE):
    """Write a floating point value to a modbus address (written across two registers).
    :param client: ModbusTcpClient
    :param value: float to be written.
    :param address: starting address for write.
    :param byteorder: order of bytes (default big endian)
    :param wordorder: order of 'words' (default little endian)
    :return response: write status
    """
    builder = BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)
    builder.add_32bit_float(float(value)) # float(value) avoids checking variable type, no effect
    payload = builder.build()

    response = client.write_registers(
        address, payload, slave=1, skip_encode=True
    )

    return response

def icc_get(controller, path, **kwargs):
    """Generic ICC get method for synchronous adapter controllers."""
    try:
        response_data = controller.get(path)
    except Exception as e:
        raise ICCError(
            f"ICC GET failed for controller {controller}, path {path}: {e}"
        )

    if not isinstance(response_data, dict):
        raise ICCError(
            f"ICC GET returned an invalid response for controller {controller}, path {path}: "
            f"{response_data}"
        )
    # Convert the dictionaries keys to a set. If there is exactly one, 'value', return it
    if set(response_data) == {"value"}:
        return response_data["value"]
    return response_data

def icc_set(controller: AnyController, path: str, data: dict[str: Any]):
    """Generic inter-adapter-controller set method for odin_control controllers.
    This method avoids the HTTP message construction and directly calls the controller's set method
    to ensure the ParameterTree is updated correctly, while avoiding unnecessary encoding/decoding.
    
    :param controller: Controller object to target.
    :type controller: Any Subclass of BaseController
    :param path: Parameter tree path to target, to not include the parameter itself
    :type path: str
    :param data: Dictionary of parameter value(s) to write to the specified path.
    :type data: dict[str, Any]
    """
    try:
        controller.set(path, data)
    except Exception as e:
        raise ICCError(
            f"ICC SET failed for controller {controller}, path {path}: {e}"
        )