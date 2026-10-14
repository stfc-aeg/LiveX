"""LiveX inference adapter.

This module implements a flexible endpoint to store data from model types that output data to be
displayed in a line graph (normalised or unbound axes), or a heatmap, in any combination.
Odin-data endpoints are used for control, results, and image collection for display.

Mika Shearwood, STFC Detector Systems Software Group
"""
from odin_control.adapters.adapter import ApiAdapter
from odin_control.adapters.adapter import ApiAdapter, ApiAdapterResponse, wants_metadata
from livex.inferencing.controller import InferencingController, LiveXError

class InferencingAdapter(ApiAdapter):

    controller_cls = InferencingController
    error_cls = LiveXError

    def get(self, path, request):
        """Base adapter get override ."""
        levels = [level for level in path.split('/') if level]
        if levels and levels[-1] == '_image':
            try:
                image = None
                # The expected path is like endpoint/<name>/results/<graph_name/results/_image
                # Only want to override it if we're sure
                if (
                    len(levels) >= 6
                    and levels[-4] == 'results'
                    and levels[-2] == 'results'
                ):
                    endpoint_name = levels[-5]
                    graph_name = levels[-3]
                    manager = self.controller.get_manager_by_name(endpoint_name)
                    if manager is not None:
                        image = manager.get_bitmap_image(graph_name)

                if image is None:
                    return ApiAdapterResponse(b"", content_type="text/plain", status_code=200)

                image_bytes, content_type = image
                return ApiAdapterResponse(
                    image_bytes, content_type=content_type, status_code=200
                )
            except self.error_cls as error:
                return ApiAdapterResponse(
                    {"error": str(error)}, content_type="application/json", status_code=400
                )

        try:
            response = self.controller.get(path, wants_metadata(request))
            return ApiAdapterResponse(
                response,
                content_type=request.headers.get("Accept", "application/json"),
                status_code=200,
            )
        except self.error_cls as error:
            response = {"error": str(error)}
            return ApiAdapterResponse(
                response, content_type="application/json", status_code=400
            )