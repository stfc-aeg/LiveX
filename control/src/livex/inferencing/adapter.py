"""LiveX inference adapter.

This module implements a flexible endpoint to store data from model types that output data to be
displayed in a line graph (normalised or unbound axes), or a heatmap, in any combination.
Odin-data endpoints are used for control, results, and image collection for display.

Mika Shearwood, STFC Detector Systems Software Group
"""
from odin_control.adapters.adapter import ApiAdapter
from livex.inferencing.controller import InferencingController, LiveXError

class InferencingAdapter(ApiAdapter):

    controller_cls = InferencingController
    error_cls = LiveXError

