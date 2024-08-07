"""Basic adapter for LiveX control

This class implements a simple adapter which reads values from the Modbus server and stores them
in the parameter tree for web interface access.
The web interface sends data to the adapter which translates this into Modbus commands
to be read by the PLC.

Mika Shearwood, Detector Systems Software Group
"""
import logging

from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTreeError
from odin.util import decode_request_body

from livex.furnace.controller import FurnaceController, LiveXError

class FurnaceAdapter(ApiAdapter):
    """Furnace adapter class for the ODIN server.

    This adapter provides ODIN clients with access to the furnace parameters.
    """

    def __init__(self, **kwargs):
        """Initialize the FurnaceAdapter object.

        This constructor initializes the FurnaceAdapter object.

        :param kwargs: keyword arguments specifying options
        """

        # Intialise superclass
        super(FurnaceAdapter, self).__init__(**kwargs)

        # Parse options
        bg_read_task_enable = bool(self.options.get('background_read_task_enable', False))
        bg_read_task_interval = float(self.options.get('background_read_task_interval', 1.0))

        bg_stream_task_enable = bool(self.options.get('background_stream_task_enable', False))
        pid_frequency = int(self.options.get('pid_frequency', 50))

        ip = self.options.get('ip', '192.168.0.159')
        port = int(self.options.get('port', '4444'))

        log_directory = self.options.get('log_directory', 'logs')
        # Filename may instead be generated? Cannot have just one configurable one,
        # subsequent uses would overwrite. generation method TBD. metadata, date/time, etc.
        log_filename = self.options.get('log_filename', 'default.hdf5')

        temp_monitor_retention = int(self.options.get('temp_monitor_retention', 60))

        self.furnace = FurnaceController(
            bg_read_task_enable, bg_read_task_interval,
            bg_stream_task_enable, pid_frequency,
            ip, port,
            log_directory, log_filename,
            temp_monitor_retention
        )

        logging.debug('FurnaceAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.furnace.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json',"application/vnd.odin-native")
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            data = decode_request_body(request)
            self.furnace.set(path, data)
            response = self.furnace.get(path)
            content_type = "applicaiton/json"
            status = 200

        except ParameterTreeError as param_error:
            response = {'response': 'TriggerAdapter PUT error: {}'.format(param_error)}
            content_type = 'application/json'
            status = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'FurnaceAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def cleanup(self):
        """Clean up adapter state at shutdown.

        This method cleans up the adapter state when called by the server at e.g. shutdown.
        It simplied calls the cleanup function of the LiveX instance.
        """
        self.furnace.cleanup()

    def initialize(self, adapters):
        """Get list of adapters and call relevant functions for them."""
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
