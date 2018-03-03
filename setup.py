#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(name='asr_setup',
      version="0.9.0",
      description='ASR-Setup to measure startle responses',
      url='https://bitbucket.org/randrian/asr_setup',
      license="GPLv3",
      author='Hinrich Rahlfs, Matthias Streb, Achim Schilling, Richard Gerum',
      author_email='richard.gerum@fau.de',
      packages=['asr_setup'],
      entry_points={
              'console_scripts': ['asr_setup=asr_setup.StimulusFrontEnd:main'],
              'gui_scripts': ['asr_setup_gui=asr_setup.StimulusFrontEnd:main'],
          },
      #setup_requires=['numpy'],
      install_requires=['sounddevice',
                        'scipy',
                        'matplotlib',
                        'qtpy',
                        'PyDAQmx',
                        'pandas'],
      include_package_data=True)
