"""Markdown metadata writer.

This module implements a markdown metadata writer class, which writes metadata fields into an
markdown file using a specified template. The class implements the context manager pattern for ease
of use.

Tim Nicholls, STFC Detector Systems Software Group
"""

import logging
import os
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from livex.util import LiveXError


class MarkdownMetaWriter:
    """Markdown metadata writer class.

    This class implements a markdown metadata writer as a context manager. Metadata are written to
    the specified path and file, formatted using the specified Jinja2 template file.

    """

    def __init__(self, template_file: str, file_path: str, file_name: str, mode: str = "w"):
        """Intialise the markdown metadata writer object.

        This method initialises the writer object, storing the specified template file name,
        markdown file path, name and mode.

        :param template_file : name of a Jinja2 template file
        :param file_path : path of the markdown file
        :param file_name : name of the markdown file
        :param file_mode : mode to open the markdown file with
        """
        # Store the path, name and mode in the object
        self.file_path = file_path
        self.file_name = file_name
        self.mode = mode

        # Construct the full file path
        self.full_path = os.path.join(file_path, file_name)

        # Resolve the template directory and file name as required by the Jinja2 loader
        self.template_dir = os.path.dirname(template_file)
        self.template_file = os.path.basename(template_file)

    def __enter__(self):
        """Enter the context manager.

        This method implements the context manager entry point. The path to the specified file is
        created if absent, then the markdown file opened. A Jinja2 environment and template are
        created as required. Exceptions are logged and raised as a LiveX error.
        """
        try:
            # Ensure the path to the markdown file exists
            os.makedirs(self.file_path, exist_ok=True)

            # Open the markdown output file
            self.file = open(self.full_path, self.mode)

        except (OSError, IOError) as error:
            error_msg = "Failed to write markdown metadata: {}".format(str(error))
            logging.error(error_msg)
            raise LiveXError(error_msg)

        try:
            # Create the Jinja2 environment and template instances
            self.env = Environment(loader=FileSystemLoader(self.template_dir))
            self.template = self.env.get_template(self.template_file)
        except TemplateNotFound as error:
            raise LiveXError("Markdown template {} not found".format(str(error)))

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, exc_tb: Any) -> None:
        """Exit the context manager.

        This method implements the context manager exit point. The file is closed if open and any
        exceptions that occurred curing writing logged and raised appropriately.
        """
        if self.file:
            self.file.close()

        if exc_value:
            error_msg = "Error during markdown metadata writing: {}: {}".format(
                exc_type.__name__, exc_value
            )
            logging.error(error_msg)
            raise LiveXError(error_msg)

    def write(self, metadata: Dict) -> None:
        """Write metadata to the file.

        This method writes the specified metadata to the file, rendering the template with the
        specified metadata fields.

        :param metadata: dictionary of metadata fields to write into file
        """
        content = self.template.render(metadata)
        self.file.write(content)

        logging.debug("Wrote metadata to markdown file %s", self.full_path)
