from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='tftapp',
      version=version,
      description="Framework providing an easy way to create simlpe applications for raspberry pi running on a small tft display.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Daniel Havlik',
      author_email='nielow@gmail.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
