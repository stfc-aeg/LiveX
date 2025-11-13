import struct
import logging

class LiveXPacketDecoder(struct.Struct):

    def __init__(self, pid_debug=False):
        """Initialise packet decoder.
        Super init to create expected structure for a packet, and set needed variables.
        :param pid_debug: bool dictating whether to unpack debugging data or normal data
        """
        super().__init__('f ffffffff ffffffff')  # counter, then 7 for each

        self.pid_debug = pid_debug  # debug flag

        # all values: used for debug data
        # this should match the order of the object send via TCP in TaskPid on the hardware
        self.all_keys = [
            'counter',
            'temperature_upper', 'output_upper', 'kp_upper', 'ki_upper', 'kd_upper', 'lastInput_upper', 'outputSum_upper', 'setpoint_upper',
            'temperature_lower', 'output_lower', 'kp_lower', 'ki_lower', 'kd_lower', 'lastInput_lower', 'outputSum_lower', 'setpoint_upper'
        ]

        # keys for non-debug data
        self.selected_keys = ['counter', 'temperature_upper', 'temperature_lower']
        # for pulling the selected values out of the unpacked reading
        self.selected_indexes = [self.all_keys.index(key) for key in self.selected_keys]

        self.keys = self.all_keys if pid_debug else self.selected_keys
        self.data = {key: None for key in self.keys}  # Initialise all values to None

    def unpack(self, reading):
        """Read the latest data from the stream and unpack it into initialised values."""
        unpacked = super().unpack(reading)

        if self.pid_debug:
            # Get all values
            self.data = dict(zip(self.all_keys, unpacked))
        else:
            # Get only selected values
            self.data = {key: unpacked[i] for key, i in zip(self.keys, self.selected_indexes)}

        return self.data
