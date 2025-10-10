
from livex.base_adapter import BaseAdapter
from livex.live_data.controller import LiveDataController, LiveXError
from livex.base_adapter import ApiAdapterResponse

from odin.adapters.adapter import wants_metadata

class LiveDataAdapter(BaseAdapter):

    controller_cls = LiveDataController
    error_cls = LiveXError

    def get(self, path, request):
        """BaseAdapter get override to handle image processing."""
        try:
            levels = path.split('/')
            img_bytes = None
            # structure for intercept: _image/<name>/<image or histogram>
            if levels[0] == '_image':
                if levels[-1] == 'image':
                    img_bytes = self.controller.get_image_from_processor_name(levels[1], 'image')
                elif levels[-1] == 'histogram':
                    img_bytes = self.controller.get_image_from_processor_name(levels[1], 'histogram')

                if not img_bytes or not isinstance(img_bytes, (bytes, bytearray)):
                    return ApiAdapterResponse(b"", content_type="text/plain", status_code=200)

                response=img_bytes
                content_type="image/png"
            else:
                response = self.controller.get(path, wants_metadata(request))
                content_type="application/json"
            status_code = 200
        except self.error_cls as error:
            response = {"error":str(error)}
            content_type = "application/json"
            status_code = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)