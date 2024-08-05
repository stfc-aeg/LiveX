import logging
import os
from typing import Dict

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from livex.util import LiveXError


class MarkdownMetaWriter:

    def __init__(
        self, template_file: str, file_path: str, file_name: str, mode: str = "w"
    ):

        self.file_path = file_path
        self.file_name = file_name
        self.mode = mode

        self.full_path = os.path.join(file_path, file_name)

        self.template_dir = os.path.dirname(template_file)
        self.template_file = os.path.basename(template_file)

    def __enter__(self):

        try:
            os.makedirs(self.file_path, exist_ok=True)
            self.file = open(self.full_path, self.mode)
        except (OSError, IOError) as error:
            raise LiveXError("Failed to write markdown metadata: {}".format(str(error)))

        try:
            self.env = Environment(loader=FileSystemLoader(self.template_dir))
            self.template = self.env.get_template(self.template_file)
        except TemplateNotFound as error:
            raise LiveXError("Markdown template {} not found".format(str(error)))

        return self

    def __exit__(self, exc_type, exc_value, exc_tb):

        if self.file:
            self.file.close()

    def write(self, metadata: Dict):

        content = self.template.render(metadata)
        self.file.write(content)

        logging.debug("Wrote metadata to markdown file %s", self.full_path)
