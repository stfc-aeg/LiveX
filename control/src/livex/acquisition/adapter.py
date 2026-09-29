from odin_control.adapters.adapter import ApiAdapter
from livex.acquisition.controller import LiveXController, LiveXError

class LiveXAdapter(ApiAdapter):
    """Adapter for the LiveX Acquisition controller class."""
    controller_cls = LiveXController
    error_cls = LiveXError
