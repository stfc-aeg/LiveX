from odin_control.adapters.adapter import ApiAdapter

from livex.trigger.controller import LiveXError, TriggerController

class TriggerAdapter(ApiAdapter):
    """Trigger adapter for the LiveX system server.
    
    This adapter implements control of the LiveX trigger device, with commands sent via
    modbus/pymodbus.
    """
    controller_cls = TriggerController
    error_cls = LiveXError
