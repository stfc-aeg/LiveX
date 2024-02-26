"""
Utilities for the LiveX adapters.

Mika Shearwood, STFC Detector Systems Software Group
"""
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian

import logging
import math

class LiveXError(Exception):
    """Simple exception class to wrap lower-level exceptions."""
    pass


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
        logging.debug("ISNAN")
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
        logging.debug("ISNAN")
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