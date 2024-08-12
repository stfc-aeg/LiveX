"""
It needs functions to:
- Check if file exists, if not create it with <name>
- Receive data structure
- Write data into file with given structure

Temp logs, camera data, metadata (config) are the obvious structures. User notes could also be handled by this, creating a markdown or text file.

Camera data will eventually need more consideration
"""
import h5py
import os
import numpy as np
import logging

class FileWriter():
    """Class to handle the writing of hdf5 files."""

    def __init__(self, filepath, filename, dtypes=None):
        """Initialise the Filewriter with a path and name, then open the file.
        :param filepath: path to file
        :param filename: name of file
        :param dtypes: optional dict detailing not-float object type of specific datasets
        """
        if not filename.endswith('.hdf5'):
            filename += '.hdf5'

        self.filepath = filepath
        self.filename = filename
        self.set_fullpath()
        os.makedirs(filepath, exist_ok=True)

        self.dtypes = dtypes
        self.file = None

    def set_fullpath(self):
        """Set the full path of the filewriter."""
        self.full_path = os.path.join(self.filepath, self.filename)

    def open_file(self, mode="a"):
        """Open the file in specified mode.
        :param mode: mode to open file in. default a (append)
        """
        self.file = h5py.File(self.full_path, mode)

    def close_file(self):
        """Close the file."""
        self.file.close()

    def write_hdf5(self, data, groupname):
        """Create or access a specified file, create a group in it and add data to that group.
        :param filepath: path to file/file directory
        :param filename: name of file
        :param data: dict of data, with each dataset as key and its data as value
        :param groupname: name of group for file
        """
        if not self.file:
            self.open_file()
        # Add group to file
        group = self.file.require_group(groupname)

        for key, values in data.items():

            # Create array with dtype. If no dtypes specified, defaults to float in all cases
            dtype = self.dtypes.get(key, 'f') if self.dtypes else 'f'
            new_data = np.array(values, dtype=dtype)

            if key in group:
                dset = group[key]
                size_orig = dset.shape[0]
                size_new = size_orig + len(values)
                dset.resize(size_new, axis=0)
                dset[size_orig:size_new] = new_data

            else:
                maxshape = (None,) + new_data.shape[1:]
                group.create_dataset(key, data=new_data, maxshape=maxshape, dtype=new_data.dtype)

        logging.debug("file written")

    def create_notes_file(filepath, filename, filetype='md'):
        """Create a notes file in the specified location, with specified name and filetype.
        :param filepath (str): folder location from control/
        :param filename (str): name of file
        :param filetype: type of file. 'txt' or 'md'
        """
        logging.debug("filetype: %s", filetype)
        # force filetype by passed argument for config mismatches
        if filetype not in ['md', 'txt']:
            logging.debug("Filetype should be 'md' or 'txt'.")
            return

        name, ext = filename.split(".")
        logging.debug("name: %s", name)
        logging.debug("ext: %s", ext)
        if ext in ['md', 'txt']:
            filename = name  # remove existing extension
        logging.debug("filename: %s", filename)
        filename += '.' + filetype
        logging.debug("filename: %s", filename)

        full_path = os.path.join(
            filepath, filename
        )
        os.makedirs(filepath, exist_ok=True),

        try:
            with open(full_path, 'x') as file:
                logging.debug("Notes file created as %s", filetype)
        except:
            logging.debug("Notes file already exists")
