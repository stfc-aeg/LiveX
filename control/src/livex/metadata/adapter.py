"""LiveX metadata adapter.

This module implements a metadata adapter for the LiveX control system. The adapter provides an
interface to configurable metadata fields, their values and the ability to log them into various
file formats.

Tim Nicholls, STFC Detector Systems Software Group
"""

from livex.base_adapter import BaseAdapter
from livex.metadata.controller import LiveXError, MetadataController


class MetadataAdapter(BaseAdapter):

    controller_cls = MetadataController
    error_cls = LiveXError

