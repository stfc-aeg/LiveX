import numpy as np
import cv2
import base64
import zmq
from multiprocessing import Process, Queue, Pipe

from tornado.escape import json_decode
from odin_data.ipc_channel import IpcChannel

class LiveDataProcessor():
    """Class to process image data received on a multiprocess that it instantiates."""

    def __init__(self, endpoint, size_x=640, size_y=480, colour='bone'):
        """Initialise the LiveDataProcessor object.
        This method constructs the Queue, Pipes and Process necessary for multiprocessing.
        :param endpoint: string representation of endpoint for image data.
        :param size_x: integer width of image in pixels (default 640).
        :param size_y: integer height of image in pixels (default 480).
        :param colour: string of opencv colourmap label (default 'bone').
        For colourmap options, see https://docs.opencv.org/3.4/d3/d50/group__imgproc__colormap.html
        """
        self.endpoint = endpoint
        self.size_x = size_x
        self.size_y = size_y
        self.dimensions = [size_x, size_y]
        self.colour = colour
        self.image = 0

        self.image_queue = Queue(maxsize=1)
        self.pipe_parent, self.pipe_child = Pipe(duplex=True)
        self.process = Process(target=self.capture_images, args=(self,))
        self.process.start()

    @staticmethod
    def capture_images(processor):
        """Create an IPC channel with the processor's endpoint and get data from it.
        Continuously polls the pipe (for processor parameters) and the channel (for images).
        On successful poll, clears queue to get latest image, to avoid historical data.
        :param processor: LiveDataProcessor object to reference.
        """
        channel = IpcChannel(IpcChannel.CHANNEL_TYPE_SUB, processor.endpoint)
        channel.connect()
        channel.subscribe()

        while True:
            pipe_poll_success = processor.pipe_child.poll()  # Do not need to wait for this, take the update if it's there
            if pipe_poll_success:
                params = processor.pipe_child.recv()
                for param, value in params.items():
                    setattr(processor, param, value)

            poll_success = channel.poll(10)
            if poll_success:
                # Continuously read values until the queue is empty - ensuring images are up-to-date
                while True:
                    try:
                        latest_message = channel.socket.recv_multipart(flags=zmq.NOBLOCK)
                    except zmq.Again:
                        break
                processor.read_data_from_socket(latest_message)

    def read_data_from_socket(self, msg):
        """Decode, interpret, and resize/recolour/render the data received.
        :param msg: JSON message of header and image data.
        """
        header = json_decode(msg[0])

        dtype = 'float32' if header['dtype'] == "float" else header['dtype']
        data = np.frombuffer(msg[1], dtype=dtype)
        data = data.reshape((2304, 4096)) # ORCA dimensions

        # OpenCV operations
        data = cv2.resize(data, (self.size_x, self.size_y))
        data = cv2.applyColorMap((data / 256).astype(np.uint8), self.get_colour_map())
        _, buffer = cv2.imencode('.jpg', data)
        buffer = np.array(buffer)

        zipped_data = base64.b64encode(buffer)

        while (not self.image_queue.empty()):
            self.image_queue.get()

        self.image_queue.put(zipped_data.decode('utf-8'))

    def get_colour_map(self):
        """Get the colour map based on the colour string. Defaults to 'bone' (greyscale)."""
        return getattr(cv2, f'COLORMAP_{self.colour.upper()}', cv2.COLORMAP_BONE)

    def get_image(self):
        """If it exists, update the image with one from the queue. Then return the image."""
        if not self.image_queue.empty():
            self.image = self.image_queue.get()
        return self.image