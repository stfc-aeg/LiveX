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

from livex.livex import LiveX, LiveXError

class LiveXAdapter(ApiAdapter):
    """System info adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server and the system that it is
    running on.
    """

    def __init__(self, **kwargs):
        """Initialize the LiveXAdapter object.

        This constructor initializes the LiveXAdapter object.

        :param kwargs: keyword arguments specifying options
        """

        # Intialise superclass
        super(LiveXAdapter, self).__init__(**kwargs)

        # Parse options
        bg_read_task_enable = bool(self.options.get('background_read_task_enable', False))
        bg_read_task_interval = float(self.options.get('background_read_task_interval', 1.0))

        bg_stream_task_enable = bool(self.options.get('background_stream_task_enable', False))
        pid_frequency = int(self.options.get('pid_frequency', 50))

        log_directory = self.options.get('log_directory', 'logs')
        # Filename may instead be generated? Cannot have just one configurable one,
        # subsequent uses would overwrite. generation method TBD. metadata, date/time, etc.
        log_filename = self.options.get('log_filename', 'default.hdf5')

        temp_monitor_retention = int(self.options.get('temp_monitor_retention', 60))

        self.livex = LiveX(
            bg_read_task_enable, bg_read_task_interval,
            bg_stream_task_enable, pid_frequency,
            log_directory, log_filename,
            temp_monitor_retention
        )

        logging.debug('LiveXAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.livex.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """

        content_type = 'application/json'

        try:
            data = json_decode(request.body)
            self.livex.set(path, data)
            response = self.livex.get(path)
            status_code = 200
        except LiveXError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'LiveXAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def cleanup(self):
        """Clean up adapter state at shutdown.

        This method cleans up the adapter state when called by the server at e.g. shutdown.
        It simplied calls the cleanup function of the LiveX instance.
        """
        self.livex.cleanup()

    def initialize(self, adapters):
        """Get list of adapters and call relevant functions for them."""
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
