import struct
import logging

class LiveXPacketDecoder(struct.Struct):

    def __init__(self, pid_debug=False):
        """Initialise packet decoder.
        Super init to create expected structure for a packet, and set needed variables.
        :param pid_debug: bool dictating whether to unpack debugging data or normal datas
        """
        if pid_debug:
            super().__init__('f fffffff fffffff')  # counter, then 7 for each

            # Values
            self.keys = [
                'counter',
                'temperatureA', 'outputA', 'kpA', 'kiA', 'kdA', 'lastInputA', 'outputSumA',
                'temperatureB', 'outputB', 'kpB', 'kiB', 'kdB', 'lastInputB', 'outputSumB'
            ]
        else:
            super().__init__('fff')
            self.keys = ['counter', 'temperature_a', 'temperature_b']

        self.data = {key: None for key in self.keys}  # Initialise all values to None

    def unpack(self, reading):
        """Read the latest data from the stream and unpack it into initialised values."""
        unpacked = super().unpack(reading)

        # Mapping
        for key, value in zip(self.keys, unpacked):
            self.data[key] = value

        return self.data
