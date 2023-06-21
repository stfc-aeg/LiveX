"""Setup script for odin_workshop python package."""

import sys
from setuptools import setup, find_packages
import versioneer

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='LiveX',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='LiveX',
      url='https://github.com/stfc-aeg/LiveX',
      author='Mika Shearwood',
      author_email='mika.shearwood@stfc.ac.uk',
      packages=find_packages(),
      install_requires=required,
      zip_safe=False,
)
