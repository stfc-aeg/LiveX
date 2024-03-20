import struct
import socket
import logging

class LiveXPacketDecoder(struct.Struct):

    def __init__(self, ip, port):
        """Initialise packet decoder.
        Super init to create expected structure for a packet, and set needed variables.
        """
        super().__init__('fff')

        # TCP client
        self.tcp_client = None
        self.ip = ip
        self.port = port

        # Values
        self.reading_counter = None
        self.temperature_a = None
        self.temperature_b = None

    def initialise_tcp_client(self):
        """Initialise the tcp client."""

        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((self.ip, self.port))

        self.tcp_client.settimeout(1)
        activate = '1'
        self.tcp_client.send(activate.encode())

    def close_tcp_client(self):
        """Safely end the connection."""
        self.tcp_client.close()

    def receive(self):
        """Read the latest data from the stream, if it exists."""
        try:
            reading = self.tcp_client.recv(12)
            (self.reading_counter, self.temperature_a, self.temperature_b) = super().unpack(reading)
            logging.debug(self.reading_counter)
        except socket.timeout:
            logging.debug("TCP Socket timeout: read no data")
        except Exception as e:
            logging.debug(f"Other TCP error: {str(e)}")
            return False
        return True

    def as_dict(self):
        """Return all the values as a dictionary."""

        dictionary = {
            'counter': self.reading_counter,
            'temperature_a': self.temperature_a,
            'temperature_b': self.temperature_b
        }
        return dictionary