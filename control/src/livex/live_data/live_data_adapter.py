import logging
import numpy as np
import cv2
import base64
import zmq
from multiprocessing import Process, Queue, Pipe

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.util import decode_request_body
from tornado.escape import json_decode

from odin_data.ipc_channel import IpcChannel

ENDPOINT_CONFIG_NAME = "live_data_endpoints"
DEFAULT_ENDPOINT = "tcp://192.168.0.31:5020"

class LiveDataAdapter(ApiAdapter):

    def __init__(self, **kwargs):
        super(LiveDataAdapter, self).__init__(**kwargs)

        num_endpoints = int(self.options.get('num_endpoints', 1))

        # Split on comma, remove whitespace if it exists
        endpoints = [
            item.strip() for item in self.options.get('livedata_endpoint', None).split(",")
        ]

        self.live_viewer = LiveDataController(num_endpoints, endpoints)

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        try:
            response = self.live_viewer.get(path)
            content_type = "application/json"
            status = 200
        except ParameterTreeError as param_error:
            response = {'response': 'LiveDataAdapter GET error: {}'.format(param_error)}
            content_type = 'application/json'
            status = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status)

    @response_types('application/json', default='application/json')
    def put(self, path, request):
        try:
            data = decode_request_body(request)
            self.live_viewer.set(path, data)
            response = self.live_viewer.get(path)
            content_type = "applicaiton/json"
            status = 200

        except ParameterTreeError as param_error:
            response = {'response': 'LiveViewAdapter PUT error: {}'.format(param_error)}
            content_type = 'application/json'
            status = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status)

    def cleanup(self):
        self.live_viewer.cleanup()


class LiveDataController():

    def __init__(self, num_endpoints, endpoints):

        logging.debug("Initialising Live Data Viewer")

        self.processors = []
        self.tree = {
            "liveview": []
        }

        for i in range(num_endpoints):
            self.processors.append(
                LiveDataProcessor(endpoints[i])
            )

            self.tree['liveview'].append(self.processors[i].tree)

        self.param_tree = ParameterTree(self.tree)

    def get(self, path):
        """Get attribute from parameter tree."""
        # logging.debug(self.param_tree)
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set attribute in parameter tree."""
        self.param_tree.set(path, data)

    def cleanup(self):
        """Clean up the LiveDataController instance.
        This method terminates thread processes, allowing shutdown.
        """
        for process in self.processes:
            process.terminate()


class LiveDataProcessor():
    """Class to process images received on the capture_images threads.
    Also handles the parameter tree for values associated with that image."""

    def __init__(self, endpoint, resize_x=2048, resize_y=1152, colour='bone'):
        self.endpoint = endpoint
        self.image_queue = Queue(maxsize=1)

        self.size_x = resize_x
        self.size_y = resize_y
        self.colour = colour

        self.image = 0

        self.pipe_parent, self.pipe_child = Pipe(duplex=True)
        self.process = Process(target=self.capture_images, args=(self,))
        self.process.start()

        self.tree = {
            "endpoint": (lambda: self.endpoint, None),
            "image":
            {
                "size_x": (lambda: self.size_x, self.set_img_x),
                "size_y": (lambda: self.size_y, self.set_img_y),
                "colour": (lambda: self.colour, self.set_img_colour),
                "data": (lambda: self.get_image(), None)
            }
        }

    @staticmethod
    def capture_images(processor):
        """Continually poll the channel, reading the data if there is a reply."""
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
        """Decode, interpret, and operate on the data received.
        :param msg: JSON message of header and image data.
        """
        header = json_decode(msg[0])

        dtype = 'float32' if header['dtype'] == "float" else header['dtype']
        data = np.frombuffer(msg[1], dtype=dtype)
        data = data.reshape((2304, 4096)) # ORCA dimensions

        # OpenCV operations
        logging.debug(f"Image operations. x: {self.size_x}, y: {self.size_y}")
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
        # if pipe has image, set self.image to pipe.get
        if not self.image_queue.empty():
            self.image = self.image_queue.get()
        return self.image

    def update_render_info(self):
        # only thing piped TO thread
        params = {
            "size_x": self.size_x,
            "size_y": self.size_y,
            "colour": self.colour
        }
        self.pipe_parent.send(params)

    def set_img_x(self, value):
        """Set the width of the image in pixels.
        :param value: integer representing number of pixels.
        """
        self.size_x = int(value)
        self.update_render_info()

    def set_img_y(self, value):
        """Set the height of the image in pixels.
        :param value: integer representing number of pixels.
        """
        self.size_y = int(value)
        self.update_render_info()

    def set_img_colour(self, value):
        """Set the colour of the image in the parameter tree, used to determine the colour map.
        :param value: colour map name as a string. see get_colour_map
        """
        self.colour = str(value)
        self.update_render_info()
