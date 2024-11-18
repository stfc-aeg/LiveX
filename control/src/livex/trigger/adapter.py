from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, response_types, request_types
from odin.adapters.parameter_tree import ParameterTreeError
from odin.util import decode_request_body

from livex.base_adapter import BaseAdapter
from livex.trigger.controller import LiveXError, TriggerController

class TriggerAdapter(BaseAdapter):
    """Trigger adapter for the LiveX system server.
    
    This adapter implements control of the LiveX trigger device, with commands sent via
    modbus/pymodbus.
    """
    controller_cls = TriggerController
    error_cls = LiveXError
