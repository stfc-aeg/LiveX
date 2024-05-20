from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, response_types
from odin.adapters.parameter_tree import ParameterTreeError
from odin.util import decode_request_body

from livex.live_data.controller import LiveDataController

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
