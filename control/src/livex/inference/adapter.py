"""LiveX inference adapter.

At present, this module implements a few basic values to show that live inferencing has merit.

Mika Shearwood, STFC Detector Systems Software Group
"""
from odin_control.adapters.adapter import ApiAdapter
from livex.inference.controller import InferenceController, LiveXError

class InferenceAdapter(ApiAdapter):

    controller_cls = InferenceController
    error_cls = LiveXError

