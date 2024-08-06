"""LiveX metadata adapter.

This module implements a metadata adapter for the LiveX control system. The adapter provides an
interface to configurable metadata fields, their values and the ability to log them into various
file formats.

Tim Nicholls, STFC Detector Systems Software Group
"""

import logging

from livex.metadata.controller import LiveXError, MetadataController
from odin.adapters.adapter import (
    ApiAdapter,
    ApiAdapterResponse,
    request_types,
    response_types,
    wants_metadata,
)
from tornado.escape import json_decode


class MetadataAdapter(ApiAdapter):
    """Metadata adapter for the LiveX system.

    This class implements the LiveX metadata adapter, providing an interface beween odin-control
    HTTP requests and the underlying metadata controller object
    """

    def __init__(self, **kwargs):
        """Initialise the MetadataAdapter object.

        This method initialises the adapter object, resolving configuration options passed from
        odin-control and instantiating a controller object.

        :param kwargs: keyword arguments specifying options
        """

        super(MetadataAdapter, self).__init__(**kwargs)

        # Parse configuration options
        metadata_config = self.options.get("metadata_config", "metadata_config.json")
        metadata_store = self.options.get("metadata_store", None)
        markdown_template = self.options.get("markdown_template", "markdown.j2")

        # Instantiate the controller object
        self.controller = MetadataController(metadata_config, metadata_store, markdown_template)
        logging.debug("MetaDataAdapter loaded")

    def initialize(self, adapters):
        """Initialize the adapter.

        This method is called by odin-control once all adapters are loaded. The dictionary of loaded
        adapters are passed to the initalize method of the controller.

        :param adapters: dictionary of adapters loaded into the odin-control instance
        """
        logging.debug("MetadataAdapter initialize called with %d adapters", len(adapters))
        adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        self.controller.initialise(adapters)

    def cleanup(self):
        """Clean up the adapter.

        This method is called by odin-control at shutdown. The corresponding method in the
        controller is called to clean up the state of the adapter.
        """
        logging.debug("MetadataAdapter cleanup called")
        self.controller.cleanup()

    @response_types("application/json", default="application/json")
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.controller.get(path, wants_metadata(request))
            status_code = 200
        except LiveXError as error:
            response = {"error": str(error)}
            status_code = 400

        content_type = "application/json"

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types("application/json")
    @response_types("application/json", default="application/json")
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """

        content_type = "application/json"

        try:
            data = json_decode(request.body)
            self.controller.set(path, data)
            response = self.controller.get(path)
            status_code = 200
        except LiveXError as error:
            response = {"error": str(error)}
            status_code = 400
        except (TypeError, ValueError) as error:
            response = {"error": "Failed to decode PUT request body: {}".format(str(error))}
            status_code = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)
