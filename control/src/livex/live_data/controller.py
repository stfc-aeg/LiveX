import logging
from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from livex.base_controller import BaseController
from livex.util import LiveXError
from livex.live_data.processor import LiveDataProcessor

class LiveDataController(BaseController):
    """Class to instantiate and manage the ParameterTree for LiveDataProcessor classes."""

    def __init__(self, options): # endpoints, names, resolutions):
        """Initialise the LiveDataController. Create a LiveDataProcessor for each endpoint
        provided in config, then create a ParameterTree to handle behaviours for those classes.
        :param endpoints: list of endpoints in string format.
        """
        logging.debug("Initialising LiveDataController.")

        # Split on comma, remove whitespace if it exists
        endpoints = [
            item.strip() for item in options.get('livedata_endpoint', None).split(",")
        ]
        names = [
            item.strip() for item in options.get('endpoint_name', None).split(",")
        ]
        # Array of dicts of resolutions
        resolutions = [
            {'x': int(width), 'y': int(height)}  # generate x/y dict
            for resolution in options.get('camera_resolution', '4096x2304').split(',') # get resolutions
            for width, height in [resolution.strip().split("x")] # each resolution split into array
        ]        

        self.tree = {
            "liveview": {}
        }

        self.processors = []

        # For each provided endpoint
        for i in range(len(endpoints)):
            name = names[i]
            resolution = resolutions[i]
            self.processors.append(
                LiveDataProcessor(endpoints[i], resolution)
            )

            proc = self.processors[i]

            # Create 'branch' of ParameterTree for each Processor
            tree = {
                "name": (lambda: name, None),
                "endpoint": (lambda proc=proc: proc.endpoint, None),
                "image":
                {  # Partials provide processor as an argument
                    # Unclear if `proc=proc` is definitely required but it is not intrusive
                    "size_x": (lambda proc=proc: proc.size_x,
                               partial(self.set_img_x, processor=proc)),
                    "size_y": (lambda proc=proc: proc.size_y,
                               partial(self.set_img_y, processor=proc)),
                    "dimensions": (lambda proc=proc: proc.out_dimensions,
                                   partial(self.set_img_dims, processor=proc)),
                    "resolution": (lambda proc=proc: proc.resolution_percent,
                                   partial(self.set_resolution, processor=proc)),
                    "colour": (lambda proc=proc: proc.colour,
                               partial(self.set_img_colour, processor=proc)),
                    "data": (lambda proc=proc: proc.get_image(), None),
                    # Use get_image in processor for JSON serialisation
                    "clip_range_value": (lambda proc=proc: [proc.clipping['min'], proc.clipping['max']],
                                   partial(self.set_img_clip_value, processor=proc)),
                    "clip_range_percent": (lambda proc=proc: [proc.clipping['percent']['min'], proc.clipping['percent']['max']],
                                        partial(self.set_img_clip_percent, processor=proc)),
                    "roi": (lambda proc=proc: [
                        proc.roi['x_lower'], proc.roi['x_upper'], proc.roi['y_lower'], proc.roi['y_upper']],
                        partial(self.set_roi_boundaries, processor=proc)),
                    "histogram": (lambda proc=proc: proc.get_histogram(), None)
                }
            }
            self.tree['liveview'][name] = tree

        self.param_tree = ParameterTree(self.tree)

    def initialize(self, adapters):
        """Initialize the controller.

        This method initializes the controller with information about the adapters loaded into the
        running application.

        :param adapters: dictionary of adapter instances
        """
        self.adapters = adapters
        if 'sequencer' in self.adapters:
            logging.debug("Live data controller registering context with sequencer")
            self.adapters['sequencer'].add_context('livedata', self)

    def cleanup(self):
        """Clean up the LiveDataController instance.

        This method terminates processors, allowing shutdown.
        """
        logging.debug(f"Terminating {len(self.processors)} processes.")
        for processer in self.processors:
            processer.process.terminate()


    def get(self, path, with_metadata=False):
        """Get parameter data from controller.

        This method gets data from the controller parameter tree.

        :param path: path to retrieve from the tree
        :param with_metadata: flag indicating if parameter metadata should be included
        :return: dictionary of parameters (and optional metadata) for specified path
        """
        try:
            return self.param_tree.get(path, with_metadata)
        except ParameterTreeError as error:
            logging.error(error)
            raise LiveXError(error)

    def set(self, path, data):
        """Set parameters in the controller.

        This method sets parameters in the controller parameter tree. If the parameters to write
        metadata to HDF and/or markdown have been set during the call, the appropriate write
        action is executed.

        :param path: path to set parameters at
        :param data: dictionary of parameters to set
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as error:
            logging.error(error)
            raise LiveXError(error)

    def update_render_info(self, processor):
        """Pipe updated parameters to processor thread.
        :param processor: LiveDataProcessor object to reference.
        """
        # Could be done programmatically but not enough to warrant this complexity
        params = {
            "dimensions": processor.out_dimensions,
            "size_x": processor.size_x,
            "size_y": processor.size_y,
            "colour": processor.colour,
            "clipping": processor.clipping,
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

        self.update_render_info(processor)

    def set_img_colour(self, value, processor):
        """Set the colour of the image in the parameter tree, used to determine the colour map.
        :param value: colour map name as a string. see get_colour_map
        :param processor: LiveDataProcessor object to reference
        """
        processor.colour = str(value)
        self.update_render_info(processor)

    def scale_percent_to_selection(self, new_percentages, current_percentages):
        """Scale selected percentages to fit an existing selection.
        e.g.: specifying a further region of interest within an already-specified one.
        :param new_percentages: array of upper and lower boundaries selected. [min, max]
        :param current_percentages: array of current boundaries. [min, max]
        :return: new minimum and maximum boundaries.
        """
        select_min = min(new_percentages)
        select_max = max(new_percentages)
        cur_min = min(current_percentages)
        cur_max = max(current_percentages)

        # Current percentage selected expressed as a value between 0 and 1
        scalar = (cur_max - cur_min) / 100

        # Min and max values are scaled to the currently-selected range, and added to boundaries.
        new_min = cur_min + select_min*scalar
        new_max = cur_max - ((100-select_max)*scalar)

        return new_min, new_max

    def set_img_clip_value(self, value, processor):
        """Set the image clipping range absolutely.
        :param value: array of clip range limits, min to max
        :param processor: LiveDataProcessor object
        """
        processor.clipping['min'] = int(value[0])
        processor.clipping['max'] = int(value[1])

        processor.clipping['percent']['min'] = (int(value[0]) / processor.cam_pixel_max) * 100
        processor.clipping['percent']['max'] = (int(value[1]) / processor.cam_pixel_max) * 100
        
        # Round for readability
        processor.clipping['percent']['min'] = round(processor.clipping['percent']['min'], 2)
        processor.clipping['percent']['max'] = round(processor.clipping['percent']['max'], 2)

        self.update_render_info(processor)

    def set_img_clip_percent(self, value, processor):
        """Set the image clipping range proportionally.
        :param value: array of clip range limits. This is provided by a clickableimage component
        so it takes the form [[xmin, xmax], [ymin, ymax]]. Here, y is irrelevant.
        :param processor: LiveDataProcessor object
        """
        select_min = value[0][0]
        select_max = value[0][1]
        cur_min = processor.clipping['percent']['min']
        cur_max = processor.clipping['percent']['max']

        new_min, new_max = self.scale_percent_to_selection(
            [select_min, select_max],
            [cur_min, cur_max]
        )

        processor.clipping['percent']['min'] = new_min
        processor.clipping['percent']['max'] = new_max

        # percentage/100 * max = 0->1 multiplier of range
        processor.clipping['min'] = int(processor.clipping['percent']['min']/100 * processor.cam_pixel_max)
        processor.clipping['max'] = int(processor.clipping['percent']['max']/100 * processor.cam_pixel_max)

        self.update_render_info(processor)

    def set_resolution(self, value, processor):
        """Set the resolution of the image.
        :param value: Resolution expressed as a percentage.
        :param processor: LiveDataProcessor object
        """
        value = int(value)
        processor.resolution = value
        new_x = int(processor.max_size_x*(value/100))
        new_y = int(processor.max_size_y*(value/100))
        self.set_img_dims([new_x, new_y], processor)

    def set_roi_boundaries(self, value, processor):
        """Set the region of interest boundaries for the image.
        Has an override - giving 0 and 100 as both x and y boundaries resets to full size.
        :param value: array of RoI boundaries in %. [[x_low, x_high], [y_low, y_high]].
        :param processor: LiveData Processor object.
        """
        x_low, x_high = value[0]
        y_low, y_high = value[1]

        img_x = processor.size_x
        img_y = processor.size_y

        # If provided value is full image size, we don't care about existing ROI, to allow reset.
        value_is_reset = (
            x_low == 0 and x_high == 100 and
            y_low == 0 and y_high == 100
        )
        if value_is_reset:  # Pretend we're picking from full image. End value will be full size
            cur_x_low = 0
            cur_x_high = 100
            cur_y_low = 0
            cur_y_high = 100
        else:  # If not reset, get real current value
            cur_x_low = processor.roi['percent']['x_lower']
            cur_x_high = processor.roi['percent']['x_upper']
            cur_y_low = processor.roi['percent']['y_lower']
            cur_y_high = processor.roi['percent']['y_upper']

        new_x_low, new_x_high = self.scale_percent_to_selection(
            [x_low, x_high],
            [cur_x_low, cur_x_high]
        )
        new_y_low, new_y_high = self.scale_percent_to_selection(
            [y_low, y_high],
            [cur_y_low, cur_y_high]
        )

        # New pixel value is max_size * (%/100)
        processor.roi['x_lower'] = int(img_x * (new_x_low/100))
        processor.roi['x_upper'] = int(img_x * (new_x_high/100))
        processor.roi['y_lower'] = int(img_y * (new_y_low/100))
        processor.roi['y_upper'] = int(img_y * (new_y_high/100))
        # Set percentage to new percentage
        processor.roi['percent']['x_lower'] = new_x_low
        processor.roi['percent']['x_upper'] = new_x_high
        processor.roi['percent']['y_lower'] = new_y_low
        processor.roi['percent']['y_upper'] = new_y_high

        self.update_render_info(processor)
