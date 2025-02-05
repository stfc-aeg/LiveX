import struct
import logging

class LiveXPacketDecoder(struct.Struct):

    def __init__(self):
        """Initialise packet decoder.
        Super init to create expected structure for a packet, and set needed variables.
        :param pid_debug: bool dictating whether to unpack debugging data or normal datas
        """
        super().__init__('f ffffffff ffffffff')  # counter, then 7 for each

        # Values
        self.keys = [
            'counter',
            'temperature_a', 'output_a', 'kp_a', 'ki_a', 'kd_a', 'lastInput_a', 'outputSum_a', 'setpoint_a',
            'temperature_b', 'output_b', 'kp_b', 'ki_b', 'kd_b', 'lastInput_b', 'outputSum_b', 'setpoint_a'
        ]

        self.data = {key: None for key in self.keys}  # Initialise all values to None

    def unpack(self, reading):
        """Read the latest data from the stream and unpack it into initialised values."""
        unpacked = super().unpack(reading)

        # Mapping
        for key, value in zip(self.keys, unpacked):
            self.data[key] = value

        return self.data
