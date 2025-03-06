"""
Utilities for the LiveX adapters.

Mika Shearwood, STFC Detector Systems Software Group
"""
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian

import logging
import struct

from livex.modbusAddresses import modAddr

class MockModbusClient:

    furnace_registers = {
        # Coils (00001-09999)
        1: 0,   # pid_enable_a_coil
        2: 0,   # pid_enable_b_coil
        3: 0,   # gradient_enable_coil
        4: 0,   # autosp_enable_coil
        5: 0,   # autosp_heating_coil
        6: 0,   # motor_enable_coil
        7: 0,   # motor_direction_coil
        8: 0,   # gradient_high_coil
        9: 0,   # acquisition_coil
        10: 0,  # gradient_update_coil
        11: 0,  # freq_aspc_update_coil
        12: 0,  # setpoint_update_coil

        # Input Registers (30001-39999)
        30001: 0,   # counter_inp
        30003: 0,    # pid_output_a_inp
        30005: 0,    # pid_output_b_inp
        30007: 0,   # pid_outputsum_a_inp
        30009: 0,   # pid_outputsum_b_inp

        30011: 21,   # thermocouple_a_inp
        30013: 20,   # thermocouple_b_inp
        30015: 20,   # thermocouple_c_inp
        30017: 20,   # thermocouple_d_inp

        30019: 0,     # gradient_actual_inp
        30021: 0,     # gradient_theory_inp
        30023: 0,  # autosp_midpt_inp

        30027: 0,   # motor_lvdt_inp

        # Holding Registers (40001-49999)
        40001: 30,   # pid_setpoint_a_hold
        40003: 0.3,    # pid_kp_a_hold
        40005: 0.02,     # pid_ki_a_hold
        40007: 0,     # pid_kd_a_hold

        40009: 30,   # pid_setpoint_b_hold
        40011: 0.3,    # pid_kp_b_hold
        40013: 0.02,     # pid_ki_b_hold
        40015: 0,     # pid_kd_b_hold

        40017: 10,    # furnace_freq_hold
        40019: 7,     # gradient_wanted_hold
        40021: 25,    # gradient_distance_hold
        40023: 2,     # autosp_rate_hold
        40025: 0,    # autosp_imgdegree_hold
        40027: 0,   # motor_speed_hold
    }
    trigger_registers = {
        # Coils (0-13)
        0: 0,   # trig_enable_coil
        1: 0,   # trig_disable_coil
        2: 0,   # trig_0_enable_coil
        3: 0,   # trig_1_enable_coil
        4: 0,   # trig_2_enable_coil
        5: 0,   # trig_3_enable_coil
        6: 0,   # trig_0_disable_coil
        7: 0,   # trig_1_disable_coil
        8: 0,   # trig_2_disable_coil
        9: 0,   # trig_3_disable_coil
        10: 0,  # trig_0_running_coil
        11: 0,  # trig_1_running_coil
        12: 0,  # trig_2_running_coil
        13: 0,  # trig_3_running_coil

        # Holding Registers (40001-49999)
        40001: 0,  # trig_0_intvl_hold
        40003: 0,  # trig_1_intvl_hold
        40005: 0,  # trig_2_intvl_hold
        40007: 0,  # trig_3_intvl_hold
        40009: 0,  # trig_0_target_hold
        40011: 0,  # trig_1_target_hold
        40013: 0,  # trig_2_target_hold
        40015: 0,  # trig_3_target_hold
    }

    def __init__(self, ip='192.168.0.159', port=4444, registers=furnace_registers):
        self.ip = ip
        self.port = port
        self.connected = False

        self.registers = registers

    def connect(self):
        """Simulate the modbus server connection."""
        self.connected = True
        logging.debug(f"Connected to FakeModbusClient at {self.ip}:{self.port}.")

    def close(self):
        """Simulate ending the modbus server connection."""
        self.connected = False
        logging.debug(f"Connection to FakeModbusClient closed.")

    def read_coils(self, address, count, slave=1):
        """Simulate reading modbus coils."""
        values = [self.registers.get(address+i, 0) for i in range(count)]

        return MockResponse(bits=[bool(self.registers.get(address,0))])

    def write_coil(self, address, value, slave=1):
        """Simulate writing to a coil."""
        self.registers[address] = bool(value)
        return MockResponse()

    def write_registers(self, address, payload, slave=1, skip_encode=True):
        """Simulate a register write. Normally floats would be written over two registers, but
        there is no such restriction here. This avoids any bit manipulation for the fake client.
        """
        payload = b"".join(payload)  # Needs to be one byte string to struct.unpack it
        registers = list(struct.unpack(f">{len(payload) // 2}H", payload))  # list of bytes
        decoder = BinaryPayloadDecoder.fromRegisters(
            registers, wordorder=Endian.LITTLE, byteorder=Endian.BIG
        )
        value = decoder.decode_32bit_float()

        self.registers[address] = value

        return MockResponse()

    def read_input_registers(self, address, count, slave=1):
        """Simulate a read of two input registers"""
        orig = self.registers.get(address, 0)
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
        builder.add_32bit_float(float(orig))

        return MockResponse(registers=builder.to_registers())

    def read_holding_registers(self, address, count, slave=1):
        """Simulate a read of two holding registers."""
        orig = self.registers.get(address, 0)
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
        builder.add_32bit_float(float(orig))

        return MockResponse(registers=builder.to_registers())


class MockResponse:
    """Response object to replicate common pymodbus responses."""

    def __init__(self, bits=None, registers=None):
        """Object definition. Bits represents coil/bool responses,  registers represents 16-bits."""
        self.bits = bits or []
        self.registers = registers or []


class MockPLC:
    """Class to mock the furnace hardware and do some basic simulated temperature control.
    The mock here only deals with one PID (a) for complexity reasons."""

    def __init__(self, mockClient):
        # Mock modbus client that adapter created
        self.client = mockClient

        # pid variables
        self.outputSum = 0
        self.temp = 25
        self.prev_temp = 0
        self.outmax = 1
        self.outmin = 0
        self.output =0

        # Simulation variables
        self.room = 25
        self.heat_coeff = 9.001
        self.cool_coeff = 0.004
        self.added_gradient = False

    def calculate_temp_change(self):
        # Temperature handling
        self.prev_temp = self.temp
        # Calculate it
        heating = self.heat_coeff * self.output**2
        cooling = self.cool_coeff * (self.prev_temp-self.room)
        temp_change = heating-cooling
        self.temp += temp_change

        self.client.registers[modAddr.thermocouple_a_inp] = self.temp

    def bg_temp_task(self):
        """Background thread task for the mock PLC.

        This method runs in the thread executor pool, sleeping for the specified interval and 
        incrementing its counter once per loop, until the background task enable is set to false.
        """
        # Get gradient/setpoints
        pid_base_sp = self.client.registers[modAddr.pid_setpoint_a_hold]

        wanted = self.client.registers[modAddr.gradient_wanted_hold]
        distance = self.client.registers[modAddr.gradient_distance_hold]
        theoretical = wanted * distance
        self.client.registers[modAddr.gradient_theory_inp] = theoretical
        gradientModifier = theoretical/2
        # No gradient signs like on real hardware as only one PID

        # Change ASPC value - with a rate of 0.2, this is just divided by 5. bg interval not likely to change while testing this
        autosp_rate = self.client.registers[modAddr.autosp_rate_hold] / 5
        if not self.client.registers[modAddr.autosp_heating_coil]:
            autosp_rate = -autosp_rate

        # Check enable - if not, exit
        if not self.client.registers[modAddr.pid_enable_a_coil]:
            self.output = 0
            self.outputSum = 0
            self.calculate_temp_change()
        else:
            # If gradient is on and not been added yet, add it
            if self.client.registers[modAddr.gradient_enable_coil] and not self.added_gradient:
                logging.warning(f"Adding gradient modifer to setpoint base")
                pid_base_sp += + gradientModifier
                self.added_gradient = True
            # If gradient is off and has been added, remove it
            elif not self.client.registers[modAddr.gradient_enable_coil] and self.added_gradient:
                logging.warning(f"Removing gradient modifer from setpoint base")
                pid_base_sp -= gradientModifier
                self.added_gradient = False
            # If gradient is on and has been added or if it's off and hasn't been added, do nothing
            pid_sp = pid_base_sp

            self.calculate_temp_change()

            # Do temp calcs - get values, make something up
            kp = self.client.registers[modAddr.pid_kp_a_hold]
            ki = self.client.registers[modAddr.pid_ki_a_hold]
            kd = self.client.registers[modAddr.pid_kd_a_hold]

            error = pid_sp - self.temp
            dInput = self.temp - self.prev_temp

            # Self.output is reset each time, self.outputSum is not as integral is cumulative
            if self.outputSum > self.outmax:
                self.outputSum = self.outmax
            elif self.outputSum < self.outmin:
                self.outputSum = self.outmin

            self.output = kp * error
            self.outputSum += ki * error
            self.output = self.outputSum - (kd * dInput)

            if self.output > self.outmax:
                self.output = self.outmax
            elif self.output < self.outmin:
                self.output = self.outmin

            # Write output
            self.client.registers[modAddr.pid_output_a_inp] = self.output
            self.client.registers[modAddr.pid_outputsum_a_inp] = self.outputSum

            # If ASPC
            if self.client.registers[modAddr.autosp_enable_coil]:
                pid_base_sp += autosp_rate
            # 'Write' new setpoint back to register
            self.client.registers[modAddr.pid_setpoint_a_hold] = pid_base_sp
