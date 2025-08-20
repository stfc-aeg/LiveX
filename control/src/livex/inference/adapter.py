"""LiveX inference adapter.

At present, this module implements a few basic values to show that live inferencing has merit.

Mika Shearwood, STFC Detector Systems Software Group
"""
from livex.base_adapter import BaseAdapter
from livex.inference.controller import InferenceController, LiveXError

class InferenceAdapter(BaseAdapter):

    controller_cls = InferenceController
    error_cls = LiveXError

