"""YAML metadata writer.

This module implements a YAML metadata writer class, which injects metadata fields into a YAML
file. The class implements the context manager pattern for ease of use.

Mika Shearwood, STFC Detector Systems Software Group
"""

import logging
import os
from typing import Any, Dict

import yaml
from livex.util import LiveXError

class YamlSequencerWriter:
    """YAML sequencer logging writer class.

    This class implements a YAML filewriter as a context manager. Output from the sequencer are 
    written to the given path and file.
    """

    def __init__(self, file_path: str, file_name: str):
        """Initialise the YAML sequencer writer object.

        This method initialises the writer object, storing the path and name.
        No file mode is provided, the class reads any existing file when you make it and overwrites
        if you call the write function while open.
        :param file_path: path of YAML file
        :param file_name: name of YAML file
        """
        self.file_path = file_path
        self.file_name = file_name

        self.full_path = os.path.join(file_path, file_name)

        self.data = {}

    def __enter__(self):
        """Enter the context manager.
        
        This method implements the context manager entry point. The path to the file is created
        if absent, then the file opened.
        If there is an existing file by that name, the name is amended with a `_X` where X is the
        number of other files with matching names.
        """
        try:
            os.makedirs(self.file_path, exist_ok=True)

            base_name, ext = os.path.splitext(self.file_name)
            hopeful_path = self.full_path
            counter = 1

            while os.path.exists(hopeful_path):
                new_name = f"{base_name}_{counter}{ext}"  # Append an incrementing counter
                hopeful_path = os.path.join(self.file_path, new_name)
                counter += 1

            self.full_path = hopeful_path
            self.data = {}

            if counter > 1:  # Did we have a namespace collision
                logging.debug(
                    f"Namespace collision: Sequencer YAML will be written to: {self.full_path}"
                )


        except (OSError, IOError) as error:
            error_msg = f"Failed to create YAML Sequencer writer: {error}"
            logging.error(error_msg)
            raise LiveXError(error_msg)
        
        return self
        
    def __exit__(self, exc_type: Any, exc_value: Any, exc_tb: Any) -> None:
        """Exit the context manager.
        
        This method implements the context manager exit point. Any exceptions that occurred during
        writing are logged and raised.
        """
        if exc_value:
            error_msg = f"Error during YAML Sequencer writing: {exc_type.__name__}: {exc_value}"
            logging.error(error_msg)
            raise LiveXError(error_msg)
        
        try:
            with open(self.full_path, "w") as f:
                yaml.safe_dump(self.data, f, sort_keys=False)

        except (OSError, IOError) as error:
            error_msg = f"Failed to write YAML Sequencer Log: {error}"
            logging.error(error_msg)
            raise LiveXError(error_msg)

    def write(self, data: Dict) -> None:
        """Write sequencer logging output to the file.
        
        This method writes the data to the class data attribute to be written on context exit.
        :param data: dict of logging fields to write into file
        """
        self.data.update(data)
        logging.debug(f"Wrote logging output to YAML file {self.full_path}")
