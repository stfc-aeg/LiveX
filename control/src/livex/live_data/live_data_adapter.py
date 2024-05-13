import logging
import numpy as np
import cv2

import base64
import time


from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.util import decode_request_body
from tornado.escape import json_decode

from odin_data.ipc_channel import IpcChannelException
from odin_data.ipc_tornado_channel import IpcTornadoChannel

ENDPOINT_CONFIG_NAME = "live_data_endpoints"
DEFAULT_ENDPOINT = "tcp://192.168.0.31:5020"


class LiveDataAdapter(ApiAdapter):

    def __init__(self, **kwargs):
        super(LiveDataAdapter, self).__init__(**kwargs)

        endpoint = self.options.get(ENDPOINT_CONFIG_NAME, DEFAULT_ENDPOINT)

        self.live_viewer = LiveDataViewer(endpoint)

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


class LiveDataViewer():

    def __init__(self, endpoint):

        logging.debug("Initialising Live Data Viewer")

        # defaults, to be done via config
        self.colour = 'plasma'
        self.resize_x = 640
        self.resize_y = 480

        self.endpoint = endpoint
        self.data_header = {"Error": "No Header Yet",
                            "shape": [256, 256]}

        self.data = np.reshape(np.arange(65536, dtype=np.uint8), [256, 256])
        self.clipped_data = np.reshape(np.arange(65536, dtype=np.uint8), [256, 256])

        self.min = None
        self.max = None
        # self.image stores the image data, updated only when image is rendered
        self.image = 0

        try:
            self.ipc_channel = SubSocket(self, endpoint)
        except IpcChannelException as chan_error:
            logging.warning("Unable to subscribe to %s: %s", endpoint, chan_error)
        
        self.param_tree = ParameterTree({
            "endpoint": (self.endpoint, None),
            "header": (lambda: self.data_header, None),
            "data": (lambda: self.image, None),
            "clipping":
                {
                    "min": (lambda: self.min, self.set_clip_min),
                    "max": (lambda: self.max, self.set_clip_max)
                },
            "image":
                {
                    "size_x": (lambda: self.resize_x, self.set_img_x),
                    "size_y": (lambda: self.resize_y, self.set_img_y),
                    "colour": (lambda: self.colour, self.set_img_colour)
                }
        })

    def read_data_from_socket(self, msg):

        header = json_decode(msg[0])
        # logging.debug("Received Data with Header: %s", header)

        self.data_header = header
        dtype = header['dtype']
        if dtype == "float":
            dtype = "float32"

        self.data_header["shape"] = [int(header["shape"][0]), int(header["shape"][1])]
        self.data = np.fromstring(msg[1], dtype=dtype)

        self.data = self.data.reshape((2304, 4096))  # Height and width of ORCA

        # opencv data operations. resize, recolour, render
        self.data = cv2.resize(self.data, (self.resize_x, self.resize_y))
        self.data = cv2.applyColorMap((self.data/256).astype(np.uint8), self.get_colour_map())
        _, buffer = cv2.imencode('.jpg', self.data)  # 165ms at full size
        buffer = np.array(buffer)

        zipped_data = base64.b64encode(buffer)
        self.image = zipped_data.decode('utf-8')

        self.clipped_data = self.clip_data(self.min, self.max)

    def set_img_x(self, value):
        """Set the width of the image in pixels.
        :param value: integer representing number of pixels.
        """
        self.resize_x = int(value)

    def set_img_y(self, value):
        """Set the height of the image in pixels.
        :param value: integer representing number of pixels.
        """
        self.resize_y = int(value)

    def set_img_colour(self, value):
        """Set the colour of the image in the parameter tree, used to determine the colour map.
        :param value: colour map name as a string. see get_colour_map
        """
        self.colour = str(value)

    def get_colour_map(self):
        """Return the appropriate colourmap, defaulting to 'bone' (greyscale)."""
        colour = self.colour.upper()
        if colour == 'AUTUMN':
            return cv2.COLORMAP_AUTUMN
        elif colour == 'BONE':
            return cv2.COLORMAP_BONE
        elif colour == 'JET':
            return cv2.COLORMAP_JET
        elif colour == 'WINTER':
            return cv2.COLORMAP_WINTER
        elif colour == 'RAINBOW':
            return cv2.COLORMAP_RAINBOW
        elif colour == 'OCEAN':
            return cv2.COLORMAP_OCEAN
        elif colour == 'SUMMER':
            return cv2.COLORMAP_SUMMER
        elif colour == 'SPRING':
            return cv2.COLORMAP_SPRING
        elif colour == 'COOL':
            return cv2.COLORMAP_COOL
        elif colour == 'HSV':
            return cv2.COLORMAP_HSV
        elif colour == 'PINK':
            return cv2.COLORMAP_PINK
        elif colour == 'HOT':
            return cv2.COLORMAP_HOT
        elif colour == 'PARULA':
            return cv2.COLORMAP_PARULA
        elif colour == 'MAGMA':
            return cv2.COLORMAP_MAGMA
        elif colour == 'INFERNO':
            return cv2.COLORMAP_INFERNO
        elif colour == 'PLASMA':
            return cv2.COLORMAP_PLASMA
        elif colour == 'VIRIDIS':
            return cv2.COLORMAP_VIRIDIS
        elif colour == 'CIVIDIS':
            return cv2.COLORMAP_CIVIDIS
        elif colour == 'TWILIGHT':
            return cv2.COLORMAP_TWILIGHT
        elif colour == 'TWILIGHT_SHIFTED':
            return cv2.COLORMAP_TWILIGHT_SHIFTED
        elif colour == 'TURBO':
            return cv2.COLORMAP_TURBO
        elif colour == 'DEEPGREEN':
            return cv2.COLORMAP_DEEPGREEN
        else:
            print(f"No valid colormap found for {colour}. Defaulting to COLORMAP_BONE.")
            return cv2.COLORMAP_BONE

    def clip_data(self, min, max):
        try:
            clipped_data = np.clip(self.data, min, max)
        except ValueError:
            clipped_data = self.data

        return clipped_data

    def set_clip_min(self, min):
        self.min = min
        self.clip_data(min, self.max)

    def set_clip_max(self, max):
        self.max = max
        self.clip_data(self.min, max)

    def get_data(self):
        _, buffer = cv2.imencode('.jpg', self.data)
        buffer = np.array(buffer)
        zipped_data = base64.b64encode(buffer)
        return zipped_data.decode("utf-8")

    def get_plotly_data(self):
        zipped_data = base64.b64encode(self.plotly_data)
        return zipped_data.decode("utf-8")

    def get(self, path):
        """Get attribute from parameter tree."""
        # logging.debug(self.param_tree)
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set attribute in parameter tree."""
        self.param_tree.set(path, data)


class SubSocket(object):
    """
    Subscriber Socket class.

    This class implements an IPC channel subcriber socker and sets up a callback function
    for receiving data from that socket that counts how many images it receives during its lifetime.
    """

    def __init__(self, parent, endpoint):
        """
        Initialise IPC channel as a subscriber, and register the callback.

        :param parent: the class that created this object, a LiveViewer, given so that this object
        can reference the method in the parent
        :param endpoint: the URI address of the socket to subscribe to
        """
        self.parent = parent
        self.endpoint = endpoint
        self.frame_count = 0

        # context = zmq.Context()
        # socket = context.socket(zmq.SUB)
        # socket.connect(endpoint)
        # socket.setsockopt_string(zmq.SUBSCRIBE, "")

        self.channel = IpcTornadoChannel(IpcTornadoChannel.CHANNEL_TYPE_SUB, endpoint=endpoint)
        self.channel.subscribe()
        self.channel.connect()
        # register the get_image method to be called when the ZMQ socket receives a message
        self.channel.register_callback(self.callback)

    def callback(self, msg):
        """
        Handle incoming data on the socket.

        This callback method is called whenever data arrives on the IPC channel socket.
        Increments the counter, then passes the message on to the image renderer of the parent.
        :param msg: the multipart message from the IPC channel
        """
        self.frame_count += 1
        self.parent.read_data_from_socket(msg)

    def cleanup(self):
        """Cleanup channel when the server is closed. Closes the IPC channel socket correctly."""
        self.channel.close()