"""HDF5 metadata writer.

This module implements a HDF5 metadata writer class, which injects metadata fields into an HDF5
file as attributes of a specified group. The class implements the context manager pattern for ease
of use.

Tim Nicholls, STFC Detector Systems Software Group
"""

import logging
import os
from typing import Any, Dict

import h5py
from livex.util import LiveXError


class HdfMetadataWriter:
    """HDF5 metadata writer class.

    This class implements an HDF5 metadata writer as a context manager. Metadata are written to the
    specified path and file, injected as attributes of the specified HDF5 group.
    """

    def __init__(self, file_path: str, file_name: str, file_mode: str = "a"):
        """Intialise the HDF5 metadata writer object.

        This method initialises the writer object, storing the specified file path, name and mode.

        :param file_path : path of the HDF5 file
        :param file_name : name of the HDF5 file
        :param file_mode : mode to open the HDF5 file with (e.g. "a" - append)
        """

        # Store the path, name and mode in the object
        self.file_path = file_path
        self.file_name = file_name
        self.file_mode = file_mode

        # Construct the full file path
        self.full_path = os.path.join(file_path, file_name)

    def __enter__(self):
        """Enter the context manager.

        This method implements the context manager entry point. The path to the specified file is
        created if absent, then the HDF5 file opened. Exceptions are logged and raised as a
        LiveX error.
        """
        try:
            # Ensure the path to the HDF5 file exists
            os.makedirs(self.file_path, exist_ok=True)

            # Open the HDF5 file
            self.file = h5py.File(self.full_path, self.file_mode)

        except (OSError, IOError) as error:
            error_msg = "Failed to create HDF metadata writer: {}".format(str(error))
            logging.error(error_msg)
            raise LiveXError(error_msg)

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, exc_tb: Any) -> None:
        """Exit the context manager.

        This method implements the context manager exit point. The file is closed if open and any
        exceptions that occurred curing writing logged and raised appropriately.
        """
        if self.file:
            self.file.close()

        if exc_value:
            error_msg = "Error during HDF metadata writing: {}: {}".format(
                exc_type.__name__, exc_value
            )
            logging.error(error_msg)
            raise LiveXError(error_msg)

    def write(self, group_name: str, metadata: Dict) -> None:
        """Write metadata to the file.

        This method writes the specified metadata to the file, injecting it as attributes of the
        specified HDF5 group, which is first created if necessary.

        :param group_name: name of group to inject metadata into
        :param metadata: dictionary of metadata fields to write into file
        """

        # Create the metadata group if necessary
        group = self.file.require_group(group_name)

        # Inject the metadata fields as attributes of the group
        for key, value in metadata.items():
            group.attrs[key] = value

        logging.debug("Wrote metadata to group %s in HDF file %s", group.name, self.full_path)
