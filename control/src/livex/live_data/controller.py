import logging
from functools import partial

from odin.adapters.parameter_tree import ParameterTree

from livex.live_data.processor import LiveDataProcessor

class LiveDataController():
    """Class to instantiate and manage the ParameterTree for LiveDataProcessor classes."""

    def __init__(self, endpoints):
        """Initialise the LiveDataController. Create a LiveDataProcessor for each endpoint
        provided in config, then create a ParameterTree to handle behaviours for those classes.
        :param endpoints: list of endpoints in string format.
        """
        logging.debug("Initialising LiveDataController.")

        self.processors = []
        self.tree = {
            "liveview": []
        }

        # For each provided endpoint
        for i in range(len(endpoints)):
            self.processors.append(
                LiveDataProcessor(endpoints[i])
            )

            proc = self.processors[i]

            # Create 'branch' of ParameterTree for each Processor
            tree = {
                "endpoint": (lambda: self.processors[i].endpoint, None),
                "image":
                {  # Partials provide processor as an argument
                    # Unclear if `proc=proc` is definitely required but it is not intrusive
                    "size_x": (lambda proc=proc: proc.size_x,
                               partial(self.set_img_x, processor=proc)),
                    "size_y": (lambda proc=proc: proc.size_y,
                               partial(self.set_img_y, processor=proc)),
                    "dimensions": (lambda proc=proc: proc.dimensions, partial(self.set_img_dims, processor=proc)),
                    "resolution": (lambda proc=proc: proc.resolution,
                                   partial(self.set_resolution, processor=proc)),
                    "colour": (lambda proc=proc: proc.colour, 
                               partial(self.set_img_colour, processor=proc)),
                    "data": (lambda proc=proc: proc.get_image(), None),
                    # Use get_image in processor for JSON serialisation
                    "clip_range": (lambda proc=proc: [proc.clip_min, proc.clip_max],
                                   partial(self.set_img_clip, processor=proc)),
                    "roi": (lambda proc=proc: [
                        proc.roi['x_lower'], proc.roi['x_upper'], proc.roi['y_lower'], proc.roi['y_upper']],
                        partial(self.set_roi_boundaries, processor=proc))
                }
            }
            self.tree['liveview'].append(tree)

        self.param_tree = ParameterTree(self.tree)

    def set_img_clip(self, value, processor):
        """Set the image clipping range.
        :param value: array of clip range limits, min to max
        :param processor: LiveDataProcessor object
        """
        processor.clip_min = int(value[0])
        processor.clip_max = int(value[1])
        self.update_render_info(processor)

    def set_resolution(self, value, processor):
        """Set the resolution of the image.
        :param value: Resolution expressed as a percentage.
        :param processor: LiveDataProcessor object
        """
        value = int(value)
        processor.resolution = value
        processor.size_x = int(processor.max_size_x*(value/100))
        processor.size_y = int(processor.max_size_y*(value/100))
        self.update_render_info(processor)

    def set_roi_boundaries(self, value, processor):
        """Set the region of interest boundaries for the image.
        :param value: array of RoI boundaries, expressed in %. [[x_low, x_high], [y_low, y_high]]
        :param processor: LiveDataProcessor object
        """
        x_low, x_high = value[0]
        y_low, y_high = value[1]

        img_x = processor.size_x
        img_y = processor.size_y

        # Translate Array to Relative Dimensions/Image Size
        processor.roi['x_lower'] = int(x_low)
        processor.roi['x_upper'] = int(x_high)
        processor.roi['y_lower'] = int(y_low)
        processor.roi['y_upper'] = int(y_high)

        # Percentage of image selected is boundary/size * 100
        processor.roi['percent']['x_lower'] = int((x_low/img_x) * 100)
        processor.roi['percent']['x_upper'] = int((x_high/img_x) * 100)
        processor.roi['percent']['y_lower'] = int((y_low/img_y) * 100)
        processor.roi['percent']['y_upper'] = int((y_high/img_y) * 100)

        logging.debug(f"roi: {processor.roi}")

        self.update_render_info(processor)

    def update_render_info(self, processor):
        """Pipe updated parameters to processor thread.
        :param processor: LiveDataProcessor object to reference.
        """
        # Could be done programmatically but not enough to warrant this complexity
        params = {
            "dimensions": processor.dimensions,
            "size_x": processor.size_x,
            "size_y": processor.size_y,
            "colour": processor.colour,
            "clip_min": processor.clip_min,
            "clip_max": processor.clip_max,
            "roi": processor.roi
        }
        processor.pipe_parent.send(params)

    def set_img_x(self, value, processor):
        """Set the width of the image in pixels.
        :param value: integer representing number of pixels.
        :param processor: LiveDataProcessor object to reference
        """
        processor.size_x = int(value)
        self.update_render_info(processor)

    def set_img_y(self, value, processor):
        """Set the height of the image in pixels.
        :param value: integer representing number of pixels.
        :param processor: LiveDataProcessor object to reference
        """
        processor.size_y = int(value)
        self.update_render_info(processor)

    def set_img_dims(self, value, processor):
        """Set both image dimensions, width and height (x and y).
        :param value: array of integers representing width/height in pixels.
        :param processor: LiveDataProcessor object to reference.
        """
        processor.dimensions = value
        processor.size_x = int(processor.dimensions[0])
        processor.size_y = int(processor.dimensions[1])

        # Update region of interest values for new resolution
        processor.roi['x_lower'] = int(
            (processor.roi['percent']['x_lower'] / 100) * processor.size_x)
        processor.roi['x_upper'] = int(
            (processor.roi['percent']['x_upper'] / 100) * processor.size_x)
        processor.roi['y_lower'] = int(
            (processor.roi['percent']['y_lower'] / 100) * processor.size_y)
        processor.roi['y_upper'] = int(
            (processor.roi['percent']['y_upper'] / 100) * processor.size_y)
        
        logging.debug(f"roi: {processor.roi}")

        self.update_render_info(processor)

    def set_img_colour(self, value, processor):
        """Set the colour of the image in the parameter tree, used to determine the colour map.
        :param value: colour map name as a string. see get_colour_map
        :param processor: LiveDataProcessor object to reference
        """
        processor.colour = str(value)
        self.update_render_info(processor)

    def get(self, path):
        """Get attribute from parameter tree."""
        # logging.debug(self.param_tree)
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set attribute in parameter tree."""
        self.param_tree.set(path, data)

    def cleanup(self):
        """Clean up the LiveDataController instance.
        This method terminates thread processes, allowing shutdown.
        """
        logging.debug(f"Terminating {len(self.processors)} processes.")
        for processer in self.processors:
            processer.process.terminate()
