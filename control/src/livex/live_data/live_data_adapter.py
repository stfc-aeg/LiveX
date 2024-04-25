import logging
import numpy as np

# compression test options
import gzip
import base64
import json

import zmq

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
        logging.debug("######################################################################################")

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

        self.endpoint = endpoint
        self.data_header = {"Error": "No Header Yet",
                            "shape": [256, 256]}

        self.data = np.reshape(np.arange(65536, dtype=np.uint8), [256, 256])
        self.clipped_data = np.reshape(np.arange(65536, dtype=np.uint8), [256, 256])

        self.min = None
        self.max = None

        try:
            self.ipc_channel = SubSocket(self, endpoint)
        except IpcChannelException as chan_error:
            logging.warning("Unable to subscribe to %s: %s", endpoint, chan_error)
        
        self.param_tree = ParameterTree({
            "endpoint": (self.endpoint, None),
            "header": (lambda: self.data_header, None),
            "data": (self.get_data, None),
            "clipping":
                {
                    "min": (lambda: self.min, self.set_clip_min),
                    "max": (lambda: self.max, self.set_clip_max)
                }

        })

    def get(self, path):
        # logging.debug(self.param_tree)
        return self.param_tree.get(path)

    def set(self, path, data):
        self.param_tree.set(path, data)

    def read_data_from_socket(self, msg):

        header = json_decode(msg[0])
        logging.debug("Received Data with Header: %s", header)

        # logging.debug("'''''''''''''''''''''''''''''''''''''''''")
        # logging.debug(msg[1])

        self.data_header = header
        dtype = header['dtype']
        if dtype == "float":
            dtype = "float32"

        self.data_header["shape"] = [int(header["shape"][0]), int(header["shape"][1])]
        self.data = np.fromstring(msg[1], dtype=dtype)

        logging.debug("Data Type: %s", self.data.dtype)

        # np.reshape(self.data, [int(header["shape"][0]), int(header["shape"][1])])
        logging.debug(self.data)
        self.clipped_data = self.clip_data(self.min, self.max)

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

        # zipped_data = gzip.compress(self.clipped_data)
        zipped_data = base64.b64encode(self.data)
        # temp_data = self.data
        # logging.debug(self.data)
        # logging.debug(zipped_data.decode('utf-8'))
        return zipped_data.decode("utf-8")


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