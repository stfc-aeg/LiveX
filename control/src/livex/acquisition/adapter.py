from livex.base_adapter import BaseAdapter
from livex.acquisition.controller import LiveXController, LiveXError

class LiveXAdapter(BaseAdapter):

    controller_cls = LiveXController
    error_cls = LiveXError
