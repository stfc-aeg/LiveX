import struct
import logging

class LiveXPacketDecoder(struct.Struct):

    def __init__(self):
        """Initialise packet decoder.
        Super init to create expected structure for a packet, and set needed variables.
        """
        super().__init__('fff')

        # Values
        self.reading_counter = None
        self.temperature_a = None
        self.temperature_b = None

    def unpack(self, reading):
        """Read the latest data from the stream and unpack it into initialised values."""
        (self.reading_counter, self.temperature_a, self.temperature_b) = super().unpack(reading)

        return reading

    def as_dict(self):
        """Return all the values as a dictionary."""

        dictionary = {
            'counter': self.reading_counter,
            'temperature_a': self.temperature_a,
            'temperature_b': self.temperature_b
        }
        return dictionary