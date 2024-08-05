import logging

from livex.metadata.controller import LiveXError, MetadataController
from odin.adapters.adapter import (
    ApiAdapter,
    ApiAdapterResponse,
    request_types,
    response_types,
)
from tornado.escape import json_decode


class MetadataAdapter(ApiAdapter):
    """Metadata adapter class."""

    def __init__(self, **kwargs):
        """Initialise MetadataAdapter object."""

        super(MetadataAdapter, self).__init__(**kwargs)

        # Parse options
        metadata_config = self.options.get("metadata_config", "metadata_config.json")
        metadata_store = self.options.get("metadata_store", None)
        markdown_template = self.options.get("markdown_template", "markdown.j2")

        # Create metadata controller
        self.controller = MetadataController(
            metadata_config, metadata_store, markdown_template
        )

    @response_types("application/json", default="application/json")
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.controller.get(path)
            status_code = 200
        except LiveXError as error:
            response = {"error": str(error)}
            status_code = 400

        content_type = "application/json"

        return ApiAdapterResponse(
            response, content_type=content_type, status_code=status_code
        )

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
            response = {
                "error": "Failed to decode PUT request body: {}".format(str(error))
            }
            status_code = 400

        return ApiAdapterResponse(
            response, content_type=content_type, status_code=status_code
        )

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = "LiveXAdapter: DELETE on path {}".format(path)
        status_code = 200

        return ApiAdapterResponse(response, status_code=status_code)

    def initialize(self, adapters):
        """Get list of adapters and call relevant functions for them."""
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)

        self.controller.initialise(self.adapters)

    def cleanup(self):
        """Clean up adapter state at shutdown.

        This method cleans up the adapter state when called by the server at e.g. shutdown.
        It simplied calls the cleanup function of the LiveX instance.
        """
        self.controller.cleanup()
