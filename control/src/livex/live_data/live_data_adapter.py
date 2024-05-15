import logging
import numpy as np
import cv2
import base64
import zmq
from multiprocessing import Process, Queue, Pipe
from functools import partial

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.util import decode_request_body
from tornado.escape import json_decode

from odin_data.ipc_channel import IpcChannel

ENDPOINT_CONFIG_NAME = "live_data_endpoints"
DEFAULT_ENDPOINT = "tcp://192.168.0.31:5020"

class LiveDataAdapter(ApiAdapter):
    """Liveview/data adapter for the ODIN server.
    
    This adapter provides ODIN clients with access to the image preview and its parameters.
    """
    def __init__(self, **kwargs):
        """Initialise the LiveDataAdapter object.
        :param kwargs: keyword arguments specifying options.
        """
        super(LiveDataAdapter, self).__init__(**kwargs)
        # Split on comma, remove whitespace if it exists
        endpoints = [
            item.strip() for item in self.options.get('livedata_endpoint', None).split(",")
        ]

        self.live_viewer = LiveDataController(endpoints)

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
    """Class to instantiate and manage the ParameterTree for LiveDataProcessor classes."""

    def __init__(self, endpoints):
        """Initialise the LiveDataController. Create a LiveDataProcessor for each endpoint
        provided in config, then create a ParameterTree to handle behaviours for those classes.
        :param endpoints: list of endpoints in string format.
        """
        logging.debug("Initialising LiveDataController.")

        self.processors = []
        self.tree = {
            "liveview": []
        }

        # For each provided endpoint
        for i in range(len(endpoints)):
            self.processors.append(
                LiveDataProcessor(endpoints[i])
            )

            proc = self.processors[i]

            # Create 'branch' of ParameterTree for each Processor
            tree = {
                "endpoint": (lambda: self.processors[i].endpoint, None),
                "image":
                {  # Partials provide processor as an argument
                    "size_x": (lambda proc=proc: self.processors[i].size_x,
                               partial(self.set_img_x, processor=proc)),
                    "size_y": (lambda: self.processors[i].size_y, 
                               partial(self.set_img_y, processor=proc)),
                    "colour": (lambda: self.processors[i].colour, 
                               partial(self.set_img_colour, processor=proc)),
                    "data": (lambda: proc.get_image(), None)
                    # Use get_image in processor for JSON serialisation
                }
            }
            self.tree['liveview'].append(tree)

        self.param_tree = ParameterTree(self.tree)

    def update_render_info(self, processor):
        """Pipe updated parameters to processor thread.
        :param processor: LiveDataProcessor object to reference.
        """
        # Could be done programmatically but not enough to warrant this complexity
        params = {
            "size_x": processor.size_x,
            "size_y": processor.size_y,
            "colour": processor.colour
        }
        processor.pipe_parent.send(params)

    def set_img_x(self, value, processor):
        """Set the width of the image in pixels.
        :param value: integer representing number of pixels.
        :param processor: LiveDataProcessor object to reference
        """
        processor.size_x = int(value)
        self.update_render_info(processor)

    def set_img_y(self, value, processor):
        """Set the height of the image in pixels.
        :param value: integer representing number of pixels.
        :param processor: LiveDataProcessor object to reference
        """
        processor.size_y = int(value)
        self.update_render_info(processor)

    def set_img_colour(self, value, processor):
        """Set the colour of the image in the parameter tree, used to determine the colour map.
        :param value: colour map name as a string. see get_colour_map
        :param processor: LiveDataProcessor object to reference
        """
        processor.colour = str(value)
        self.update_render_info(processor)

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
        logging.debug(f"Terminating {len(self.processors)} processes.")
        for processer in self.processors:
            processer.process.terminate()


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