
from livex.base_adapter import BaseAdapter
from livex.live_data.controller import LiveDataController, LiveXError

class LiveDataAdapter(BaseAdapter):

    controller_cls = LiveDataController
    error_cls = LiveXError
