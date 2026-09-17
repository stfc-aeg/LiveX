"""Basic adapter for LiveX control

This class implements a simple adapter which reads values from the Modbus server and stores them
in the parameter tree for web interface access.
The web interface sends data to the adapter which translates this into Modbus commands
to be read by the PLC.

Mika Shearwood, Detector Systems Software Group
"""

from odin_control.adapters.adapter import ApiAdapter
from livex.furnace.controller import FurnaceController, LiveXError

class FurnaceAdapter(ApiAdapter):

    controller_cls = FurnaceController
    error_cls = LiveXError
