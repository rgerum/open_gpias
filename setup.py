#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(name='open_gpias',
      version="0.9.0",
      description='Open GPIAS to measure startle responses',
      url='https://bitbucket.org/randrian/asr_setup',
      license="GPLv3",
      author='Hinrich Rahlfs, Matthias Streb, Achim Schilling, Richard Gerum',
      author_email='richard.gerum@fau.de',
      packages=['open_gpias'],
      entry_points={
              'console_scripts': ['open_gpias=open_gpias.mainWindow:main'],
              'gui_scripts': ['open_gpias_gui=open_gpias.mainWindow:main'],
          },
      #setup_requires=['numpy'],
      install_requires=['sounddevice',
                        'scipy',
                        'matplotlib',
                        'qtpy',
                        'PyDAQmx',
                        'pandas'],
      include_package_data=True)
