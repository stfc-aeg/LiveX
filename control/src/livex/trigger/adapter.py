from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, response_types
from odin.adapters.parameter_tree import ParameterTreeError
from odin.util import decode_request_body
import logging

from livex.trigger.trigger_controller import TriggerController

class TriggerAdapter(ApiAdapter):
    """Trigger adapter for the ODIN server.
    
    This adapter provides ODIN clients with access to parameters to adjust settings on the
    trigger device, with commands sent via modbus/pymodbus.
    """
    def __init__(self, **kwargs):
        """Initialise the TriggerAdapter object.
        :param kwargs: keyword arguments specifying options.
        """
        super(TriggerAdapter, self).__init__(**kwargs)

        ip = self.options.get('ip', None)

        frequencies = {
            'furnace': int(self.options.get('furnace_frequency', 50)),
            'wideFov': int(self.options.get('wideFov_frequency', 80)),
            'narrowFov': int(self.options.get('narrowFov_frequency', 120))
        }

        status_bg_task_enable = int(self.options.get('status_bg_task_enable', 1))
        status_bg_task_interval = int(self.options.get('status_bg_task_interval', 10))

        self.trigger = TriggerController(ip, frequencies, status_bg_task_enable, status_bg_task_interval)

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        try:
            response = self.trigger.get(path)
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
            self.trigger.set(path, data)
            response = self.trigger.get(path)
            content_type = "applicaiton/json"
            status = 200

        except ParameterTreeError as param_error:
            response = {'response': 'LiveViewAdapter PUT error: {}'.format(param_error)}
            content_type = 'application/json'
            status = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status)

    def cleanup(self):
        self.trigger.cleanup()