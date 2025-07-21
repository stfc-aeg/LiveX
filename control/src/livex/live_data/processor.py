import numpy as np
import cv2
import blosc
import base64
import zmq
from multiprocessing import Process, Queue, Pipe

import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from tornado.escape import json_decode
from odin_data.control.ipc_channel import IpcChannel

class LiveDataProcessor():
    """Class to process image data received on a multiprocess that it instantiates."""

    def __init__(self, endpoint, resolution, size_x=2048, size_y=1152, colour='bone'):
        """Initialise the LiveDataProcessor object.
        This method constructs the Queue, Pipes and Process necessary for multiprocessing.
        :param endpoint: string representation of endpoint for image data.
        :param resolution: dict ({'x': x, 'y': y}) of maximum image dimensions
        :param size_x: integer width of output image in pixels (default 640).
        :param size_y: integer height of output image in pixels (default 480).
        :param colour: string of opencv colourmap label (default 'bone').
        For colourmap options, see https://docs.opencv.org/3.4/d3/d50/group__imgproc__colormap.html
        """
        self.endpoint = endpoint
        self.max_size_x = resolution['x']
        self.max_size_y = resolution['y']
        self.size_x = size_x
        self.size_y = size_y
        self.out_dimensions = [size_x, size_y]
        self.colour = colour

        self.resolution_percent = 100

        self.image = 0
        self.histogram = None

        # Minimum and maximum values that the camera data can be. e.g.: 16-bit pixel data, 65535
        self.cam_pixel_min = 0
        self.cam_pixel_max = 65535

        # Matplotlib fontmanager and PngImagePlugin fill log, so they are disabled here
        logging.getLogger('matplotlib.font_manager').disabled = True
        logging.getLogger('PIL.PngImagePlugin').disabled=True

        # Region of interest limits. 0 to dimension until changed
        self.roi = {
            'x_lower': 0,
            'x_upper': self.max_size_x,
            'y_lower': 0,
            'y_upper': self.max_size_y,
            'percent': {
                'x_lower': 0,
                'x_upper': 100,
                'y_lower': 0,
                'y_upper': 100
            }
        }
        self.clipping = {
            'min': 0,
            'max': 65535,
            'percent': {
                'min': 0,
                'max': 100
            }
        }

        self.image_queue = Queue(maxsize=1)
        self.hist_queue = Queue(maxsize=1)
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

        # Check for image compression by checking raw data size. Decompress if needed
        # Currently assumes bytes-per-pixel of 2
        if len(msg[1]) != (self.max_size_x*self.max_size_y*2):
            uncompressed_data = blosc.decompress(msg[1])
            data = np.fromstring(uncompressed_data, dtype=dtype)
        else:
            data = np.frombuffer(msg[1], dtype=dtype)  # Otherwise, grab the data as-is

        # For histogram, it's easier to clip the data before reshaping it
        clipped_ = np.clip(data, self.clipping['min'], self.clipping['max'])
        # After clipping, scale data back out to full range
        scaled_data = ((clipped_ - self.clipping['min']) / (self.clipping['max'] - self.clipping['min'])) * 65535

        reshaped_data = scaled_data.reshape((2304, 4096)) # ORCA dimensions

        # OpenCV operations
        resized_data = cv2.resize(reshaped_data, (self.size_x, self.size_y))

        roi_data = resized_data[self.roi['y_lower']:self.roi['y_upper'],
                        self.roi['x_lower']:self.roi['x_upper']]

        colour_data = cv2.applyColorMap((roi_data / 256).astype(np.uint8), self.get_colour_map())
        _, buffer = cv2.imencode('.jpg', colour_data)
        buffer = np.array(buffer)

        while (not self.image_queue.empty()):
            self.image_queue.get()

        # self.image_queue.put(zipped_data.decode('utf-8'))
        self.image_queue.put(buffer.tobytes())

        # Fixed quantity of bins instead of generating it from range
        bins_count = 2048

        # Create histogram
        flat_data = data.flatten()  # Histogram made on original data
        fig, ax = plt.subplots(figsize=(8,2), dpi=100)
        ax.hist(flat_data, bins=bins_count, alpha=0.75, color='blue', log=True)

        # No y-axis
        ax.yaxis.set_visible(False)
        for spine in ['top', 'left', 'right']:
            ax.spines[spine].set_visible(False)
        # Make x-axis take entire width
        ax.set_xlim(left=self.clipping['min'], right=self.clipping['max'])

        fig.tight_layout(pad=0.05)

        # Generate matplotlib figure and convert it to array
        fig.canvas.draw()
        histData = np.frombuffer(fig.canvas.renderer.buffer_rgba(), dtype=np.uint8)
        width, height = fig.canvas.get_width_height()
        # Resize frombuffer array to 3d
        histData = histData.reshape((height, width, 4))
        histData = cv2.cvtColor(histData, cv2.COLOR_RGBA2BGR)

        # Must explicitly close figures
        plt.close(fig)

        _, histImage = cv2.imencode('.jpg', histData)
        zipped_data = base64.b64encode(histImage)
        while (not self.hist_queue.empty()):
            self.hist_queue.get()
        self.hist_queue.put(zipped_data.decode('utf-8'))

    def get_colour_map(self):
        """Get the colour map based on the colour string. Defaults to 'bone' (greyscale)."""
        return getattr(cv2, f'COLORMAP_{self.colour.upper()}', cv2.COLORMAP_BONE)

    def get_histogram(self):
        """If it exists, update the histogram with one from the queue, then return it."""
        if not self.hist_queue.empty():
            self.histogram = self.hist_queue.get()
        return self.histogram

    def get_image(self):
        """If it exists, update the image with one from the queue. Then return the image."""
        if not self.image_queue.empty():
            self.image = self.image_queue.get()
        return self.image