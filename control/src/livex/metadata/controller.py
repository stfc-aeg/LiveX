"""LiveX metadata controller.

This module implements the LiveX metadata controller class, which manages metadata for the LiveX
control system. Metadata fields are loaded from a configuration file and presented as parameters
for use in the system. Metadata can be written into HDF and markdown files for storage.

Tim Nicholls, STFC Detector Systems Software Group
"""

import json
import logging
from functools import partial
from typing import Any, Callable, Dict, Tuple

from livex.base_controller import BaseController
from livex.util import LiveXError
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from .hdf_writer import HdfMetadataWriter
from .markdown_writer import MarkdownMetaWriter
from .yaml_writer import YamlMetadataWriter
from .types import MetadataField, ParamDict


class MetadataController(BaseController):
    """MetadataController - controller class for LiveX metadata.

    This class implements the controller for the LiveX metadata adapter. It manages metadata fields,
    their state and output of metadata to YAML (with allowance of HDF and markdown) files.
    """

    def __init__(self, options):
        """Initialise the MetadataController object.

        This constructor initialises the state of the controller, loading metadata fields from a
        configuration file and building the parameter tree.

        :param option: dict of controller options
        """

        # Parse configuration options
        metadata_config = options.get("metadata_config", "metadata_config.json")
        metadata_store = options.get("metadata_store", None)
        self.markdown_template = options.get("markdown_template", "markdown.j2")

        # Initialise the state of the controller
        self.metadata_config = ""
        self.metadata_store = ""
        self.config_loaded = False
        self.config_error = ""
        self.metadata = {}

        self.hdf_path = "/tmp"
        self.hdf_file = "metadata.hdf5"
        self.hdf_group = "metadata"
        self.hdf_write = False

        self.markdown_path = "/tmp"
        self.markdown_file = "metadata.md"
        self.markdown_write = False

        self.yaml_path = "/tmp"
        self.yaml_file = "metadata.yaml"
        self.yaml_write = False

        # Build a default parameter tree
        self._build_tree()

        # If a persistent metadata store has been specified, configure the MetadataField dataclass
        # to use it
        if metadata_store:
            try:
                MetadataField.set_store(metadata_store)
                self.metadata_store = metadata_store
            except Exception as error:
                # shelve.open() exception types are poorly documented, catch all at this point
                error_msg = "Failed to open persistent store file {}: {}".format(
                    metadata_store, error
                )
                logging.error(error_msg)

        # Load the specified metadata configuration file
        self._load_config(metadata_config, raise_error=False)

    def initialize(self, adapters: ParamDict) -> None:
        """Initialize the controller.

        This method initializes the controller with information about the adapters loaded into the
        running application.

        :param adapters: dictionary of adapter instances
        """
        self.adapters = adapters
        if 'sequencer' in self.adapters:
            logging.debug("Metadata controller registering context with sequencer")
            self.adapters['sequencer'].add_context('metadata', self)

    def cleanup(self) -> None:
        """Clean up the controller.

        This method cleans up the state of the controller at shutdown, closing the persistent
        metadata store if open.
        """
        if self.metadata_store:
            MetadataField.close_store()

    def get(self, path: str, with_metadata: bool = False) -> ParamDict:
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

    def set(self, path: str, data: ParamDict) -> None:
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

        # If the HDF write parameter has been set, write metadata to an HDF file
        if self.hdf_write:
            self._write_hdf()

        # If the markdown write parameter has been set, write metadata to a markdown file
        if self.markdown_write:
            self._write_markdown()
        
        if self.yaml_write:
            self._write_yaml()

    def _load_config(self, metadata_config: str, raise_error: bool = True) -> None:
        """Load metadata configuration from a file.

        This method loads the metadata configuration from the specified file. Metadata fields are
        created from that configuration and the parameter tree rebuilt accordingly. Errors in this
        process normally raise an exception, but this can be supressed during initial loading to
        allow the state of the controller to be populated and initialisation.

        :param metadata_config: configuration file name
        :param raise_error: if an error occurs during configuration loading or parsing, raise it
        """

        def handle_config_error(error: str) -> None:
            """Handle configuration error

            This inner helper function handles errors during configuration loading. The error
            message is stored for access via the parameter tree, logged and, if configured, raised
            as an exception.

            :param error: error message
            """
            self.config_error = error
            logging.error(error)
            if raise_error:
                raise LiveXError(error)

        try:
            # Load the metadata fields from the JSON configuration file
            self.config_loaded = False
            with open(metadata_config, "r") as config_file:
                fields = json.load(config_file)

            # Build metadata fields from the parsed configuration
            self.metadata = {
                name: MetadataField(key=name, **field) for name, field in fields.items()
            }

            # Update the configuraiton state and parameter tree with the new fields
            self._build_tree()
            self.metadata_config = metadata_config
            self.config_loaded = True
            self.config_error = ""
            logging.info("Loaded metadata config from file %s", self.metadata_config)

        except FileNotFoundError as error:
            # Handle file errors during loading
            handle_config_error("Unable to load metadata parameter configuration: {}".format(error))

        except json.JSONDecodeError as error:
            # Handle JSON parsing errors
            handle_config_error(
                "Unable to parse metadata parameter configuration {}: {}".format(
                    self.metadata_config,
                    error,
                )
            )

        except TypeError as error:
            # Handle field generation errors
            handle_config_error("Failed to generate metadata fields: {}".format(error))

    def _build_tree(self) -> None:
        """Build the controller parameter tree.

        This method (re)builds the controller parameter tree. This is isolated from the init
        method to allow the tree to rebuilt if the metadata configuration is reloaded.
        """

        def _attr_accessor(attr_name: str) -> Tuple[Callable, Callable]:
            """Generate an attribute attribute accessor.

            This inner helper function generates a parameter accessor getter/setter pair for the
            specified attribute of the controller object.

            :param attr_name: attribute name
            """
            return (partial(getattr, self, attr_name), partial(setattr, self, attr_name))

        # Build the parameter tree
        self.param_tree = ParameterTree(
            {
                "metadata_config": (lambda: self.metadata_config, self._load_config),
                "config_loaded": (lambda: self.config_loaded, None),
                "config_error": (lambda: self.config_error, None),
                "metadata_store": (lambda: self.metadata_store, None),
                "hdf": {
                    "path": _attr_accessor("hdf_path"),
                    "file": _attr_accessor("hdf_file"),
                    "group": _attr_accessor("hdf_group"),
                    "write": _attr_accessor("hdf_write"),
                },
                "markdown": {
                    "path": _attr_accessor("markdown_path"),
                    "file": _attr_accessor("markdown_file"),
                    "write": _attr_accessor("markdown_write"),
                },
                "yaml": {
                    "path": _attr_accessor("yaml_path"),
                    "file": _attr_accessor("yaml_file"),
                    "write": _attr_accessor("yaml_write")
                },
                "fields": ParameterTree(
                    {
                        key: self.metadata[key].build_accessor()
                        for key, field in self.metadata.items()
                    }
                ),
            }
        )

    def _write_hdf(self) -> None:
        """Write metadata fields to an HDF file.

        This method writes metadata to an HDF file. The path and name of the file are obtained
        from the appropriate attributes mapped into the parameter tree of the controller.
        """
        self.hdf_write = False

        # Build a dict of the current metadata values
        metadata = {key: field.value for key, field in self.metadata.items()}

        with HdfMetadataWriter(self.hdf_path, self.hdf_file) as hdf5:
            hdf5.write(self.hdf_group, metadata)

    def _write_markdown(self) -> None:
        """Write metadata fields to a markdownfile.

        This method writes metadata to a markdown file. The path and name of the file are obtained
        from the appropriate attributes mapped into the parameter tree of the controller.
        """
        self.markdown_write = False

        # Build a dict of the current metadata values
        metadata = {key: field.value for key, field in self.metadata.items()}

        with MarkdownMetaWriter(
            self.markdown_template, self.markdown_path, self.markdown_file
        ) as markdown:
            markdown.write(metadata)

    def _write_yaml(self) -> None:
        """Write metadata fields to a YAML file.
        
        This method writes metadata to a YAML file. The path and name of the file are obtained from
        attributes mapped into the parameter tree of the controller.
        """
        self.yaml_write = False

        # Build a dict of the current metadata values
        metadata = {key: field.value for key, field in self.metadata.items()}

        with YamlMetadataWriter(self.yaml_path, self.yaml_file) as yaml:
            yaml.write(metadata)
