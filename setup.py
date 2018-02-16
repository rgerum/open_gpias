#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(name='asr_setup',
      version="0.9.0",
      description='ASR-Setup to measure startle responses',
      url='https://bitbucket.org/randrian/asr_setup',
      license="GPLv3",
      author='Richard Gerum, Sebastian Richter',
      author_email='richard.gerum@fau.de',
      packages=['asr_setup'],
      entry_points={
              'console_scripts': ['clickpoints=clickpoints.launch:main'],
              'gui_scripts': ['clickpoints_gui=clickpoints.launch:main'],
          },
      #setup_requires=['numpy'],
      install_requires=['sounddevice',
                        'scipy',
                        'matplotlib',
                        'qtpy',
                        'PyDAQmx'],
      include_package_data=True)
