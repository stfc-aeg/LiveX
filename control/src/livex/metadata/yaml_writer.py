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

class YamlMetadataWriter:
    """YAML metadata writer class.
    
    This class implements a YAML metadata writer as a context manager. Metadata are written to
    the given path and file 
    """

    def __init__(self, file_path: str, file_name: str):
        """Initialise the Yaml metadata writer object.
        
        This method initialises the writer object, storing the file path and name.
        No file mode is provided, the class reads any existing file when you make it and overwrites
        if you call the write function while open.
        e.g.: with YamlMetadataWriter(args) as f: f.data will give you the file contents
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
        If there's metadatadata in an existing file by that name, it retains that information under
        'existing', effetively saving one prior version of data.
        """
        try:
            os.makedirs(self.file_path, exist_ok=True)
            
            # Look at existing file if it's there, if you want to append
            # If not appending, the file will be overwritten when you write
            if os.path.exists(self.full_path):
                with open(self.full_path, "r") as f:
                    existing_data = yaml.safe_load(f) or {}
                    if "metadata" in existing_data:
                        # Move data currently in there under a header
                        existing_data["previous"] = existing_data.pop("metadata")
                    self.data = existing_data
            else:
                self.data = {}

        except (OSError, IOError) as error:
            error_msg = f"Failed to creature YAML Metadata writer: {error}"
            logging.error(error_msg)
            raise LiveXError(error_msg)
        
        return self
        
    def __exit__(self, exc_type: Any, exc_value: Any, exc_tb: Any) -> None:
        """Exit the context manager.
        
        This method implements the context manager exit point. Any exceptions that occurred during
        writing are logged and raised.
        """
        if exc_value:
            error_msg = f"Error during YAML Metadata writing: {exc_type.__name__}: {exc_value}"
            logging.error(error_msg)
            raise LiveXError(error_msg)
        
        try:
            with open(self.full_path, "w") as f:
                yaml.safe_dump(self.data, f, sort_keys=False)

        except (OSError, IOError) as error:
            error_msg = f"Failed to write YAML Metadata: {error}"
            logging.error(error_msg)
            raise LiveXError(error_msg)

    def write(self, metadata: Dict) -> None:
        """Write metadata to the file.
        
        This method writes the metadata to the class data attribute to be written on context exit.
        :param metadata: dict of metadata fields to write into file
        """
        self.data["metadata"] = metadata
        logging.debug(f"Wrote metadata for group metadata to YAML file {self.full_path}")
