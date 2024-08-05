import json
import logging
from functools import partial

from livex.util import LiveXError
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from .field import MetadataField
from .hdf_writer import HdfMetadataWriter
from .markdown_writer import MarkdownMetaWriter


class MetadataController:
    """MetadataController - class that manages the other adapters for LiveX."""

    def __init__(
        self, metadata_config, metadata_store=None, markdown_template="markdown.j2"
    ):
        """Initialise the MetadataController object.

        This constructor initialises the MetadataController, building the parameter tree and getting
        system info.
        """

        # Initialise the state of the controller and parameter tree
        self.metadata_config = ""
        self.metadata_store = ""
        self.config_loaded = False
        self.config_error = ""
        self.metadata = {}

        self.hdf_path = "/tmp"
        self.hdf_file = "metadata.hdf5"
        self.hdf_group = "metadata"
        self.hdf_write = False

        self.markdown_template = markdown_template
        self.markdown_path = "/tmp"
        self.markdown_file = "metadata.md"
        self.markdown_write = False

        self._build_tree()

        # If a persistent metadata store has been specified, configure the MetadataField dataclass
        # to use it
        if metadata_store:
            MetadataField.set_store(metadata_store)
            self.metadata_store = metadata_store

        # Load the specified metadata configuration file
        self._load_config(metadata_config, raise_error=False)

    def initialise(self, adapters):
        """Get access to all of the other adapters.
        :param adapters: dict of adapters from adapter.py.
        """
        self.adapters = adapters

    def cleanup(self):
        if self.metadata_store:
            MetadataField.close_store()

    def get(self, path):
        """Get the parameter tree.
        This method returns the parameter tree for use by clients via the FurnaceController adapter.
        :param path: path to retrieve from tree
        """
        try:
            return self.param_tree.get(path)
        except ParameterTreeError as error:
            raise LiveXError(error)

    def set(self, path, data):
        """Set parameters in the parameter tree.
        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate LiveXError.
        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise LiveXError(e)

        if self.hdf_write:
            self._write_hdf()

        if self.markdown_write:
            self._write_markdown()

    def _load_config(self, metadata_config, raise_error=True):

        def handle_config_error(error):
            self.config_error = error
            logging.error(error)
            if raise_error:
                raise LiveXError(error)

        try:
            self.config_loaded = False
            with open(metadata_config, "r") as config_file:
                fields = json.load(config_file)

            self.metadata = {
                name: MetadataField(key=name, **field) for name, field in fields.items()
            }

            self._build_tree()
            self.metadata_config = metadata_config
            self.config_loaded = True
            self.config_error = ""
            logging.info("Loaded metadata config from file %s", self.metadata_config)

        except FileNotFoundError as error:
            handle_config_error(
                "Unable to load metadata parameter configuration: {}".format(error)
            )

        except json.JSONDecodeError as error:
            handle_config_error(
                "Unable to parse metadata parameter configuration {}: {}".format(
                    self.metadata_config,
                    error,
                )
            )

        except TypeError as error:
            handle_config_error("Failed to generate metadata fields: {}".format(error))

    def _build_tree(self):

        def _attr_accessor(param):
            return (partial(getattr, self, param), partial(setattr, self, param))

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
                "fields": ParameterTree(
                    {
                        key: self.metadata[key].build_accessor()
                        for key, field in self.metadata.items()
                    }
                ),
            }
        )

    def _write_hdf(self):

        self.hdf_write = False

        # Build a dict of the current metadata values
        metadata = {key: field.value for key, field in self.metadata.items()}

        with HdfMetadataWriter(self.hdf_path, self.hdf_file) as hdf5:
            hdf5.write(self.hdf_group, metadata)

    def _write_markdown(self):

        self.markdown_write = False

        # Build a dict of the current metadata values
        metadata = {key: field.value for key, field in self.metadata.items()}

        with MarkdownMetaWriter(
            self.markdown_template, self.markdown_path, self.markdown_file
        ) as markdown:
            markdown.write(metadata)
