"""Class to handle the metadata page. The specifics aren't yet known but a basic implementation
will make future development with more explicit requirements much faster."""

from odin.adapters.parameter_tree import ParameterTree
from datetime import datetime

class Metadata():

    def __init__(self):
        
        # Establish defaults for common settings
        # Leave oft-changed settings blank?

        now = datetime.now()

        # Define some meta settings
        self.comment = None
        self.sample = None
        self.date = now.date().isoformat()
        self.time = now.time().strftime('%H:%M:%S')

        # Some other dummy values
        self.spinner = 0
        self.freetext = None

        # Values to be read from dropdown lists
        # Would e.g.: samples be determined from a file?
        self.dropdowns = {
            'samples': ['sample_a', 'sample_b', 'sample_c'],
            'samples_index': 0
        }

        self.tree = ParameterTree({
            'comment': (lambda: self.comment, self.update_comment),
            'sample': (lambda: self.sample, self.set_sample),
            'date': (lambda: self.date, None),
            'time': (lambda: self.time, None),
            'spinner': (lambda: self.spinner, self.set_spinner),
            'freetext': (lambda: self.freetext, self.set_freetext),
            'dropdowns': (lambda: self.dropdowns, None)
        })


    def update_comment(self, value):
        self.comment = value

    def set_sample(self, value):
        self.sample = value

    def set_spinner(self, value):
        self.spinner = value

    def set_freetext(self, value):
        self.freetext = value
