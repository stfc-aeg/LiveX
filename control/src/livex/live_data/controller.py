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
                    "size_x": (lambda proc=proc: self.processors[i].size_x,
                               partial(self.set_img_x, processor=proc)),
                    "size_y": (lambda: self.processors[i].size_y,
                               partial(self.set_img_y, processor=proc)),
                    "dimensions": (lambda: self.processors[i].dimensions, partial(self.set_img_dims, processor=proc)),
                    "colour": (lambda: self.processors[i].colour, 
                               partial(self.set_img_colour, processor=proc)),
                    "data": (lambda: proc.get_image(), None)
                    # Use get_image in processor for JSON serialisation
                }
            }
            self.tree['liveview'].append(tree)

        self.param_tree = ParameterTree(self.tree)

    def update_render_info(self, processor):
        """Pipe updated parameters to processor thread.
        :param processor: LiveDataProcessor object to reference.
        """
        # Could be done programmatically but not enough to warrant this complexity
        params = {
            "dimensions": processor.dimensions,
            "size_x": processor.size_x,
            "size_y": processor.size_y,
            "colour": processor.colour
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
